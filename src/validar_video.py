"""Validação técnica do MP4 antes de qualquer chamada à Meta."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src import config


def sondar(video: Path) -> dict:
    saida = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)],
        text=True,
    )
    return json.loads(saida)


def validar(video: Path) -> dict:
    """Levanta ValueError se o arquivo não puder ir ao ar. Devolve um resumo."""
    if not video.exists():
        raise ValueError(f"arquivo inexistente: {video}")

    dados = sondar(video)
    streams = dados["streams"]

    v = next((s for s in streams if s["codec_type"] == "video"), None)
    a = next((s for s in streams if s["codec_type"] == "audio"), None)

    if v is None:
        raise ValueError("o arquivo não tem faixa de vídeo")
    if a is None:
        raise ValueError("o arquivo não tem faixa de áudio")

    largura, altura = int(v["width"]), int(v["height"])
    if (largura, altura) != (config.LARGURA, config.ALTURA):
        raise ValueError(f"dimensões {largura}x{altura}; esperado {config.LARGURA}x{config.ALTURA}")

    if v["codec_name"] != "h264":
        raise ValueError(f"codec de vídeo {v['codec_name']}; o Instagram espera h264")
    if a["codec_name"] != "aac":
        raise ValueError(f"codec de áudio {a['codec_name']}; o Instagram espera aac")

    duracao = float(dados["format"]["duration"])
    if not config.DURACAO_MIN_S <= duracao <= config.DURACAO_MAX_S:
        raise ValueError(f"duração de {duracao:.1f}s fora da faixa permitida")

    tamanho_mb = video.stat().st_size / (1024 * 1024)
    if tamanho_mb > 90:
        raise ValueError(f"arquivo com {tamanho_mb:.1f} MB; grande demais para servir por raw URL")

    return {
        "duracao_s": round(duracao, 2),
        "resolucao": f"{largura}x{altura}",
        "fps": v.get("r_frame_rate"),
        "tamanho_mb": round(tamanho_mb, 2),
        "codec_video": v["codec_name"],
        "codec_audio": a["codec_name"],
    }
