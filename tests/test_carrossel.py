"""Testes da fila e do publicador de carrossel."""
from __future__ import annotations

import json
from datetime import date

import pytest

from src import carrossel_fila as cf
from src import legenda_carrossel


def item_valido(**extra) -> dict:
    base = {
        "id": "CAR-999",
        "referencia_exibida": "Provérbios 1:1",
        "texto_biblico": "Provérbios de Salomão, filho de Davi, rei de Israel:",
        "titulo": "Um título",
        "gancho": "Um gancho curto.",
        "pergunta": "Uma pergunta?",
        "cta": "Um fechamento.",
        "pontos": [
            {"etiqueta": "a", "titulo": "t1", "corpo": "c1"},
            {"etiqueta": "b", "titulo": "t2", "corpo": "c2"},
            {"etiqueta": "c", "titulo": "t3", "corpo": "c3"},
        ],
        "status": "em_revisao",
        "arquivos": [],
        "sha256": {},
    }
    base.update(extra)
    return base


def test_item_completo_passa():
    assert cf.validar_item(item_valido()) == []


def test_campo_vazio_reprova():
    erros = cf.validar_item(item_valido(titulo="  "))
    assert any("titulo" in e for e in erros)


def test_precisa_de_tres_desdobramentos():
    erros = cf.validar_item(item_valido(pontos=[{"etiqueta": "a", "titulo": "t", "corpo": "c"}]))
    assert any("desdobramentos" in e for e in erros)


def test_promessa_proibida_reprova():
    erros = cf.validar_item(item_valido(cta="Faça isso e Deus vai te dar o dobro"))
    assert any("proibida" in e for e in erros)


def test_aprovado_sem_imagem_reprova():
    erros = cf.validar_item(item_valido(status="aprovado"))
    assert any("imagens" in e for e in erros)


def test_status_invalido_reprova():
    assert any("status" in e for e in cf.validar_item(item_valido(status="qualquer")))


def test_sha256_diferente_reprova(tmp_path):
    pasta = tmp_path / "carrosseis" / "CAR-999"
    pasta.mkdir(parents=True)
    arquivos = []
    for i in range(1, 8):
        f = pasta / f"CAR-999-{i:02d}.jpg"
        f.write_bytes(b"imagem")
        arquivos.append(f"carrosseis/CAR-999/CAR-999-{i:02d}.jpg")
    item = item_valido(status="aprovado", arquivos=arquivos,
                       sha256={a: "0" * 64 for a in arquivos})
    erros = cf.validar_item(item, raiz=tmp_path)
    assert all("sha256 diferente" in e for e in erros)
    assert len(erros) == 7


def test_sorteio_e_estavel_no_mesmo_dia(monkeypatch):
    fila = [item_valido(id=f"CAR-{i:03d}", status="aprovado") for i in range(1, 6)]
    monkeypatch.setattr(cf, "carregar_fila", lambda: fila)
    monkeypatch.setattr(cf, "ja_publicados", lambda: set())
    monkeypatch.setattr(cf, "validar_item", lambda item, raiz=None: [])
    hoje = date(2026, 9, 7)
    escolhas = {cf.sortear(hoje)["id"] for _ in range(20)}
    assert len(escolhas) == 1


def test_sorteio_muda_de_dia(monkeypatch):
    fila = [item_valido(id=f"CAR-{i:03d}", status="aprovado") for i in range(1, 15)]
    monkeypatch.setattr(cf, "carregar_fila", lambda: fila)
    monkeypatch.setattr(cf, "ja_publicados", lambda: set())
    monkeypatch.setattr(cf, "validar_item", lambda item, raiz=None: [])
    dias = {cf.sortear(date(2026, 9, d))["id"] for d in range(7, 25)}
    assert len(dias) > 1


def test_sorteio_ignora_ja_publicado(monkeypatch):
    fila = [item_valido(id="CAR-001", status="aprovado"),
            item_valido(id="CAR-002", status="aprovado")]
    monkeypatch.setattr(cf, "carregar_fila", lambda: fila)
    monkeypatch.setattr(cf, "ja_publicados", lambda: {"CAR-001"})
    monkeypatch.setattr(cf, "validar_item", lambda item, raiz=None: [])
    assert cf.sortear(date(2026, 9, 7))["id"] == "CAR-002"


def test_sorteio_sem_candidato_devolve_none(monkeypatch):
    monkeypatch.setattr(cf, "carregar_fila", lambda: [])
    monkeypatch.setattr(cf, "ja_publicados", lambda: set())
    assert cf.sortear(date(2026, 9, 7)) is None


def test_legenda_traz_versiculo_e_fonte():
    texto = legenda_carrossel.montar(item_valido())
    assert "Provérbios 1:1" in texto
    assert "domínio público" in texto
    assert len(texto) <= legenda_carrossel.LIMITE


def test_fila_do_repositorio_esta_limpa():
    """A fila de verdade não pode ter item quebrado."""
    problemas = {i["id"]: e for i in cf.carregar_fila() if (e := cf.validar_item(i))}
    assert problemas == {}


def test_fila_do_repositorio_tem_a_contagem_certa_de_slides():
    """Formato escrito = 7 slides; formato D (leitura) = 5."""
    for item in cf.carregar_fila():
        if not item.get("arquivos"):
            continue
        esperado = 5 if item.get("formato") == "D" else cf.SLIDES_ESPERADOS
        assert len(item["arquivos"]) == esperado, item["id"]


