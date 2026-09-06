"""Estúdio: transforma um item da fila em Reel pronto para aprovação.

    python -m estudio.produzir --id EP-001
    python -m estudio.produzir --id EP-001 --mudo      # sem rede, só o visual
    python -m estudio.produzir --pendentes             # tudo que ainda não tem MP4

O que este script NÃO faz: publicar. Publicar é trabalho do src/main.py,
com a chave PUBLICAR_ATIVO e a aprovação registrada.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from estudio import render, roteiro, voz
from src import config, fila, validar_video


def produzir(item: dict, mudo: bool = False, voz_escolhida: str = voz.VOZ_PADRAO) -> dict:
    segmentos = roteiro.montar(item)
    texto = roteiro.texto_falado(item)
    trabalho = config.SAIDA / item["id"]
    trabalho.mkdir(parents=True, exist_ok=True)

    wav = trabalho / "narracao.wav"
    dados_voz = voz.gerar(segmentos, wav, voz=voz_escolhida, mudo=mudo)

    destino = config.REELS / f"{item['id']}.mp4"
    destino.parent.mkdir(parents=True, exist_ok=True)
    render.renderizar(item, wav, dados_voz, destino)

    tecnico = validar_video.validar(destino)
    resultado = {
        "id": item["id"],
        "arquivo": f"reels/{destino.name}",
        "sha256": fila.sha256_arquivo(destino),
        "palavras": len(texto.split()),
        "voz": dados_voz["voz"],
        **tecnico,
    }

    lista = fila.carregar_fila()
    for i in lista:
        if i["id"] == item["id"]:
            mudou = i.get("sha256") != resultado["sha256"]
            i["arquivo"] = resultado["arquivo"]
            i["sha256"] = resultado["sha256"]
            i["duracao_s"] = tecnico["duracao_s"]
            # Produzir de novo INVALIDA a aprovação: o que foi aprovado era o
            # arquivo antigo. Sem isso, um render novo entraria no ar sem
            # ninguém ter visto — exatamente o que a trava do sha256 evita.
            if i.get("status") in {"rascunho", "em_revisao"} or (mudou and i.get("status") == "aprovado"):
                i["status"] = "em_revisao"
                i["aprovado_por"] = None
                i["aprovado_em"] = None
    fila.salvar_json(config.FILA_JSON, lista)

    (trabalho / "producao.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return resultado


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--id", action="append", default=[])
    p.add_argument("--pendentes", action="store_true")
    p.add_argument("--mudo", action="store_true", help="silêncio no lugar da voz (só teste de render)")
    p.add_argument("--voz", default=voz.VOZ_PADRAO)
    args = p.parse_args()

    lista = fila.carregar_fila()
    if args.pendentes:
        alvos = [i for i in lista if i.get("status") in {"rascunho", "em_revisao"} and not (config.RAIZ / str(i.get("arquivo", "x"))).exists()]
    else:
        alvos = [i for i in lista if i["id"] in args.id]

    if not alvos:
        print(json.dumps({"ok": False, "erro": "nenhum episódio selecionado"}, ensure_ascii=False))
        return 1

    saidas = []
    for item in alvos:
        print(f"→ produzindo {item['id']} · {item['titulo']}")
        saidas.append(produzir(item, mudo=args.mudo, voz_escolhida=args.voz))

    print(json.dumps({"ok": True, "produzidos": saidas}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
