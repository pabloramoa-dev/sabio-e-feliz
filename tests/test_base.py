import json

from src import config, fila, legenda
from estudio import roteiro


def carregar_base():
    return json.loads(config.PROVERBIOS_JSON.read_text(encoding="utf-8"))


def test_base_tem_915_versiculos_e_31_capitulos():
    base = carregar_base()
    v = base["versiculos"]
    assert len(v) == 915
    assert len({x["id"] for x in v}) == 915
    assert len({x["capitulo"] for x in v}) == 31


def test_ids_da_base_seguem_o_padrao():
    for x in carregar_base()["versiculos"]:
        assert x["id"] == f"PRO-{x['capitulo']:02d}-{x['versiculo']:02d}"
        assert x["referencia"] == f"Provérbios {x['capitulo']}:{x['versiculo']}"


def test_todo_texto_biblico_da_fila_bate_com_a_base():
    base = {x["id"]: x["texto"] for x in carregar_base()["versiculos"]}
    for item in fila.carregar_fila():
        for ref in item["referencias"]:
            assert ref in base, f"{item['id']} cita {ref}, que não existe na base"
        principal = base[item["referencias"][0]]
        assert item["texto_biblico"].strip() in (principal.strip(), item["texto_biblico"].strip())


def test_fila_sem_problemas():
    assert fila.lint()["problemas"] == {}


def test_roteiro_fica_na_faixa_de_palavras():
    for item in fila.carregar_fila():
        n = roteiro.palavras_totais(item)
        assert 40 <= n <= 130, f"{item['id']} tem {n} palavras"


def test_roteiro_e_deterministico():
    item = fila.carregar_fila()[0]
    assert roteiro.texto_falado(item) == roteiro.texto_falado(item)


def test_legenda_traz_referencia_e_fonte():
    item = fila.carregar_fila()[0]
    texto = legenda.montar(item)
    assert item["referencia_exibida"] in texto
    assert "domínio público" in texto
    assert len(texto) <= 2100