def test_formato_D_aceita_versiculos_no_lugar_dos_desdobramentos():
    item = item_valido(formato="D", pontos=[], versiculos=[
        {"referencia": "Provérbios 1:2", "texto": "a"},
        {"referencia": "Provérbios 1:3", "texto": "b"},
        {"referencia": "Provérbios 1:4", "texto": "c"},
    ])
    assert cf.validar_item(item) == []


def test_formato_D_exige_tres_versiculos():
    item = item_valido(formato="D", pontos=[], versiculos=[
        {"referencia": "Provérbios 1:2", "texto": "a"}])
    assert any("3 versículos" in e for e in cf.validar_item(item))


def test_legenda_de_leitura_nao_promete_parafrase():
    from src import legenda_carrossel as lc
    item = item_valido(formato="D", versiculos=[
        {"referencia": "Provérbios 1:2", "texto": "a"},
        {"referencia": "Provérbios 1:3", "texto": "b"},
        {"referencia": "Provérbios 1:4", "texto": "c"},
    ])
    texto = lc.montar(item)
    assert "paráfrases" not in texto
    assert "Provérbios 1:3" in texto


# --------------------------------------------------------------- reserva
def test_reserva_so_aceita_versiculo_autocontido():
    from estudio.reserva import autocontido
    assert not autocontido({"texto": "Para se conhecer a sabedoria e a instrução;"})
    assert not autocontido({"texto": "E disse:"})
    assert autocontido({"texto":
        "A resposta branda desvia o furor, mas a palavra dura suscita a ira, "
        "e quem cala nem sempre concorda com o que ouviu."})


def test_reserva_tem_material_de_sobra():
    """Precisa haver capítulo suficiente para o canal nunca secar."""
    from estudio.reserva import por_capitulo
    pool = por_capitulo()
    assert len(pool) >= 25
    assert sum(len(v) for v in pool.values()) >= 400


def test_aprovacao_automatica_recusa_item_quebrado(monkeypatch):
    from src import aprovar_auto
    quebrado = item_valido(status="em_revisao", titulo="")
    monkeypatch.setattr(aprovar_auto.cfila, "carregar_fila", lambda: [quebrado])
    monkeypatch.setattr(aprovar_auto.cfila, "salvar_fila", lambda itens: None)
    saida = aprovar_auto.aprovar_carrosseis()
    assert saida["aprovados"] == []
    assert "CAR-999" in saida["recusados"]
    assert quebrado["status"] == "em_revisao"


def test_aprovacao_automatica_assina_como_automatico(monkeypatch, tmp_path):
    from src import aprovar_auto
    from src.fila import sha256_arquivo

    pasta = tmp_path / "carrosseis" / "CAR-999"
    pasta.mkdir(parents=True)
    arquivos, somas = [], {}
    for i in range(1, 6):
        f = pasta / f"CAR-999-{i:02d}.jpg"
        f.write_bytes(f"imagem {i}".encode())
        rel = f"carrosseis/CAR-999/CAR-999-{i:02d}.jpg"
        arquivos.append(rel)
        somas[rel] = sha256_arquivo(f)

    bom = item_valido(status="em_revisao", formato="D", pontos=[],
                      arquivos=arquivos, sha256=somas, versiculos=[
        {"referencia": "Provérbios 1:2", "texto": "a"},
        {"referencia": "Provérbios 1:3", "texto": "b"},
        {"referencia": "Provérbios 1:4", "texto": "c"},
    ])
    monkeypatch.setattr(aprovar_auto.cfila, "carregar_fila", lambda: [bom])
    monkeypatch.setattr(aprovar_auto.cfila, "salvar_fila", lambda itens: None)
    saida = aprovar_auto.aprovar_carrosseis(raiz=tmp_path)
    assert saida["aprovados"] == ["CAR-999"]
    assert bom["aprovado_por"] == "automatico"


def test_aprovacao_automatica_recusa_imagem_adulterada(monkeypatch, tmp_path):
    """A trava que sobrevive ao fim da aprovação humana: o sha256."""
    from src import aprovar_auto
    pasta = tmp_path / "carrosseis" / "CAR-999"
    pasta.mkdir(parents=True)
    arquivos = []
    for i in range(1, 6):
        (pasta / f"CAR-999-{i:02d}.jpg").write_bytes(b"outra coisa")
        arquivos.append(f"carrosseis/CAR-999/CAR-999-{i:02d}.jpg")

    item = item_valido(status="em_revisao", formato="D", pontos=[],
                       arquivos=arquivos, sha256={a: "0" * 64 for a in arquivos},
                       versiculos=[{"referencia": "Provérbios 1:2", "texto": "a"},
                                   {"referencia": "Provérbios 1:3", "texto": "b"},
                                   {"referencia": "Provérbios 1:4", "texto": "c"}])
    monkeypatch.setattr(aprovar_auto.cfila, "carregar_fila", lambda: [item])
    monkeypatch.setattr(aprovar_auto.cfila, "salvar_fila", lambda itens: None)
    saida = aprovar_auto.aprovar_carrosseis(raiz=tmp_path)
    assert saida["aprovados"] == []
    assert item["status"] == "em_revisao"
