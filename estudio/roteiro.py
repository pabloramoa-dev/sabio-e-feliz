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


def convite(item):
    if item.get("estilo") == "aplicado_v1":
        return str(item["cta"]).strip()
    tema = item.get("tema")
    if tema and tema != "leitura":
        return f"Manda pra quem conversou com você sobre {tema}."
    return "Manda pra quem lê Provérbios com você."


def montar(item: dict) -> list[dict]:
    """Devolve os segmentos falados, na ordem, com direção de cena."""
    if item.get("estilo") == "aplicado_v1":
        # Formato do piloto aprovado: primeira fala é o versículo literal.
        # O gancho continua como metadado editorial, mas não é narrado.
        return [
            dict(papel=papel, texto=texto, expressao=expressao,
                 gesto=gesto, palavras=len(texto.split()))
            for papel, texto, expressao, gesto in (
                ("passagem", item["texto_biblico"].strip(), "reflexao", "livro"),
                ("reflexao", item["reflexao"].strip(), "seriedade", "explicando"),
                ("aplicacao", item["aplicacao"].strip(), "acolhimento", "explicando"),
                ("cta", convite(item), "paz", "coracao"),
            )
        ]

    abertura = item.get("abertura") or item["texto_biblico"].split(";")[0].split(",")[0]
    saida = [dict(papel="abertura", texto=abertura, expressao="seriedade",
                  gesto="apontar", palavras=len(abertura.split()))]
    passagem = item["texto_biblico"].strip()

    for papel, campo, expressao, gesto in SEGMENTOS:
        texto = passagem if campo == "_passagem" else str(item.get(campo, "")).strip()
        if item.get("curto") and papel == "reflexao":
            continue
        if item.get("curto") and papel == "aplicacao" and item["formato"] == "D":
            continue
        if papel == "cta":
            texto = convite(item)
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
