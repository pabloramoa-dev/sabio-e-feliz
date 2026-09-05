"""Narração do Sábio — voz neural local com Kokoro.

Por que Kokoro e não um serviço na nuvem: o edge-tts é bloqueado quando a
chamada sai de um datacenter (o runner do GitHub leva 403 da Microsoft).
O Kokoro roda dentro do próprio runner, sem chave, sem cota e sem depender
de ninguém estar no ar. É a mesma voz que já roda nos outros canais.

Vozes PT-BR disponíveis:
    pm_alex   masculina, madura e calma   <- padrão do Sábio
    pm_santa  masculina, mais grave
    pf_dora   feminina

Sincronia da legenda: o Kokoro não devolve o tempo de cada palavra, então a
narração é sintetizada FRASE A FRASE. Assim o início e o fim de cada frase
são medidos de verdade, e dentro da frase as palavras são distribuídas pelo
tamanho. A legenda karaokê acerta porque a âncora é medida, não estimada.

Modo mudo (--mudo): silêncio com tempos estimados. Só para conferir o visual
sem baixar modelo; nunca vai ao ar.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

VOZ_PADRAO = "pf_dora"   # a mesma voz da Dona Maria no canal do tempo
VELOCIDADE = 0.92          # 125-145 palavras por minuto, sem pressa
PRE_ROLL = 0.6             # respiro no começo
CAUDA = 1.4                # silêncio no fim: o encerramento não pode ser cortado
PAUSA_FRASE = 0.20         # respiro entre frases da mesma ideia
PAUSA_SEGMENTO = 0.42      # pausa maior entre gancho, passagem, reflexão...
LUFS_ALVO = -16.5

RAIZ_MODELOS = Path(os.getenv("KOKORO_DIR", Path(__file__).resolve().parent.parent / "modelos"))
URL_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
ARQUIVOS = {"kokoro-v1.0.onnx": f"{URL_BASE}/kokoro-v1.0.onnx",
            "voices-v1.0.bin": f"{URL_BASE}/voices-v1.0.bin"}

MAX_PALAVRAS_FRASE = 12


@dataclass
class Palavra:
    texto: str
    inicio: float
    fim: float


def garantir_modelo() -> tuple[Path, Path]:
    RAIZ_MODELOS.mkdir(parents=True, exist_ok=True)
    for nome, url in ARQUIVOS.items():
        destino = RAIZ_MODELOS / nome
        if not destino.exists() or destino.stat().st_size < 1_000_000:
            print(f"  baixando {nome}...")
            urllib.request.urlretrieve(url, destino)
    return RAIZ_MODELOS / "kokoro-v1.0.onnx", RAIZ_MODELOS / "voices-v1.0.bin"


def frases(texto: str) -> list[str]:
    """Quebra em frases faláveis: pontuação forte primeiro, vírgula depois."""
    brutas = [p.strip() for p in re.split(r"(?<=[.!?:;])\s+", texto) if p.strip()]
    saida: list[str] = []
    for frase in brutas:
        if len(frase.split()) <= MAX_PALAVRAS_FRASE:
            saida.append(frase)
            continue
        pedaco: list[str] = []
        for parte in re.split(r"(?<=,)\s+", frase):
            if pedaco and len(" ".join(pedaco + [parte]).split()) > MAX_PALAVRAS_FRASE:
                saida.append(" ".join(pedaco))
                pedaco = [parte]
            else:
                pedaco.append(parte)
        if pedaco:
            saida.append(" ".join(pedaco))
    return saida


def _tempos_das_palavras(frase: str, inicio: float, fim: float) -> list[Palavra]:
    """Dentro da frase, cada palavra recebe fatia proporcional ao tamanho."""
    palavras = frase.split()
    pesos = [len(p) + 1 for p in palavras]
    total = sum(pesos) or 1
    duracao = max(fim - inicio, 0.05)
    saida, t = [], inicio
    for palavra, peso in zip(palavras, pesos):
        d = duracao * peso / total
        saida.append(Palavra(palavra, t, t + d))
        t += d
    return saida


def gerar(segmentos: list[dict], destino_wav: Path, voz: str = VOZ_PADRAO,
          mudo: bool = False) -> dict:
    """Sintetiza a narração inteira e devolve o mapa de tempos."""
    destino_wav.parent.mkdir(parents=True, exist_ok=True)
    taxa = 24000

    trilha: list[np.ndarray] = []
    palavras: list[Palavra] = []
    mapa_frases: list[dict] = []
    mapa_segmentos: list[dict] = []
    t = PRE_ROLL
    trilha.append(np.zeros(int(PRE_ROLL * taxa), dtype=np.float32))

    kokoro = None
    if not mudo:
        modelo, vozes = garantir_modelo()
        from kokoro_onnx import Kokoro
        kokoro = Kokoro(str(modelo), str(vozes))

    for n, seg in enumerate(segmentos):
        inicio_seg = t
        for i, frase in enumerate(frases(seg["texto"])):
            if mudo:
                dur = max(0.6, len(frase) / 15.0)
                audio = np.zeros(int(dur * taxa), dtype=np.float32)
            else:
                audio, taxa_k = kokoro.create(frase, voice=voz, speed=VELOCIDADE, lang="pt-br")
                audio = np.asarray(audio, dtype=np.float32)
                taxa = taxa_k
                dur = len(audio) / taxa
            trilha.append(audio)
            palavras.extend(_tempos_das_palavras(frase, t, t + dur))
            mapa_frases.append({"texto": frase, "inicio": round(t, 3),
                                "fim": round(t + dur, 3), "papel": seg["papel"]})
            t += dur
            pausa = PAUSA_FRASE
            trilha.append(np.zeros(int(pausa * taxa), dtype=np.float32))
            t += pausa

        extra = PAUSA_SEGMENTO - PAUSA_FRASE
        if n < len(segmentos) - 1 and extra > 0:
            trilha.append(np.zeros(int(extra * taxa), dtype=np.float32))
            t += extra

        mapa_segmentos.append({
            "papel": seg["papel"], "expressao": seg["expressao"],
            "gesto": seg["gesto"], "inicio": round(inicio_seg, 3), "fim": round(t, 3),
        })

    trilha.append(np.zeros(int(CAUDA * taxa), dtype=np.float32))
    sinal = np.concatenate(trilha)

    bruto = destino_wav.with_suffix(".bruto.wav")
    _escrever_wav(bruto, sinal, taxa)
    _masterizar(bruto, destino_wav)
    bruto.unlink(missing_ok=True)

    dados = {
        "voz": "mudo" if mudo else voz,
        "duracao_s": duracao(destino_wav),
        "palavras": [asdict(p) for p in palavras],
        "frases": mapa_frases,
        "segmentos": mapa_segmentos,
    }
    destino_wav.with_suffix(".tempos.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return dados


def _escrever_wav(caminho: Path, sinal: np.ndarray, taxa: int) -> None:
    import wave

    pico = float(np.max(np.abs(sinal))) or 1.0
    dados = (np.clip(sinal / max(pico, 1e-6) * 0.89, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes(dados.tobytes())


def _masterizar(entrada: Path, saida: Path) -> None:
    """Mede o volume, aplica ganho FIXO e limitador.

    Nada de loudnorm de passe único no caminho do sinal: em passe único ele
    trabalha em modo dinâmico e a narração sai estalando.
    """
    medida = subprocess.run(
        ["ffmpeg", "-i", str(entrada), "-af", "loudnorm=I=-16.5:TP=-1.5:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    ganho_db = 0.0
    try:
        bloco = medida[medida.rindex("{"):medida.rindex("}") + 1]
        entrada_i = float(json.loads(bloco)["input_i"])
        if entrada_i > -70:
            ganho_db = LUFS_ALVO - entrada_i
    except Exception:
        ganho_db = 0.0

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(entrada),
         "-af", f"volume={ganho_db:.2f}dB,alimiter=limit=0.95",
         "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(saida)],
        check=True, capture_output=True,
    )


def duracao(arquivo: Path) -> float:
    saida = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
         "default=nw=1:nk=1", str(arquivo)], text=True,
    )
    return float(saida.strip())


def amplitude_por_quadro(wav: Path, fps: int) -> list[float]:
    """Envelope de amplitude — é o que abre e fecha a boca do personagem."""
    bruto = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", str(wav), "-f", "s16le", "-ac", "1",
         "-ar", "16000", "-"], stderr=subprocess.DEVNULL,
    )
    amostras = np.frombuffer(bruto, dtype=np.int16).astype(np.float32) / 32768.0
    por_quadro = int(16000 / fps)
    n = len(amostras) // por_quadro
    if n == 0:
        return [0.0]
    blocos = amostras[: n * por_quadro].reshape(n, por_quadro)
    rms = np.sqrt((blocos ** 2).mean(axis=1))
    pico = float(rms.max()) or 1.0
    env = np.clip(rms / pico * 1.35, 0, 1)
    return [float(x) for x in np.convolve(env, np.ones(3) / 3, mode="same")]
