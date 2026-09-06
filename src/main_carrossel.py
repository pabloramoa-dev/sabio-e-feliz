"""Orquestrador da publicação do carrossel da tarde (@sabioefeliz).

Uso:
    python -m src.main_carrossel          # respeita DRY_RUN / PUBLICAR_ATIVO

Mesmas três travas do Reel da manhã, com um ledger próprio para que as duas
publicações do dia não briguem pelo limite uma da outra:
  1. DRY_RUN=true          -> valida tudo e para antes de falar com a Meta
  2. PUBLICAR_ATIVO=false  -> nunca publica, mesmo com DRY_RUN=false
  3. um carrossel por dia
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from src import carrossel_fila as cfila
from src import config, legenda_carrossel
from src.instagram import Publicador


def url_publica(cfg: config.Config, caminho_relativo: str) -> str:
    return f"{cfg.raw_base_url}/{caminho_relativo.lstrip('/')}"


def executar() -> dict:
    cfg = config.carregar(exigir_credenciais=True)

    item = cfila.sortear()
    if item is None:
        return {
            "publicado": False,
            "motivo": "nenhum carrossel aprovado disponível — a fila da tarde está vazia.",
            "resumo": cfila.conferir(),
        }

    erros = cfila.validar_item(item)
    if erros:
        raise RuntimeError(f"{item['id']} não passou no lint na hora de publicar: {erros}")

    texto = legenda_carrossel.montar(item)
    resultado = {
        "carrossel": item["id"],
        "referencia": item["referencia_exibida"],
        "titulo": item["titulo"],
        "slides": len(item["arquivos"]),
        "legenda_previa": texto[:180] + ("..." if len(texto) > 180 else ""),
        "publicado": False,
    }

    if cfg.dry_run:
        resultado["motivo"] = "DRY_RUN ligado: nada foi enviado à Meta."
        return resultado

    if not cfg.publicar_ativo:
        resultado["motivo"] = "PUBLICAR_ATIVO desligado: a chave geral de publicação está fechada."
        return resultado

    if cfila.publicados_hoje() >= config.MAX_PUBLICACOES_POR_DIA:
        resultado["motivo"] = "já houve um carrossel hoje; limite diário respeitado."
        return resultado

    pub = Publicador(cfg)

    conta = pub.conferir_conta()
    resultado["conta"] = conta
    if conta.get("username") and conta["username"].lower() not in {"sabioefeliz", "sabio_e_feliz"}:
        raise RuntimeError(
            f"INCIDENTE: o token aponta para @{conta['username']}, não para a conta de "
            "provérbios. Publicação abortada."
        )

    filhos = [pub.criar_item_carrossel(url_publica(cfg, rel)) for rel in item["arquivos"]]
    resultado["containers_filhos"] = filhos

    pai = pub.criar_container_carrossel(filhos, texto)
    resultado["container_id"] = pai
    pub.aguardar_pronto(pai)

    try:
        media_id = pub.publicar(pai)
    except Exception as erro:  # timeout ou rede: estado indefinido
        provavel = pub.reconciliar(pai)
        raise RuntimeError(
            f"Publicação em estado indefinido ({erro}). Última mídia da conta: {provavel}. "
            "Conferir no Instagram ANTES de rodar de novo."
        ) from erro

    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cfila.registrar(item, media_id, agora)

    fila = cfila.carregar_fila()
    for i in fila:
        if i["id"] == item["id"]:
            i["status"] = "publicado"
            i["publicado_em"] = agora
            i["instagram_media_id"] = media_id
    cfila.salvar_fila(fila)

    resultado.update({"publicado": True, "instagram_media_id": media_id, "registro": agora})
    return resultado


def main() -> int:
    if "--conferir" in sys.argv:
        print(json.dumps(cfila.conferir(), ensure_ascii=False, indent=2))
        return 0
    try:
        saida = executar()
    except Exception as erro:
        print(json.dumps({"ok": False, "erro": config.esconder(str(erro))},
                         ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, **saida}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
