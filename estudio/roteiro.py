"""Roteiro determinístico: o mesmo item da fila gera sempre o mesmo vídeo."""
from __future__ import annotations

SEGMENTOS = [
    # papel,        campo,           expressão,      gesto
    ("gancho",      "gancho",        "duvida",       "apontar"),
    ("passagem",    "_passagem",     "reflexao",     "livro"),
    ("reflexao",    "reflexao",      "seriedade",    "explicando"),
    ("aplicacao",   "aplicacao",     "acolhimento",  "explicando"),
    ("cta",         "cta",           "paz",          "coracao"),
]


def montar(item: dict) -> list[dict]:
    """Devolve os segmentos falados, na ordem, com direção de cena."""
    passagem = (
        f"O provérbio de hoje está em {item['referencia_exibida']}. "
        f"{item['texto_biblico'].strip()}"
    )
    saida = []
    for papel, campo, expressao, gesto in SEGMENTOS:
        texto = passagem if campo == "_passagem" else str(item.get(campo, "")).strip()
        if not texto:
            continue
        saida.append({
            "papel": papel,
            "texto": texto,
            "expressao": expressao,
            "gesto": gesto,
            "palavras": len(texto.split()),
        })
    return saida


def texto_falado(item: dict) -> str:
    return " ".join(s["texto"] for s in montar(item))


def palavras_totais(item: dict) -> int:
    return len(texto_falado(item).split())
