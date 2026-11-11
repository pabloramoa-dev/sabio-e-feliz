"""Seleção determinística de exemplos cotidianos para Reels do Sábio e Feliz.

Não há geração de interpretações por IA no momento da publicação.
As duas cenas de cada versículo estão no banco editorial versionado.
"""
from __future__ import annotations

import json
from copy import deepcopy

from src import config

ESTILO = "aplicado_v1"
BANCO = config.CONTEUDO / "cenas_aplicadas.json"


def carregar() -> dict[str, list[dict]]:
    documento = json.loads(BANCO.read_text(encoding="utf-8"))
    cenas = documento["cenas"]
    if not isinstance(cenas, dict) or not cenas:
        raise ValueError("Banco de aplicações vazio")
    return cenas


def preparar(item: dict, indice: int = 0) -> dict:
    """Cria uma cópia para o formato aprovado: versículo, caso real e ação.

    Para versículos sem aplicação revisada, falha em vez de inventar ou
    publicar o antigo formato de leitura pura.
    """
    referencias = item.get("referencias") or []
    if len(referencias) != 1:
        raise ValueError("Reel aplicado requer exatamente um versículo")
    referencia = referencias[0]
    cenas = carregar().get(referencia)
    if not cenas:
        raise ValueError(f"Sem aplicação revisada para {referencia}")
    if indice < 0:
        raise ValueError("Índice de uso negativo")

    base = json.loads(config.PROVERBIOS_JSON.read_text(encoding="utf-8"))
    versiculos = {v["id"]: v for v in base["versiculos"]}
    versiculo = versiculos.get(referencia)
    if not versiculo:
        raise ValueError(f"Versículo inexistente na base: {referencia}")
    if item["texto_biblico"].strip() != versiculo["texto"].strip():
        raise ValueError(f"Texto bíblico divergente da fonte em {referencia}")

    convite = json.loads(BANCO.read_text(encoding="utf-8")).get("convites", {}).get(referencia)
    if not convite or not convite.startswith("Manda pra "):
        raise ValueError(f"{referencia}: falta convite de envio revisado")
    cena = cenas[indice % len(cenas)]
    for campo in ("reflexao", "aplicacao"):
        if not isinstance(cena.get(campo), str) or len(cena[campo].split()) < 12:
            raise ValueError(f"{referencia}: cena sem {campo} concreto")

    novo = deepcopy(item)
    novo.update({
        "estilo": ESTILO,
        "formato": item["formato"] if item["formato"] in {"A", "B", "C"} else "A",
        "curto": False,
        "texto_biblico": versiculo["texto"],
        "referencia_exibida": versiculo["referencia"],
        "reflexao": cena["reflexao"],
        "aplicacao": cena["aplicacao"],
        "cta": convite,
        "cta_tipo": "envio",
        "variante_aplicada": indice % len(cenas),
    })
    novo.pop("abertura", None)
    return novo
