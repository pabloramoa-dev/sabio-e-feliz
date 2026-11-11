"""Regras de regressão do novo padrão aprovado pelo proprietário do canal."""
from __future__ import annotations

from copy import deepcopy

import pytest

from estudio import aplicado, reserva, roteiro
from src import fila


def modelos_originais():
    return [
        i for i in fila.carregar_fila()
        if i.get("origem") != "reserva" and i.get("formato") in ("A", "B", "C")
    ]


def test_banco_cobre_todos_os_modelos_editoriais_e_tem_alternancia():
    banco = aplicado.carregar()
    assert len(banco) >= 21
    assert all(len(cenas) >= 2 for cenas in banco.values())
    assert {m["referencias"][0] for m in modelos_originais()} <= set(banco)


@pytest.mark.parametrize("indice", [0, 1])
def test_todos_os_modelos_falam_versiculo_exemplo_e_acao(indice):
    for modelo in modelos_originais():
        item = aplicado.preparar(modelo, indice)
        segs = roteiro.montar(item)
        assert item["estilo"] == aplicado.ESTILO
        assert not item["curto"]
        assert item["formato"] in ("A", "B", "C")
        assert len(item["referencias"]) == 1
        assert [s["papel"] for s in segs] == [
            "passagem", "reflexao", "aplicacao", "cta"
        ]
        assert segs[0]["texto"] == modelo["texto_biblico"]
        assert segs[1]["texto"] == item["reflexao"]
        assert segs[2]["texto"] == item["aplicacao"]
        assert segs[3]["texto"].startswith("Manda pra ")
        assert 40 <= roteiro.palavras_totais(item) <= 130
        # O gancho é metadado para a redação, não rouba os primeiros segundos.
        assert all(s["papel"] != "gancho" for s in segs)
        assert all(s["papel"] != "abertura" for s in segs)


def test_alternativas_reais_para_cada_versiculo():
    for modelo in modelos_originais():
        a = aplicado.preparar(modelo, 0)
        b = aplicado.preparar(modelo, 1)
        assert a["reflexao"] != b["reflexao"]
        assert a["aplicacao"] != b["aplicacao"]
        assert a["texto_biblico"] == b["texto_biblico"]


def test_rejeitar_versiculo_sem_curadoria():
    item = deepcopy(modelos_originais()[0])
    item["referencias"] = ["PRO-01-01"]
    with pytest.raises(ValueError, match="Sem aplicação revisada"):
        aplicado.preparar(item)


def test_fila_a_publicar_usa_somente_formato_aplicado():
    itens = fila.carregar_fila()
    pendentes = [i for i in itens if i["status"] != "publicado"]
    assert pendentes
    for item in pendentes:
        assert item["estilo"] == aplicado.ESTILO
        assert item["status"] in ("rascunho", "em_revisao", "aprovado")
        assert not item.get("curto")
        assert item.get("sha256") is None or item["status"] != "rascunho"
        assert [s["papel"] for s in roteiro.montar(item)] == [
            "passagem", "reflexao", "aplicacao", "cta"
        ]
    assert all(i.get("publicado_em") for i in itens if i["status"] == "publicado")


def test_reserva_nova_gera_episodios_na_estrutura_aprovada(monkeypatch):
    antigos = fila.carregar_fila()
    gravados = []
    monkeypatch.setattr(reserva, "carregar_reels", lambda: deepcopy(antigos))
    monkeypatch.setattr(reserva, "salvar_reels", lambda itens: gravados.append(itens))
    novos = reserva.gerar_reels(4, semente="regressao-aplicado")
    assert len(novos) == 4
    assert len(gravados) == 1
    assert all(i["estilo"] == aplicado.ESTILO for i in novos)
    assert all(i["status"] == "rascunho" for i in novos)
    assert all(len(roteiro.montar(i)) == 4 for i in novos)
    assert all(fila.validar_item(i) == [] for i in novos)
