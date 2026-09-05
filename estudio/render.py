"""Render do Reel em Manim + junção com a narração.

Entrega 1080x1920 a 30 fps, H.264 Main/Level 4.0 com faststart.
Nada de 60 fps: 1080x1920@60 estoura o Level 4.0 e trava o player.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from estudio import voz as vozmod

FPS = 30
LARGURA, ALTURA = 1080, 1920


def _manim() -> str:
    exe = os.getenv("MANIM_BIN") or shutil.which("manim")
    if not exe:
        raise RuntimeError("manim não encontrado; instale com pip install manim")
    return exe


def renderizar(item: dict, wav: Path, dados_voz: dict, saida: Path) -> Path:
    saida.parent.mkdir(parents=True, exist_ok=True)
    raiz = Path(__file__).resolve().parent.parent
    trabalho = wav.parent

    job = {
        "id": item["id"],
        "titulo": item["titulo"],
        "referencia": item["referencia_exibida"],
        "duracao_s": dados_voz["duracao_s"],
        "fps": FPS,
        "frases": dados_voz["frases"],
        "segmentos": dados_voz["segmentos"],
        "envelope": vozmod.amplitude_por_quadro(wav, FPS),
    }
    caminho_job = trabalho / "cena.json"
    caminho_job.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")

    media = trabalho / "manim"
    ambiente = dict(os.environ)
    ambiente["SABIO_JOB"] = str(caminho_job)
    ambiente["PYTHONPATH"] = str(raiz) + os.pathsep + ambiente.get("PYTHONPATH", "")

    proc = subprocess.run(
        [_manim(), "render", "--format=mp4", "-r", f"{LARGURA},{ALTURA}",
         "--fps", str(FPS), "--media_dir", str(media), "-o", item["id"],
         "--disable_caching", "-v", "WARNING",
         str(raiz / "estudio" / "cena.py"), "Episodio"],
        cwd=str(raiz), env=ambiente, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"manim falhou:\n{proc.stdout[-1500:]}\n{proc.stderr[-3000:]}")

    mudos = list(media.rglob(f"{item['id']}.mp4"))
    if not mudos:
        raise RuntimeError(f"manim não gerou o MP4 esperado em {media}")
    mudo = mudos[0]

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mudo), "-i", str(wav),
         "-c:v", "libx264", "-profile:v", "main", "-level", "4.0", "-preset", "medium",
         "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
         "-movflags", "+faststart", "-shortest", str(saida)],
        check=True, capture_output=True,
    )
    return saida
