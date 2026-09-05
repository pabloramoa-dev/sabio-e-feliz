"""Conferência da fila — usada pelo validar.yml e pelo vigia-fila.yml.

    python -m src.conferir            # relatório legível, falha se houver problema
    python -m src.conferir --resumo   # linhas chave=valor para o GitHub Actions
"""
from __future__ import annotations

import json
import sys

from src import config, fila


def main() -> int:
    rel = fila.lint()

    if "--resumo" in sys.argv:
        print(f"aprovados={rel['aprovados']}")
        print(f"total={rel['total']}")
        print(f"reserva_baixa={'false' if rel['reserva_ok'] else 'true'}")
        return 0

    print(json.dumps(rel, ensure_ascii=False, indent=1))
    if rel["problemas"]:
        print("\n✗ A fila tem problemas. Nada será publicado até que sejam resolvidos.")
        return 1
    if not rel["reserva_ok"]:
        print(f"\n⚠ Reserva baixa: {rel['aprovados']} aprovados (mínimo {config.RESERVA_MINIMA}).")
    print("\n✓ Fila íntegra.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
