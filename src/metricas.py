"""Coleta de métricas 24h e 72h depois da publicação.

Regra da Seção 9.3: métrica ausente é "não disponível", nunca zero.
Indicador só é calculado quando o denominador existe.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from src import config, fila
from src.instagram import Publicador


def _idade_horas(registro: dict) -> float:
    t = datetime.fromisoformat(registro["publicado_em"])
    return (datetime.now(timezone.utc) - t).total_seconds() / 3600


def compartilhamentos_por_mil(metricas: dict) -> float | None:
    alcance = metricas.get("reach")
    shares = metricas.get("shares")
    if not alcance or shares is None:
        return None
    return round(shares / alcance * 1000, 2)


def coletar() -> list[dict]:
    cfg = config.carregar(exigir_credenciais=True)
    pub = Publicador(cfg)
    publicados = fila.carregar_publicados()
    atualizados = []

    for registro in publicados:
        if not registro.get("instagram_media_id"):
            continue
        idade = _idade_horas(registro)
        alvo = None
        if 24 <= idade < 72 and registro.get("metricas_24h") is None:
            alvo = "metricas_24h"
        elif idade >= 72 and registro.get("metricas_72h") is None:
            alvo = "metricas_72h"
        if not alvo:
            continue

        dados = pub.metricas(registro["instagram_media_id"])
        dados["compartilhamentos_por_1000_alcancados"] = compartilhamentos_por_mil(dados)
        dados["coletado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        registro[alvo] = dados
        atualizados.append({"id": registro["id"], "janela": alvo, "dados": dados})

    if atualizados:
        fila.salvar_json(config.PUBLICADOS_JSON, publicados)
    return atualizados


if __name__ == "__main__":
    print(json.dumps(coletar(), ensure_ascii=False, indent=2))
