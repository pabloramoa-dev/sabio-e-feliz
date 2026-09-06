"""Legenda do carrossel da tarde.

Difere da legenda do Reel: aqui o texto que a pessoa lê no feed precisa
funcionar mesmo para quem não arrastar nenhum slide — por isso o versículo
vem primeiro e inteiro, e só depois o convite para arrastar.
"""
from __future__ import annotations

from src.legenda import HASHTAGS_BASE, RODAPE_FONTE

# No formato D não existe paráfrase nenhuma — só o texto bíblico. Repetir o
# aviso de paráfrase ali seria dizer algo que não é verdade sobre o post.
RODAPE_LEITURA = "Texto bíblico: João Ferreira de Almeida, domínio público (Open Bibles)."

LIMITE = 2100  # o limite do Instagram é 2.200; deixamos folga


def montar(item: dict, hashtags: list[str] | None = None) -> str:
    tags = hashtags if hashtags is not None else HASHTAGS_BASE

    if item.get("formato") == "D":
        # leitura: as três referências exatas vão na legenda, já que o vídeo
        # e a capa citam só o capítulo
        partes = [item["titulo"].strip(), ""]
        for v in item.get("versiculos", []):
            partes += [f"“{v['texto'].strip()}”", f"— {v['referencia']}", ""]
        partes += [item["cta"].strip(), "", RODAPE_LEITURA]
        if tags:
            partes += ["", " ".join(tags)]
        legenda = "\n".join(partes).strip()
        return legenda if len(legenda) <= LIMITE else legenda[: LIMITE - 3] + "..."

    partes = [
        f"“{item['texto_biblico'].strip()}”",
        f"— {item['referencia_exibida'].strip()}",
        "",
        item["gancho"].strip(),
        "",
        "Arraste até o fim: são três desdobramentos curtos e uma pergunta para hoje.",
        "",
        item["cta"].strip(),
        "",
        RODAPE_FONTE,
    ]
    if tags:
        partes += ["", " ".join(tags)]

    legenda = "\n".join(partes).strip()
    return legenda if len(legenda) <= LIMITE else legenda[: LIMITE - 3] + "..."
