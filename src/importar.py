"""Traz para o ledger os Reels que foram publicados na mão.

Os nove primeiros episódios foram ao ar antes de a automação ligar. Sem o
media_id deles, o coletor de métricas não tem o que perguntar à Meta e esses
nove ficam invisíveis para o projeto — justamente os que estrearam o canal.

Este script lê as mídias recentes da conta, casa cada uma com o episódio
pelo título que abre a legenda, e preenche publicados.json. Não publica nada
e não apaga nada: só reconhece o que já existe.

    python -m src.importar
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import requests

from src import config, fila
from src.instagram import Publicador


def buscar_midias(cfg: config.Config, limite: int = 50) -> list[dict]:
    r = requests.get(
        f"{cfg.base_conta}/media",
        params={"fields": "id,caption,timestamp,media_type,permalink",
                "limit": limite, "access_token": cfg.ig_token},
        timeout=30,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {config.esconder(r.text)[:300]}")
    return r.json().get("data", [])


def importar() -> list[dict]:
    cfg = config.carregar(exigir_credenciais=True)
    midias = buscar_midias(cfg)
    lista = fila.carregar_fila()
    publicados = fila.carregar_publicados()
    ja = {p["id"] for p in publicados}
    novos = []

    for item in lista:
        if item["id"] in ja or not item.get("publicado_em"):
            continue
        titulo = item["titulo"].strip().lower()
        casada = next(
            (m for m in midias if (m.get("caption") or "").strip().lower().startswith(titulo)),
            None,
        )
        if not casada:
            continue
        registro = {
            "id": item["id"],
            "referencia": item["referencia_exibida"],
            "titulo": item["titulo"],
            "formato": item["formato"],
            "arquivo": item["arquivo"],
            "sha256": item.get("sha256"),
            "url_video": None,
            "instagram_media_id": casada["id"],
            "publicado_em": casada.get("timestamp") or datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "commit": "manual",
            "execucao": "manual",
            "tecnico": {"origem": "publicado manualmente, importado depois"},
            "permalink": casada.get("permalink"),
            "metricas_24h": None,
            "metricas_72h": None,
        }
        publicados.append(registro)
        novos.append({"id": item["id"], "media_id": casada["id"]})
        for i in lista:
            if i["id"] == item["id"]:
                i["instagram_media_id"] = casada["id"]

    if novos:
        publicados.sort(key=lambda p: p["publicado_em"])
        fila.salvar_json(config.PUBLICADOS_JSON, publicados)
        fila.salvar_json(config.FILA_JSON, lista)
    return novos


if __name__ == "__main__":
    print(json.dumps({"importados": importar()}, ensure_ascii=False, indent=1))
