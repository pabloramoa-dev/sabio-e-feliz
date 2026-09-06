"""Conferência das duas filas — usada pelo validar.yml e pelo vigia-fila.yml.

O canal publica duas vezes por dia: Reel de manhã e carrossel à tarde. Cada um
tem a sua fila e a sua reserva; aqui elas são conferidas juntas para que um
único relatório diga se falta material em algum dos dois.

    python -m src.conferir            # relatório legível, falha se houver problema
    python -m src.conferir --resumo   # linhas chave=valor para o GitHub Actions
"""
from __future__ import annotations

import json
import sys

from src import carrossel_fila, config, fila


def main() -> int:
    reels = fila.lint()
    carros = carrossel_fila.conferir()

    if "--resumo" in sys.argv:
        baixa = (not reels["reserva_ok"]) or (not carros["reserva_ok"])
        print(f"aprovados={reels['aprovados']}")
        print(f"total={reels['total']}")
        print(f"carrosseis_disponiveis={carros['disponiveis']}")
        print(f"reserva_baixa={'true' if baixa else 'false'}")
        return 0

    print(json.dumps({"reels": reels, "carrosseis": carros}, ensure_ascii=False, indent=1))

    if reels["problemas"] or carros["problemas"]:
        print("\n✗ Há problemas nas filas. Nada será publicado até que sejam resolvidos.")
        return 1
    if not reels["reserva_ok"]:
        print(f"\n⚠ Reserva de Reels baixa: {reels['aprovados']} aprovados "
              f"(mínimo {config.RESERVA_MINIMA}).")
    if not carros["reserva_ok"]:
        print(f"\n⚠ Reserva de carrosséis baixa: {carros['disponiveis']} disponíveis "
              f"(mínimo {config.RESERVA_MINIMA}).")
    print("\n✓ Filas íntegras.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
