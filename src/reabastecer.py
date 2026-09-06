"""Decide o que precisa ser feito para o canal nunca parar.

Roda antes da produção: olha quantos itens aprovados ainda existem em cada
fila e diz quantos faltam para chegar ao alvo. Quem gera é o estudio.reserva;
quem renderiza é o estúdio; quem aprova é o src.aprovar_auto. Aqui só se
calcula a conta.

    python -m src.reabastecer --alvo 14 --resumo
"""
from __future__ import annotations

import argparse
import json

from src import carrossel_fila as cfila
from src import fila as rfila

ALVO_PADRAO = 14      # duas semanas de folga em cada fila


def faltando(alvo: int = ALVO_PADRAO) -> dict:
    reels = rfila.carregar_fila()
    publicados_reels = {p["id"] for p in rfila.carregar_publicados()}
    prontos_reels = [
        i for i in reels
        if i.get("status") == "aprovado"
        and not i.get("publicado_em")
        and i["id"] not in publicados_reels
    ]
    # o que já está escrito mas ainda não virou vídeo também conta como reserva
    na_esteira_reels = [i for i in reels if i.get("status") in {"rascunho", "em_revisao"}]

    carros = cfila.carregar_fila()
    publicados_carros = cfila.ja_publicados()
    prontos_carros = [
        i for i in carros
        if i.get("status") == "aprovado"
        and not i.get("publicado_em")
        and i["id"] not in publicados_carros
    ]
    na_esteira_carros = [i for i in carros if i.get("status") in {"rascunho", "em_revisao"}]

    return {
        "alvo": alvo,
        "reels_prontos": len(prontos_reels),
        "reels_na_esteira": len(na_esteira_reels),
        "reels_a_gerar": max(0, alvo - len(prontos_reels) - len(na_esteira_reels)),
        "carrosseis_prontos": len(prontos_carros),
        "carrosseis_na_esteira": len(na_esteira_carros),
        "carrosseis_a_gerar": max(0, alvo - len(prontos_carros) - len(na_esteira_carros)),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--alvo", type=int, default=ALVO_PADRAO)
    p.add_argument("--resumo", action="store_true", help="saída chave=valor para o Actions")
    a = p.parse_args()

    conta = faltando(a.alvo)
    if a.resumo:
        for chave, valor in conta.items():
            print(f"{chave}={valor}")
    else:
        print(json.dumps(conta, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
