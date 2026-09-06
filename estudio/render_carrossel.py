"""Produção dos carrosséis — roda no estúdio, nunca na hora de publicar.

Gera as sete imagens de cada item que ainda não tem arquivo, grava em
carrosseis/<ID>/ e devolve para a fila a lista de arquivos e o sha256 de cada
um. Se um item aprovado for renderizado de novo, a aprovação CAI: as imagens
mudaram, então quem aprovou não viu isto. Mesma trava dos Reels.

    python -m estudio.render_carrossel            # tudo que falta
    python -m estudio.render_carrossel CAR-003    # um só
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from estudio.carrossel import gravar
from src import config
from src.carrossel_fila import carregar_fila, salvar_fila, PASTA_IMAGENS
from src.fila import sha256_arquivo


def produzir(ids: list[str] | None = None, forcar: bool = False) -> list[str]:
    fila = carregar_fila()
    feitos: list[str] = []

    for item in fila:
        if ids and item["id"] not in ids:
            continue
        if item.get("status") in {"publicado", "arquivado"}:
            continue
        if item.get("arquivos") and not forcar and not ids:
            continue

        destino = PASTA_IMAGENS / item["id"]
        caminhos = gravar(item, str(destino))

        relativos = [str(c.relative_to(config.RAIZ)) if hasattr(c, "relative_to")
                     else str(c).replace(str(config.RAIZ) + "/", "")
                     for c in map(str, caminhos)]
        relativos = [r.lstrip("./") for r in relativos]

        era_aprovado = item.get("status") == "aprovado"
        item["arquivos"] = relativos
        item["sha256"] = {r: sha256_arquivo(config.RAIZ / r) for r in relativos}
        item["produzido_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

        if era_aprovado:
            # imagens novas invalidam a aprovação antiga — sem exceção
            item["status"] = "em_revisao"
            item["aprovado_por"] = None
            item["aprovado_em"] = None

        feitos.append(item["id"])

    salvar_fila(fila)
    return feitos


if __name__ == "__main__":
    alvos = [a for a in sys.argv[1:] if a.startswith("CAR-")] or None
    forcar = "--forcar" in sys.argv
    print("produzidos:", ", ".join(produzir(alvos, forcar)) or "nenhum")
