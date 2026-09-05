"""Registro auditável do que foi publicado."""
from __future__ import annotations

from datetime import datetime, timezone
import os

from src import config, fila


def registrar(item: dict, media_id: str, url_video: str, resumo_tecnico: dict) -> dict:
    publicados = fila.carregar_publicados()
    if any(p["id"] == item["id"] for p in publicados):
        raise RuntimeError(f"{item['id']} já consta no ledger — publicação duplicada evitada")

    registro = {
        "id": item["id"],
        "referencia": item["referencia_exibida"],
        "titulo": item["titulo"],
        "formato": item["formato"],
        "arquivo": item["arquivo"],
        "sha256": item.get("sha256"),
        "url_video": url_video,
        "instagram_media_id": media_id,
        "publicado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": os.getenv("GITHUB_SHA", "local"),
        "execucao": os.getenv("GITHUB_RUN_ID", "local"),
        "tecnico": resumo_tecnico,
        "metricas_24h": None,
        "metricas_72h": None,
    }
    publicados.append(registro)
    fila.salvar_json(config.PUBLICADOS_JSON, publicados)

    lista = fila.carregar_fila()
    for i in lista:
        if i["id"] == item["id"]:
            i["status"] = "publicado"
            i["publicado_em"] = registro["publicado_em"]
            i["instagram_media_id"] = media_id
    fila.salvar_json(config.FILA_JSON, lista)

    return registro
