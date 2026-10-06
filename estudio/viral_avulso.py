"""Render avulso para referências virais.

Lê um JSON independente da fila diária e gera MP4 + descrição.
Não toca em conteudo/fila.json, não aprova e não publica.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from estudio import render, roteiro, voz
from src import config, validar_video


def produzir(item_path: Path, voz_escolhida: str = voz.VOZ_PADRAO) -> dict:
    item = json.loads(item_path.read_text(encoding="utf-8"))
    ident = str(item["id"])
    trabalho = config.SAIDA / f"viral_{ident}"
    trabalho.mkdir(parents=True, exist_ok=True)

    segmentos = roteiro.montar(item)
    wav = trabalho / "narracao.wav"
    dados_voz = voz.gerar(segmentos, wav, voz=voz_escolhida, mudo=False)

    pasta = config.RAIZ / "viral_prontos"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{ident}.mp4"
    render.renderizar(item, wav, dados_voz, destino)
    tecnico = validar_video.validar(destino)

    descricao = str(item.get("descricao_post") or item.get("cta") or "").strip()
    (pasta / f"{ident}.txt").write_text(descricao + "\n", encoding="utf-8")
    (pasta / f"{ident}.json").write_text(json.dumps({
        "id": ident,
        "origem": "referencia-viral",
        "publicar_automaticamente": False,
        "arquivo": destino.name,
        "voz": dados_voz["voz"],
        **tecnico,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "arquivo": str(destino), "publicado": False}, ensure_ascii=False))
    return {"arquivo": destino, **tecnico}


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("item")
    p.add_argument("--voz", default=voz.VOZ_PADRAO)
    a=p.parse_args()
    produzir(Path(a.item), voz_escolhida=a.voz)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
