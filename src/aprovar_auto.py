"""Aprovação automática — o canal roda sem portão humano.

Decisão do Pablo em 2026-09-06: nada de aprovar item a item. Este módulo
assume o lugar dessa assinatura, com uma diferença importante: ele não julga
o conteúdo, ele só confirma que o item passou em TODAS as checagens de máquina.

O que continua valendo, e não depende de ninguém:
  - lint editorial (campos, tamanho, promessas proibidas)
  - arquivo existe e o sha256 bate com o que foi renderizado
  - um post por dia, por tipo
  - o token tem que apontar para @sabioefeliz, senão aborta

O que deixa de existir: a espera por uma pessoa. Um item que passa no lint
vira 'aprovado' na mesma hora, com aprovado_por='automatico'.

    python -m src.aprovar_auto            # aprova as duas filas
    python -m src.aprovar_auto --reels    # só os Reels
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from src import carrossel_fila as cfila
from src import fila as rfila

ASSINATURA = "automatico"


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def aprovar_reels(raiz=None) -> dict:
    itens = rfila.carregar_fila()
    aprovados, recusados = [], {}
    for item in itens:
        if item.get("status") != "em_revisao":
            continue
        erros = rfila.validar_item(item, raiz)
        if erros:
            recusados[item["id"]] = erros
            continue
        item["status"] = "aprovado"
        item["aprovado_por"] = ASSINATURA
        item["aprovado_em"] = _agora()
        aprovados.append(item["id"])
    if aprovados:
        rfila.salvar_fila(itens)
    return {"aprovados": aprovados, "recusados": recusados}


def aprovar_carrosseis(raiz=None) -> dict:
    itens = cfila.carregar_fila()
    aprovados, recusados = [], {}
    for item in itens:
        if item.get("status") != "em_revisao":
            continue
        # o lint de imagem só roda em item aprovado; simulamos para não
        # aprovar um carrossel cujas imagens não existem ou não batem
        teste = dict(item, status="aprovado")
        erros = cfila.validar_item(teste, raiz)
        if erros:
            recusados[item["id"]] = erros
            continue
        item["status"] = "aprovado"
        item["aprovado_por"] = ASSINATURA
        item["aprovado_em"] = _agora()
        aprovados.append(item["id"])
    if aprovados:
        cfila.salvar_fila(itens)
    return {"aprovados": aprovados, "recusados": recusados}


def main() -> int:
    so_reels = "--reels" in sys.argv
    so_carros = "--carrosseis" in sys.argv
    saida = {}
    if not so_carros:
        saida["reels"] = aprovar_reels()
    if not so_reels:
        saida["carrosseis"] = aprovar_carrosseis()
    print(json.dumps(saida, ensure_ascii=False, indent=1))
    # recusa não derruba o workflow: o item fica em revisão e o resto segue
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
