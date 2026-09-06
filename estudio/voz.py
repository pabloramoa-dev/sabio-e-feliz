"""Narração — voz neural local com Kokoro.

Por que Kokoro e não um serviço na nuvem: o edge-tts é bloqueado quando a
chamada sai de um datacenter (o runner do GitHub leva 403 da Microsoft).
O Kokoro roda dentro do próprio runner, sem chave, sem cota e sem depender
de ninguém estar no ar. É a mesma voz que já roda nos outros canais.

Vozes PT-BR:
    pf_dora   feminina  <- padrão (a mesma da Dona Maria no canal do tempo)
    pm_alex   masculina madura
    pm_santa  masculina mais grave

TRÊS DECISÕES QUE MUDAM MUITO A NATURALIDADE

1. A narração é sintetizada por BLOCO DE IDEIA, não frase por frase. Cada
   chamada ao Kokoro reinicia a entonação: picotar em pedacinhos faz a voz
   subir e descer do zero a cada respiro e é o que mais soa robótico.

2. Nenhum silêncio artificial é enfiado dentro do bloco. O próprio modelo
   já produz a pausa de vírgula e de ponto. Colar 0,2 s fixo entre frases
   soa metrônomo.

3. A referência bíblica é EXPANDIDA antes de falar: "Provérbios 15:1" vira
   "Provérbios, capítulo quinze, versículo um". Sem isso o fonetizador lê
   "quinze:um" grudado — vira "quinzum".

Os tempos da legenda continuam medidos, não estimados: dentro do bloco os
silêncios reais do áudio marcam onde cada frase começa.
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

# Uma voz pode ser um nome do modelo ou uma MISTURA: "pm_alex+im_nicola"
# combina os dois vetores meio a meio, e "pm_alex:0.7+im_nicola:0.3" define o
# peso. Misturar cria vozes que não existem soltas no modelo.
VOZ_PADRAO = "pm_alex+im_nicola"
VELOCIDADE = 0.94          # um respiro mais devagar que o natural do modelo
PRE_ROLL = 0.5             # respiro antes da primeira palavra
CAUDA = 1.3                # o encerramento não pode ser cortado
PAUSA_SEGMENTO = 0.28      # respiro entre gancho, passagem, reflexão...
LUFS_ALVO = -16.5

RAIZ_MODELOS = Path(os.getenv("KOKORO_DIR", Path(__file__).resolve().parent.parent / "modelos"))
URL_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
ARQUIVOS = {"kokoro-v1.0.onnx": f"{URL_BASE}/kokoro-v1.0.onnx",
            "voices-v1.0.bin": f"{URL_BASE}/voices-v1.0.bin"}

UNIDADES = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete",
            "oito", "nove", "dez", "onze", "doze", "treze", "catorze", "quinze",
            "dezesseis", "dezessete", "dezoito", "dezenove"]
DEZENAS = {20: "vinte", 30: "trinta", 40: "quarenta", 50: "cinquenta",
           60: "sessenta", 70: "setenta", 80: "oitenta", 90: "noventa"}


def estilo(kokoro, voz: str):
    """Devolve o vetor de estilo: nome simples ou mistura ponderada."""
    if "+" not in voz:
        return voz

    partes, pesos = [], []
    for termo in voz.split("+"):
        termo = termo.strip()
        if ":" in termo:
            nome, peso = termo.rsplit(":", 1)
            partes.append(nome.strip())
            pesos.append(float(peso))
        else:
            partes.append(termo)
            pesos.append(1.0)

    total = sum(pesos) or 1.0
    vetor = None
    for nome, peso in zip(partes, pesos):
        parcela = kokoro.get_voice_style(nome) * (peso / total)
        vetor = parcela if vetor is None else vetor + parcela
    return vetor


@dataclass
class Palavra:
    texto: str
    inicio: float
    fim: float


# =====================================================================
#  TEXTO FALADO
# =====================================================================
def por_extenso(n: int) -> str:
    if n < 20:
        return UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        base = DEZENAS[d * 10]
        return base if u == 0 else f"{base} e {UNIDADES[u]}"
    return str(n)


def expandir_referencia(texto: str) -> str:
    """Provérbios 15:1 -> Provérbios, capítulo quinze, versículo um."""
    def _um(m):
        cap, v1, v2 = int(m.group(1)), int(m.group(2)), m.group(3)
        if v2:
            return (f", capítulo {por_extenso(cap)}, "
                    f"versículos {por_extenso(v1)} a {por_extenso(int(v2))}")
        return f", capítulo {por_extenso(cap)}, versículo {por_extenso(v1)}"

    return re.sub(r"\s*(\d{1,2}):(\d{1,3})(?:\s*[-–a]\s*(\d{1,3}))?", _um, texto)


def frases(texto: str) -> list[str]:
    """Só para a LEGENDA: quebra em frases faláveis, sem cortar a síntese."""
    brutas = [p.strip() for p in re.split(r"(?<=[.!?:;])\s+", texto) if p.strip()]
    saida: list[str] = []
    for frase in brutas:
        if len(frase.split()) <= 12:
            saida.append(frase)
            continue
        pedaco: list[str] = []
        for parte in re.split(r"(?<=,)\s+", frase):
            if pedaco and len(" ".join(pedaco + [parte]).split()) > 12:
                saida.append(" ".join(pedaco))
                pedaco = [parte]
            else:
                pedaco.append(parte)
        if pedaco:
            saida.append(" ".join(pedaco))
    return saida


# =====================================================================
#  MODELO
# =====================================================================
def garantir_modelo() -> tuple[Path, Path]:
    RAIZ_MODELOS.mkdir(parents=True, exist_ok=True)
    for nome, url in ARQUIVOS.items():
        destino = RAIZ_MODELOS / nome
        if not destino.exists() or destino.stat().st_size < 1_000_000:
            print(f"  baixando {nome}...")
            urllib.request.urlretrieve(url, destino)
    return RAIZ_MODELOS / "kokoro-v1.0.onnx", RAIZ_MODELOS / "voices-v1.0.bin"


# =====================================================================
#  ALINHAMENTO PELOS SILÊNCIOS REAIS
# =====================================================================
def _silencios(audio: np.ndarray, taxa: int) -> list[tuple[float, float]]:
    """Todos os respiros do bloco: (centro em segundos, duração em segundos)."""
    salto = int(taxa * 0.01)
    janela = int(taxa * 0.02)
    n = max(1, (len(audio) - janela) // salto)
    rms = np.array([
        np.sqrt(np.mean(audio[i * salto: i * salto + janela] ** 2) + 1e-12)
        for i in range(n)
    ])
    limiar = max(rms.max() * 0.06, 1e-4)
    quieto = rms < limiar

    achados, i = [], 0
    while i < n:
        if quieto[i]:
            j = i
            while j < n and quieto[j]:
                j += 1
            dur = (j - i) * salto / taxa
            if dur >= 0.045 and i > 0 and j < n:
                achados.append(((i + j) / 2 * salto / taxa, dur))
            i = j
        else:
            i += 1
    return achados


def _fronteiras(audio: np.ndarray, taxa: int, pedacos: list[str], dur: float) -> list[float]:
    """Onde cada frase da legenda começa dentro do bloco.

    Primeiro estima pela quantidade de texto, depois puxa cada estimativa
    para o respiro real mais próximo. Pegar simplesmente os maiores
    silêncios erra feio: uma vírgula longa no meio rouba a fronteira de
    quem precisava dela.
    """
    if len(pedacos) < 2:
        return []

    pesos = np.array([len(p) for p in pedacos], dtype=float)
    esperado = list(np.cumsum(pesos / pesos.sum()) * dur)[:-1]

    respiros = _silencios(audio, taxa)
    if not respiros:
        return esperado

    saida, usados, anterior = [], set(), 0.0
    for alvo in esperado:
        tolerancia = max(0.45, dur * 0.10)
        candidatos = [
            (abs(c - alvo), c) for k, (c, _d) in enumerate(respiros)
            if k not in usados and c > anterior and abs(c - alvo) <= tolerancia
        ]
        if candidatos:
            _, escolhido = min(candidatos)
            usados.add(next(k for k, (c, _d) in enumerate(respiros) if c == escolhido))
        else:
            escolhido = alvo
        saida.append(escolhido)
        anterior = escolhido
    return saida


def _tempos_das_palavras(frase: str, inicio: float, fim: float) -> list[Palavra]:
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


# =====================================================================
#  GERAÇÃO
# =====================================================================
def gerar(segmentos: list[dict], destino_wav: Path, voz: str = VOZ_PADRAO,
          mudo: bool = False) -> dict:
    destino_wav.parent.mkdir(parents=True, exist_ok=True)
    taxa = 24000

    kokoro = None
    if not mudo:
        modelo, vozes = garantir_modelo()
        from kokoro_onnx import Kokoro
        kokoro = Kokoro(str(modelo), str(vozes))
        estilo_voz = estilo(kokoro, voz)

    trilha: list[np.ndarray] = [np.zeros(int(PRE_ROLL * taxa), dtype=np.float32)]
    palavras: list[Palavra] = []
    mapa_frases: list[dict] = []
    mapa_segmentos: list[dict] = []
    t = PRE_ROLL

    for n, seg in enumerate(segmentos):
        # o bloco inteiro vai de uma vez: a entonação atravessa as frases
        falado = expandir_referencia(seg["texto"])
        if mudo:
            dur = max(1.0, len(falado) / 15.0)
            audio = np.zeros(int(dur * taxa), dtype=np.float32)
        else:
            audio, taxa_k = kokoro.create(falado, voice=estilo_voz, speed=VELOCIDADE, lang="pt-br")
            audio = np.asarray(audio, dtype=np.float32)
            taxa = taxa_k
            dur = len(audio) / taxa

        # legenda: as frases do texto ESCRITO, ancoradas nos silêncios do áudio
        pedacos = frases(seg["texto"])
        if mudo:
            pesos = np.array([len(p) for p in pedacos], dtype=float)
            cortes = list(np.cumsum(pesos / pesos.sum()) * dur)[:-1]
        else:
            cortes = _fronteiras(audio, taxa, pedacos, dur)
        limites = [0.0] + list(cortes) + [dur]

        inicio_seg = t
        for k, frase in enumerate(pedacos):
            ini, fim = t + limites[k], t + limites[k + 1]
            palavras.extend(_tempos_das_palavras(frase, ini, fim))
            mapa_frases.append({"texto": frase, "inicio": round(ini, 3),
                                "fim": round(fim, 3), "papel": seg["papel"]})

        trilha.append(audio)
        t += dur
        if n < len(segmentos) - 1:
            trilha.append(np.zeros(int(PAUSA_SEGMENTO * taxa), dtype=np.float32))
            t += PAUSA_SEGMENTO

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
