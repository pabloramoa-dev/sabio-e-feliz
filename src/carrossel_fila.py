"""Fila editorial dos carrosséis — validação, sorteio e ledger.

Mesma regra de ouro dos Reels (Seção 15.1 do plano): o publicador da tarde
não desenha nada. Ele só pega um carrossel que já está APROVADO, com as sete
imagens no repositório e com o sha256 batendo, e manda para a Meta.

A diferença é a escolha: o Reel segue a ordem da fila; o carrossel é
SORTEADO entre os aprovados que ainda não foram ao ar. O sorteio usa a data
como semente, então o mesmo dia sempre escolhe o mesmo item — repetir a
execução não muda o resultado nem publica outro por engano.
"""
from __future__ import annotations

import hashlib
import random
from datetime import date
from pathlib import Path
from typing import Any

from src import config
from src.fila import PALAVRAS_PROIBIDAS, carregar_json, salvar_json, sha256_arquivo

CARROSSEIS_JSON = config.CONTEUDO / "carrosseis.json"
CARROSSEIS_PUBLICADOS_JSON = config.CONTEUDO / "carrosseis_publicados.json"
PASTA_IMAGENS = config.RAIZ / "carrosseis"

SLIDES_ESPERADOS = 7      # formato escrito; o formato D (leitura) tem 5
MIN_SLIDES, MAX_SLIDES = 2, 10          # limite da própria Graph API
STATUS_VALIDOS = {"rascunho", "em_revisao", "aprovado", "publicado", "arquivado"}

CAMPOS_TEXTO = ["titulo", "gancho", "texto_biblico", "pergunta", "cta",
                "referencia_exibida"]


def carregar_fila() -> list[dict]:
    dados = carregar_json(CARROSSEIS_JSON, {"carrosseis": []})
    return dados["carrosseis"] if isinstance(dados, dict) else dados


def salvar_fila(itens: list[dict]) -> None:
    dados = carregar_json(CARROSSEIS_JSON, {})
    if isinstance(dados, dict):
        dados["carrosseis"] = itens
        dados["total"] = len(itens)
    else:
        dados = itens
    salvar_json(CARROSSEIS_JSON, dados)


def carregar_ledger() -> list[dict]:
    return carregar_json(CARROSSEIS_PUBLICADOS_JSON, [])


def registrar(item: dict, media_id: str, quando: str) -> None:
    ledger = carregar_ledger()
    ledger.append({
        "id": item["id"],
        "referencia_exibida": item["referencia_exibida"],
        "titulo": item["titulo"],
        "instagram_media_id": media_id,
        "publicado_em": quando,
        "slides": len(item.get("arquivos", [])),
    })
    salvar_json(CARROSSEIS_PUBLICADOS_JSON, ledger)


def ja_publicados() -> set[str]:
    return {r["id"] for r in carregar_ledger()}


# --------------------------------------------------------------------- lint
def validar_item(item: dict, raiz: Path | None = None) -> list[str]:
    raiz = raiz or config.RAIZ
    erros: list[str] = []

    for campo in CAMPOS_TEXTO:
        if not str(item.get(campo, "")).strip():
            erros.append(f"campo vazio: {campo}")

    if item.get("status") not in STATUS_VALIDOS:
        erros.append(f"status inválido: {item.get('status')!r}")

    # Formato D (leitura) não tem paráfrase: em vez de três desdobramentos
    # escritos, traz três versículos do mesmo capítulo, texto bíblico puro.
    if item.get("formato") == "D":
        versiculos = item.get("versiculos") or []
        if len(versiculos) != 3:
            erros.append(f"formato D espera 3 versículos, encontrados {len(versiculos)}")
        for i, v in enumerate(versiculos, 1):
            for campo in ("referencia", "texto"):
                if not str(v.get(campo, "")).strip():
                    erros.append(f"versículo {i}: campo vazio ({campo})")
        pontos = []
    else:
        pontos = item.get("pontos") or []
        if len(pontos) != 3:
            erros.append(f"esperados 3 desdobramentos, encontrados {len(pontos)}")
        for i, ponto in enumerate(pontos, 1):
            for campo in ("etiqueta", "titulo", "corpo"):
                if not str(ponto.get(campo, "")).strip():
                    erros.append(f"desdobramento {i}: campo vazio ({campo})")

    texto = " ".join(
        [str(item.get(c, "")) for c in CAMPOS_TEXTO]
        + [f"{p.get('titulo','')} {p.get('corpo','')}" for p in pontos]
    ).lower()
    for proibida in PALAVRAS_PROIBIDAS:
        if proibida in texto:
            erros.append(f"promessa proibida no texto: {proibida!r}")

    arquivos = item.get("arquivos") or []
    if item.get("status") in {"aprovado", "publicado"}:
        if not MIN_SLIDES <= len(arquivos) <= MAX_SLIDES:
            erros.append(
                f"carrossel precisa de {MIN_SLIDES} a {MAX_SLIDES} imagens, tem {len(arquivos)}")
        somas = item.get("sha256") or {}
        for rel in arquivos:
            caminho = raiz / rel
            if not caminho.exists():
                erros.append(f"imagem não encontrada: {rel}")
                continue
            esperado = somas.get(rel)
            if not esperado:
                erros.append(f"sem sha256 registrado: {rel}")
            elif esperado != sha256_arquivo(caminho):
                erros.append(f"sha256 diferente do aprovado: {rel}")

    return erros


def conferir(raiz: Path | None = None) -> dict[str, Any]:
    fila = carregar_fila()
    problemas = {i["id"]: e for i in fila if (e := validar_item(i, raiz))}
    aprovados = [i for i in fila if i.get("status") == "aprovado"]
    disponiveis = [i for i in aprovados if i["id"] not in ja_publicados()]
    return {
        "total": len(fila),
        "aprovados": len(aprovados),
        "disponiveis": len(disponiveis),
        "reserva_ok": len(disponiveis) >= config.RESERVA_MINIMA,
        "problemas": problemas,
    }


# ------------------------------------------------------------------ sorteio
def sortear(hoje: date | None = None, raiz: Path | None = None) -> dict | None:
    """Sorteia entre os aprovados que ainda não foram publicados.

    A semente é a data + os ids disponíveis: o mesmo dia devolve sempre o
    mesmo carrossel, então rodar o workflow duas vezes no mesmo dia não muda
    a escolha — e a trava de um-por-dia faz o resto.
    """
    hoje = hoje or date.today()
    publicados = ja_publicados()
    candidatos = [
        i for i in carregar_fila()
        if i.get("status") == "aprovado"
        and not i.get("publicado_em")
        and i["id"] not in publicados
        and not validar_item(i, raiz)
    ]
    if not candidatos:
        return None
    semente = hashlib.sha256(
        (hoje.isoformat() + "|" + ",".join(sorted(i["id"] for i in candidatos)))
        .encode("utf-8")
    ).hexdigest()
    return random.Random(int(semente[:16], 16)).choice(candidatos)


def publicados_hoje(hoje: date | None = None) -> int:
    hoje = (hoje or date.today()).isoformat()
    return sum(1 for r in carregar_ledger()
               if str(r.get("publicado_em", "")).startswith(hoje))
