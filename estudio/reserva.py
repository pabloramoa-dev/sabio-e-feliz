"""Reserva infinita — o canal nunca fica sem o que publicar.

Os novos Reels usam o formato aprovado: um versículo literal, uma
situação concreta do cotidiano e uma ação prática. As situações vêm de
conteudo/cenas_aplicadas.json (biblioteca editorial versionada, sem
interpretação de IA na hora de publicar). A seleção alterna as variações
revisadas de cada versículo, em rodízio.

Os carrosséis continuam com três versículos do mesmo capítulo, sem explicação.
Versículos novos para Reels exigem exemplo editorial revisado na biblioteca.
Não gerar vídeo de leitura pura para preencher lacunas.

    python -m estudio.reserva --carrosseis 10 --reels 10
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone

from src import config
from src.carrossel_fila import carregar_fila as carregar_carros, salvar_fila as salvar_carros
from src.fila import carregar_fila as carregar_reels, carregar_json, salvar_fila as salvar_reels, salvar_json

USADOS_JSON = config.CONTEUDO / "reserva_usados.json"

# --- filtro de versículo autocontido -----------------------------------------
MIN_CARACTERES, MAX_CARACTERES = 70, 185
INICIOS_DEPENDENTES = (
    "para ", "porque ", "e ", "mas ", "assim ", "então ", "também ", "nem ",
    "o que ", "os que ", "tal como ", "como ", "pois ",
)
NUMEROS = {
    1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco", 6: "seis",
    7: "sete", 8: "oito", 9: "nove", 10: "dez", 11: "onze", 12: "doze",
    13: "treze", 14: "catorze", 15: "quinze", 16: "dezesseis", 17: "dezessete",
    18: "dezoito", 19: "dezenove", 20: "vinte", 21: "vinte e um",
    22: "vinte e dois", 23: "vinte e três", 24: "vinte e quatro",
    25: "vinte e cinco", 26: "vinte e seis", 27: "vinte e sete",
    28: "vinte e oito", 29: "vinte e nove", 30: "trinta", 31: "trinta e um",
}


def autocontido(v: dict) -> bool:
    """Serve para ficar sozinho num slide? Corta fragmento e frase pendurada."""
    t = v["texto"].strip()
    if not MIN_CARACTERES <= len(t) <= MAX_CARACTERES:
        return False
    if not t.endswith((".", "!", "?")):
        return False
    baixo = t.lower()
    if baixo.startswith(INICIOS_DEPENDENTES):
        return False
    if baixo.startswith(("meu filho", "filho meu")):
        return False   # abre um discurso: sem o resto, fica no ar
    return True


def carregar_versiculos() -> list[dict]:
    return json.loads(config.PROVERBIOS_JSON.read_text(encoding="utf-8"))["versiculos"]


def por_capitulo() -> dict[int, list[dict]]:
    """Capítulos com pelo menos três versículos autocontidos."""
    mapa: dict[int, list[dict]] = {}
    for v in carregar_versiculos():
        if autocontido(v):
            mapa.setdefault(v["capitulo"], []).append(v)
    return {c: vs for c, vs in mapa.items() if len(vs) >= 3}


def _registro() -> dict:
    """Quantas vezes cada versículo já foi usado, e quais trios já saíram.

    Não bloqueamos capítulo: bloquear esgotaria a reserva em 30 posts. O que
    o registro faz é RODÍZIO — sempre saem os versículos menos usados, e um
    trio idêntico nunca se repete. Com 500+ versículos autocontidos isso dá
    material para anos sem repetir combinação.
    """
    return carregar_json(USADOS_JSON, {"uso": {}, "trios": []})


# --- montagem -----------------------------------------------------------------
def _trio(rng: random.Random, versos: list[dict], uso: dict, trios: set[str]):
    """Três versículos do capítulo, dando preferência aos menos usados."""
    for _ in range(40):
        ordenados = sorted(versos, key=lambda v: (uso.get(v["id"], 0), rng.random()))
        escolha = sorted(ordenados[:max(3, len(ordenados) // 3)], key=lambda v: rng.random())[:3]
        chave = "|".join(sorted(v["id"] for v in escolha))
        if chave not in trios:
            return sorted(escolha, key=lambda v: v["versiculo"]), chave
    return None, None


def gerar_carrosseis(quantos: int, semente: str | None = None) -> list[dict]:
    reg = _registro()
    pool = por_capitulo()
    rng = random.Random(semente or datetime.now(timezone.utc).isoformat())
    fila = carregar_carros()
    proximo = max([int(i["id"].split("-")[-1]) for i in fila] or [0]) + 1
    trios = set(reg["trios"])

    novos = []
    capitulos = sorted(pool)
    rng.shuffle(capitulos)
    for capitulo in (capitulos * (quantos // len(capitulos) + 1))[:quantos]:
        trio, chave = _trio(rng, pool[capitulo], reg["uso"], trios)
        if trio is None:
            continue
        trios.add(chave)
        reg["trios"].append(chave)
        for v in trio:
            reg["uso"][v["id"]] = reg["uso"].get(v["id"], 0) + 1
        novos.append({
            "id": f"CAR-{proximo:03d}",
            "origem": "reserva",
            "formato": "D",
            "referencias": [v["id"] for v in trio],
            "referencia_exibida": f"Provérbios {capitulo}",
            "capitulo": capitulo,
            "texto_biblico": trio[0]["texto"],
            "versiculos": [
                {"referencia": v["referencia"], "texto": v["texto"]} for v in trio
            ],
            "tema": "leitura",
            "titulo": f"Três de Provérbios {capitulo}",
            "gancho": "Três versículos do mesmo capítulo, sem comentário. Só o texto.",
            "pergunta": "Qual dos três você leva para hoje?",
            "cta": f"Leia Provérbios {capitulo} inteiro hoje.",
            "rosto": "assets/marca/sabio-rosto.png",
            "arquivos": [],
            "sha256": {},
            "status": "em_revisao",
            "aprovado_por": None,
            "aprovado_em": None,
            "publicado_em": None,
            "instagram_media_id": None,
            "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        proximo += 1

    if novos:
        salvar_carros(fila + novos)
        salvar_json(USADOS_JSON, reg)
    return novos


def reel_curto(numero: int, modelo: dict, indice: int = 0) -> dict:
    """Compatibilidade: gera o Reel aplicado, não o formato curto de leitura."""
    from estudio.aplicado import preparar

    novo = {
        "id": f"EP-{numero:03d}", "origem": "reserva",
        "referencias": list(modelo["referencias"]),
        "referencia_exibida": modelo["referencia_exibida"],
        "texto_biblico": modelo["texto_biblico"],
        "formato": modelo["formato"], "tema": modelo["tema"],
        "titulo": modelo["titulo"], "gancho": modelo["gancho"],
        "reflexao": modelo["reflexao"], "aplicacao": modelo["aplicacao"],
        "cta": modelo["cta"], "cta_tipo": "envio",
        "arquivo": f"reels/EP-{numero:03d}.mp4",
        "duracao_s": None, "sha256": None,
        "status": "rascunho", "aprovado_por": None,
        "aprovado_em": None, "prioridade": 50,
        "publicado_em": None, "instagram_media_id": None,
        "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return preparar(novo, indice)


def gerar_reels(quantos: int, semente: str | None = None) -> list[dict]:
    """Usa só modelos editoriais originais, nunca cópias já geradas."""
    from estudio.aplicado import ESTILO, carregar

    fila = carregar_reels()
    referencias_revisadas = set(carregar())
    modelos = [
        i for i in fila
        if i.get("origem") != "reserva"
        and i["formato"] in ("A", "B", "C")
        and len(i.get("referencias", [])) == 1
        and i["referencias"][0] in referencias_revisadas
    ]
    if not modelos:
        raise RuntimeError("Nenhum modelo de provérbio possui aplicação revisada")
    proximo = max(int(i["id"].split("-")[-1]) for i in fila) + 1
    rng = random.Random(semente)
    rng.shuffle(modelos)
    usos = {m["referencias"][0]: 0 for m in modelos}
    for item in fila:
        ref = (item.get("referencias") or [None])[0]
        if item.get("estilo") == ESTILO and ref in usos:
            usos[ref] += 1

    novos = []
    for numero in range(proximo, proximo + quantos):
        modelo = min(modelos, key=lambda m: usos[m["referencias"][0]])
        ref = modelo["referencias"][0]
        novos.append(reel_curto(numero, modelo, usos[ref]))
        usos[ref] += 1
    if novos:
        salvar_reels(fila + novos)
    return novos


def main() -> int:
    p = argparse.ArgumentParser(description="Repõe a reserva do canal")
    p.add_argument("--carrosseis", type=int, default=0)
    p.add_argument("--reels", type=int, default=0)
    p.add_argument("--semente", default=None)
    a = p.parse_args()

    saida = {
        "carrosseis": [i["id"] for i in gerar_carrosseis(a.carrosseis, a.semente)],
        "reels": [i["id"] for i in gerar_reels(a.reels, a.semente)],
    }
    print(json.dumps(saida, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
