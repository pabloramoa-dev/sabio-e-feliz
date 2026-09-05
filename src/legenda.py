"""Monta a legenda (caption) publicada junto com o Reel."""
from __future__ import annotations

HASHTAGS_BASE = [
    "#proverbios", "#sabedoria", "#reflexao", "#fedeCristo",
    "#versiculododia", "#biblia", "#palavradedeus", "#sabioefeliz",
]

RODAPE_FONTE = (
    "Texto bíblico: João Ferreira de Almeida, domínio público (Open Bibles).\n"
    "As explicações são paráfrases, não substituem a leitura do capítulo."
)


def montar(item: dict, hashtags: list[str] | None = None) -> str:
    tags = hashtags if hashtags is not None else HASHTAGS_BASE
    partes = [
        item["titulo"].strip(),
        "",
        f"“{item['texto_biblico'].strip()}”",
        f"— {item['referencia_exibida'].strip()}",
        "",
        item["aplicacao"].strip(),
        "",
        item["cta"].strip(),
        "",
        RODAPE_FONTE,
    ]
    if tags:
        partes += ["", " ".join(tags)]

    legenda = "\n".join(partes).strip()
    if len(legenda) > 2100:  # limite prático do Instagram é 2.200
        legenda = legenda[:2097] + "..."
    return legenda
