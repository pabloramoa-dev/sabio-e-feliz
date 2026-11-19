"""Piloto isolado: o Sábio lê Provérbios 15:1 e mostra aplicação cotidiana.

Não utiliza a fila editorial, não aprova e não publica no Instagram.
A narração e o visual são produzidos pelo motor oficial Kokoro + HyperFrames.
Executar: python -m pilotos.proverbio_aplicacao [--roteiro]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src import config

VERSICULO_ID = "PRO-15-01"
NOME_MP4 = "sabio-proverbio-aplicado-15-1.mp4"

# Textos autorais da demonstração: exemplo reconhecível e ação concreta.
EXEMPLO = (
    "Imagine que alguém da sua família responde com irritação. "
    "Você já está cansado e sente vontade de falar no mesmo tom. "
    "Mas isso pode transformar um problema pequeno numa discussão."
)
APLICACAO = (
    "Experimente dizer: Quero entender o que houve, mas vamos conversar com calma. "
    "Você pode estabelecer limites e discordar sem ofender. "
    "A resposta tranquila não é fraqueza; é uma escolha."
)
CONVITE = "Manda pra quem conversou com você sobre paciência."


def montar_item() -> dict:
    base = json.loads(config.PROVERBIOS_JSON.read_text(encoding="utf-8"))
    verso = next((v for v in base["versiculos"] if v["id"] == VERSICULO_ID), None)
    if not verso:
        raise RuntimeError(f"Versículo não encontrado: {VERSICULO_ID}")
    if (verso["capitulo"], verso["versiculo"]) != (15, 1):
        raise ValueError("A referência bíblica não confere")
    return {
        "id": "PILOTO-APLICACAO-15-1",
        "origem": "piloto_manual",
        "formato": "A",
        "tema": "paciência",
        "titulo": "Uma resposta muda tudo",
        "referencias": [VERSICULO_ID],
        "referencia_exibida": verso["referencia"],
        "texto_biblico": verso["texto"],
        "gancho": "",
        "reflexao": EXEMPLO,
        "aplicacao": APLICACAO,
        "cta": CONVITE,
        "curto": False,
        "status": "rascunho",
    }


def montar_segmentos(item: dict) -> list[dict]:
    # O versículo é realmente a PRIMEIRA fala: nada de cartão ou abertura falada.
    return [
        {"papel": "passagem", "texto": item["texto_biblico"],
         "expressao": "reflexao", "gesto": "livro"},
        {"papel": "reflexao", "texto": item["reflexao"],
         "expressao": "seriedade", "gesto": "explicando"},
        {"papel": "aplicacao", "texto": item["aplicacao"],
         "expressao": "acolhimento", "gesto": "explicando"},
        {"papel": "cta", "texto": item["cta"],
         "expressao": "paz", "gesto": "coracao"},
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roteiro", action="store_true",
                        help="Só mostra o roteiro, sem renderizar ou acessar rede")
    args = parser.parse_args()
    item = montar_item()
    segmentos = montar_segmentos(item)

    if args.roteiro:
        print(json.dumps({"referencia": item["referencia_exibida"],
                          "segmentos": segmentos}, ensure_ascii=False, indent=2))
        return 0

    from estudio import render, voz
    from src.validar_video import validar

    pasta = config.SAIDA / "pilotos" / "proverbio-aplicacao"
    pasta.mkdir(parents=True, exist_ok=True)
    wav = pasta / "narracao.wav"
    dados = voz.gerar(segmentos, wav, voz=voz.VOZ_PADRAO, curto=False)

    mp4 = pasta / NOME_MP4
    render.renderizar(item, wav, dados, mp4)
    tecnico = validar(mp4)
    resultado = {
        "piloto": True,
        "publicado": False,
        "arquivo": str(mp4),
        "versiculo": item["referencia_exibida"],
        "voz": dados["voz"],
        **tecnico,
    }
    (pasta / "resultado.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
