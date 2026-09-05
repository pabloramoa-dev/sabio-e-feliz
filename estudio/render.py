"""Render do Reel: 1080x1920, 30 fps, H.264 Main/Level 4.0 com faststart.

Nada de 60 fps aqui: 1080x1920@60 estoura o Level 4.0 e o player trava —
lição já paga em outro canal do Pablo.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from estudio import texto as txt
from estudio import voz as vozmod
from estudio.cenario import desenhar as desenhar_cenario
from estudio.paleta import A, L
from estudio.sabio import desenhar as desenhar_sabio

FPS = 30
FADE_CARTELA_ATE = 2.4     # cartela some depois de ~2,4s
CARTELA_CHEIA_ATE = 1.6


def _segmento_em(mapa: list[dict], t: float) -> dict:
    for seg in mapa:
        if seg["inicio"] <= t <= seg["fim"]:
            return seg
    return mapa[-1] if mapa else {"expressao": "acolhimento", "gesto": "livro", "papel": "fim"}


def _bloco_em(blocos: list[dict], t: float) -> dict | None:
    for b in blocos:
        if b["inicio"] - 0.12 <= t <= b["fim"] + 0.25:
            return b
    return None


def renderizar(item: dict, wav: Path, dados_voz: dict, saida: Path) -> Path:
    saida.parent.mkdir(parents=True, exist_ok=True)
    duracao = dados_voz["duracao_s"]
    palavras = dados_voz["palavras"]
    total_quadros = max(1, int(math.ceil(duracao * FPS)))

    amplitude = vozmod.amplitude_por_quadro(wav, FPS)
    mapa = [dict(s) for s in dados_voz["segmentos"]]
    if mapa:
        mapa[-1]["fim"] += 1.2   # segura o encerramento até o fim do áudio

    base = desenhar_cenario(0)
    blocos = txt.blocos_legenda(base, palavras)

    proc = subprocess.Popen(
        ["ffmpeg", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{L}x{A}", "-r", str(FPS), "-i", "-",
         "-i", str(wav),
         "-c:v", "libx264", "-profile:v", "main", "-level", "4.0", "-preset", "medium",
         "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
         "-movflags", "+faststart", "-shortest", str(saida)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )

    for q in range(total_quadros):
        t = q / FPS
        seg = _segmento_em(mapa, t)

        amp = amplitude[q] if q < len(amplitude) else 0.0
        boca = amp if seg["papel"] != "fim" else 0.0

        # piscada em intervalo irregular — olho parado lê como boneco
        fase = (t * 1000) % (3100 + 900 * math.sin(t / 2.7))
        piscada = 1.0 if fase < 110 else 0.0

        respiracao = math.sin(t * 1.7)
        olhar = (0.35 * math.sin(t / 3.1), 0.25 * math.sin(t / 4.3))

        quadro = desenhar_cenario(q)
        desenhar_sabio(quadro, boca=boca, piscada=piscada, expressao=seg["expressao"],
                       gesto=seg["gesto"], respiracao=respiracao, olhar=olhar)

        if t < FADE_CARTELA_ATE:
            alpha = 1.0 if t < CARTELA_CHEIA_ATE else 1 - (t - CARTELA_CHEIA_ATE) / (FADE_CARTELA_ATE - CARTELA_CHEIA_ATE)
            txt.desenhar_cartela(quadro, item["titulo"], alpha)
        elif seg["papel"] == "passagem":
            txt.desenhar_selo(quadro, item["referencia_exibida"], 1.0)

        bloco = _bloco_em(blocos, t)
        if bloco and t >= FADE_CARTELA_ATE - 0.6:
            txt.desenhar_legenda(quadro, bloco, t)

        txt.desenhar_assinatura(quadro)

        proc.stdin.write(quadro.tobytes())

    proc.stdin.close()
    erro = proc.stderr.read().decode("utf-8", "ignore")
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg falhou:\n{erro[-2000:]}")
    return saida
