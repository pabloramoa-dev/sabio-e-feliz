"""Fila editorial: seleção, validação e regras de aprovação."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from src import config

CAMPOS_OBRIGATORIOS = [
    "id", "referencia_exibida", "texto_biblico", "formato",
    "titulo", "gancho", "reflexao", "aplicacao", "cta", "arquivo",
]
STATUS_VALIDOS = {"rascunho", "em_revisao", "aprovado", "publicado", "bloqueado"}
FORMATOS = {"A", "B", "C"}

# Promessas que o plano mestre proíbe (Seção 5.3).
PALAVRAS_PROIBIDAS = [
    "vai prosperar", "deus vai te dar", "cura garantida", "milagre garantido",
    "você vai ficar rico", "vai ser abençoado com dinheiro", "castigo de deus",
    "marque quem precisa aprender", "envie para o orgulhoso",
]


def carregar_json(caminho: Path, padrao: Any) -> Any:
    if not caminho.exists():
        return padrao
    return json.loads(caminho.read_text(encoding="utf-8"))


def salvar_json(caminho: Path, dados: Any) -> None:
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def carregar_fila() -> list[dict]:
    return carregar_json(config.FILA_JSON, [])


def carregar_publicados() -> list[dict]:
    return carregar_json(config.PUBLICADOS_JSON, [])


def validar_item(item: dict, raiz: Path | None = None) -> list[str]:
    """Devolve a lista de problemas. Lista vazia = item íntegro."""
    raiz = raiz or config.RAIZ
    erros: list[str] = []

    faltando = [c for c in CAMPOS_OBRIGATORIOS if not str(item.get(c, "")).strip()]
    if faltando:
        erros.append(f"campos vazios: {faltando}")

    if item.get("status") not in STATUS_VALIDOS:
        erros.append(f"status inválido: {item.get('status')!r}")

    if item.get("formato") not in FORMATOS:
        erros.append(f"formato inválido: {item.get('formato')!r}")

    falado = " ".join(
        str(item.get(c, "")) for c in ("gancho", "texto_biblico", "reflexao", "aplicacao", "cta")
    )
    palavras = len(falado.split())
    if not 40 <= palavras <= 130:
        erros.append(f"roteiro com {palavras} palavras (esperado entre 40 e 130)")

    baixo = falado.lower()
    for proibida in PALAVRAS_PROIBIDAS:
        if proibida in baixo:
            erros.append(f"promessa proibida no roteiro: {proibida!r}")

    if item.get("cta") and falado.lower().count("compartilh") > 2:
        erros.append("mais de um convite de compartilhamento no mesmo roteiro")

    arquivo = raiz / str(item.get("arquivo", ""))
    if item.get("status") in {"aprovado", "publicado"}:
        if not arquivo.exists():
            erros.append(f"MP4 não encontrado: {item.get('arquivo')}")
        else:
            esperado = item.get("sha256")
            if not esperado:
                erros.append("item aprovado sem sha256 do MP4")
            elif sha256_arquivo(arquivo) != esperado:
                erros.append(
                    "o MP4 mudou depois da aprovação (sha256 diferente) — reaprovar antes de publicar"
                )
        if not item.get("aprovado_por"):
            erros.append("item aprovado sem responsável registrado")

    return erros


def lint(raiz: Path | None = None) -> dict:
    """Confere a fila inteira. Usado pelo workflow validar.yml."""
    fila = carregar_fila()
    ids = [i.get("id") for i in fila]
    problemas: dict[str, list[str]] = {}

    duplicados = {i for i in ids if ids.count(i) > 1}
    if duplicados:
        problemas["_fila"] = [f"IDs repetidos: {sorted(duplicados)}"]

    arquivos = [i.get("arquivo") for i in fila if i.get("arquivo")]
    dup_arq = {a for a in arquivos if arquivos.count(a) > 1}
    if dup_arq:
        problemas.setdefault("_fila", []).append(f"MP4 usado em mais de um episódio: {sorted(dup_arq)}")

    for item in fila:
        erros = validar_item(item, raiz)
        if erros:
            problemas[str(item.get("id"))] = erros

    return {
        "total": len(fila),
        "aprovados": len([i for i in fila if i.get("status") == "aprovado"]),
        "reserva_ok": len([i for i in fila if i.get("status") == "aprovado"]) >= config.RESERVA_MINIMA,
        "problemas": problemas,
    }


def proximo_episodio() -> dict:
    """Seleciona o próximo item aprovado e ainda não publicado."""
    fila = carregar_fila()
    publicados_ids = {p["id"] for p in carregar_publicados()}

    elegiveis = [
        i for i in fila
        if i.get("status") == "aprovado"
        and not i.get("publicado_em")
        and i.get("id") not in publicados_ids
    ]
    if not elegiveis:
        raise RuntimeError(
            "Nenhum episódio aprovado disponível. Produza e aprove novos Reels antes do próximo horário."
        )

    elegiveis.sort(key=lambda i: (i.get("prioridade", 100), i["id"]))
    escolhido = elegiveis[0]

    erros = validar_item(escolhido)
    if erros:
        raise RuntimeError(f"Episódio {escolhido['id']} reprovado na validação: {erros}")

    return escolhido


def publicou_hoje() -> bool:
    hoje = date.today().isoformat()
    return any(str(p.get("publicado_em", "")).startswith(hoje) for p in carregar_publicados())
