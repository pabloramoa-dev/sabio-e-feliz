"""Orquestrador da publicação diária do @sabioefeliz.

Uso:
    python -m src.main            # respeita DRY_RUN / PUBLICAR_ATIVO
    python -m src.main --conta    # só confere a qual conta o token aponta

Trave de segurança em três camadas:
  1. DRY_RUN=true  -> valida tudo e para antes de falar com a Meta
  2. PUBLICAR_ATIVO=false -> nunca publica, mesmo com DRY_RUN=false
  3. uma publicação por dia por conta
"""
from __future__ import annotations

import json
import sys

from src import config, fila, ledger, legenda, validar_video
from src.instagram import Publicador


def url_publica(cfg: config.Config, caminho_relativo: str) -> str:
    return f"{cfg.raw_base_url}/{caminho_relativo.lstrip('/')}"


def executar() -> dict:
    cfg = config.carregar(exigir_credenciais=True)

    item = fila.proximo_episodio()
    video = config.RAIZ / item["arquivo"]
    from tools.channel_ops import validate_render
    if item.get("render_receipt"):
        from tools.channel_ops import atomic_json
        atomic_json(video.with_suffix(".production.json"), item["render_receipt"])
    validate_render(video, item, config.RAIZ)
    tecnico = validar_video.validar(video)
    texto_legenda = legenda.montar(item)

    resultado = {
        "episodio": item["id"],
        "referencia": item["referencia_exibida"],
        "titulo": item["titulo"],
        "arquivo": item["arquivo"],
        "tecnico": tecnico,
        "legenda_previa": texto_legenda[:180] + ("..." if len(texto_legenda) > 180 else ""),
        "publicado": False,
    }

    if cfg.dry_run:
        resultado["motivo"] = "DRY_RUN ligado: nada foi enviado à Meta."
        return resultado

    if not cfg.publicar_ativo:
        resultado["motivo"] = "PUBLICAR_ATIVO desligado: a chave geral de publicação está fechada."
        return resultado

    if fila.publicou_hoje():
        resultado["motivo"] = "já houve uma publicação hoje; limite diário respeitado."
        return resultado

    pub = Publicador(cfg)

    conta = pub.conferir_conta()
    resultado["conta"] = conta
    if conta.get("username") and conta["username"].lower() not in {"sabioefeliz", "sabio_e_feliz"}:
        raise RuntimeError(
            f"INCIDENTE: o token aponta para @{conta['username']}, não para a conta de provérbios. Publicação abortada."
        )

    url_video = url_publica(cfg, item["arquivo"])
    from tools.channel_ops import resume_send, pending_send, confirm_send
    media_id = resume_send(config.RAIZ, item['id'], lambda cid: pub.reconciliar(cid, texto_legenda))
    if not media_id:
        container = pub.criar_container(url_video, texto_legenda)
        resultado["container_id"] = container

        pub.aguardar_pronto(container)

        pending_send(config.RAIZ, item['id'], container)
        try:
            media_id = pub.publicar(container)
        except Exception as erro:  # timeout ou erro transitório após media_publish
            media_id = pub.reconciliar(container, texto_legenda)
            if not media_id:
                raise RuntimeError(
                    f"Publicação em estado indefinido ({erro}). Nenhuma mídia recente com a legenda esperada foi encontrada. "
                    "Conferir no Instagram ANTES de rodar de novo."
                ) from erro
            resultado["reconciliado_apos_erro"] = True

        confirm_send(config.RAIZ, item['id'], media_id)

    registro = ledger.registrar(item, media_id, url_video, tecnico)
    resultado.update({"publicado": True, "instagram_media_id": media_id, "registro": registro["publicado_em"]})
    return resultado


def main() -> int:
    if "--conta" in sys.argv:
        cfg = config.carregar(exigir_credenciais=True)
        print(json.dumps(Publicador(cfg).conferir_conta(), ensure_ascii=False, indent=2))
        return 0

    try:
        saida = executar()
    except Exception as erro:
        print(json.dumps({"ok": False, "erro": config.esconder(str(erro))}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps({"ok": True, **saida}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
