"""Narração do Sábio.

Motor padrão: edge-tts (gratuito, sem chave, vozes neurais PT-BR).
Vantagem decisiva: devolve WordBoundary, ou seja, o tempo exato de cada
palavra — é isso que faz a legenda karaokê bater com a fala em vez de ser
estimada por contagem de caracteres.

Vozes PT-BR recomendadas para o Sábio:
    pt-BR-AntonioNeural  (masculina, madura, calma)  <- padrão
    pt-BR-FabioNeural    (masculina, mais clara)
    pt-BR-ThalitaNeural  (feminina)

Modo mudo (--mudo): gera silêncio com tempos estimados. Serve só para
validar o render sem rede; nunca deve ir ao ar.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

VOZ_PADRAO = "pt-BR-AntonioNeural"
RITMO = "-8%"     # 125-145 palavras por minuto, sem aceleração artificial
TOM = "-2Hz"
PRE_ROLL = 0.6    # respiro no começo, dos dois lados (áudio e vídeo)
CAUDA = 1.4       # silêncio no fim para o encerramento não ser cortado


@dataclass
class Palavra:
    texto: str
    inicio: float
    fim: float


async def _sintetizar(texto: str, saida_mp3: Path, voz: str) -> list[Palavra]:
    import edge_tts

    com = edge_tts.Communicate(texto, voz, rate=RITMO, pitch=TOM)
    palavras: list[Palavra] = []
    with saida_mp3.open("wb") as fh:
        async for pedaco in com.stream():
            if pedaco["type"] == "audio":
                fh.write(pedaco["data"])
            elif pedaco["type"] == "WordBoundary":
                ini = pedaco["offset"] / 1e7
                dur = pedaco["duration"] / 1e7
                palavras.append(Palavra(pedaco["text"], ini + PRE_ROLL, ini + dur + PRE_ROLL))
    return palavras


def _estimar(texto: str) -> list[Palavra]:
    """Tempos estimados para o modo mudo: 2,4 caracteres por 100 ms."""
    palavras: list[Palavra] = []
    t = PRE_ROLL
    for p in texto.split():
        dur = max(0.22, len(p) / 13.5)
        palavras.append(Palavra(p, t, t + dur))
        t += dur + 0.06
    return palavras


def gerar(texto: str, destino_wav: Path, voz: str = VOZ_PADRAO, mudo: bool = False) -> dict:
    """Gera o WAV final (com pré-roll e cauda) e o mapa de palavras."""
    destino_wav.parent.mkdir(parents=True, exist_ok=True)
    bruto = destino_wav.with_suffix(".bruto.mp3")

    if mudo:
        palavras = _estimar(texto)
        dur_fala = palavras[-1].fim - PRE_ROLL if palavras else 1.0
        total = PRE_ROLL + dur_fala + CAUDA
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={total:.2f}",
             "-c:a", "pcm_s16le", str(destino_wav)],
            check=True, capture_output=True,
        )
    else:
        palavras = asyncio.run(_sintetizar(texto, bruto, voz))
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(bruto),
             "-af", f"adelay={int(PRE_ROLL*1000)}|{int(PRE_ROLL*1000)},apad=pad_dur={CAUDA},"
                    "loudnorm=I=-16.5:TP=-1.5:LRA=11:print_format=summary,alimiter=limit=0.95",
             "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(destino_wav)],
            check=True, capture_output=True,
        )
        bruto.unlink(missing_ok=True)

    dados = {
        "voz": "mudo" if mudo else voz,
        "duracao_s": duracao(destino_wav),
        "palavras": [asdict(p) for p in palavras],
    }
    destino_wav.with_suffix(".palavras.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return dados


def duracao(arquivo: Path) -> float:
    saida = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
         "default=nw=1:nk=1", str(arquivo)], text=True,
    )
    return float(saida.strip())


def amplitude_por_quadro(wav: Path, fps: int) -> list[float]:
    """Envelope de amplitude normalizado — é o que abre e fecha a boca."""
    import numpy as np

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
    # suaviza para a boca não tremer
    suave = np.convolve(env, np.ones(3) / 3, mode="same")
    return [float(x) for x in suave]
