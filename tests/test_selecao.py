import pytest

from src import fila


BASE = {
    "id": "EP-999",
    "referencias": ["PRO-15-01"],
    "referencia_exibida": "Provérbios 15:1",
    "texto_biblico": "A resposta branda desvia o furor, mas a palavra dura suscita a ira.",
    "formato": "A",
    "titulo": "Teste",
    "gancho": "Você ia mandar essa mensagem com raiva?",
    "reflexao": "A resposta já estava pronta na sua cabeça, mas ela resolveria o problema ou começaria outro?",
    "aplicacao": "Antes de enviar, releia e tire a parte que só aumenta a briga do texto.",
    "cta": "Envie para quem sabe acalmar uma conversa.",
    "arquivo": "reels/EP-999.mp4",
    "status": "rascunho",
}


def test_item_rascunho_completo_passa():
    assert fila.validar_item(dict(BASE)) == []


def test_campo_vazio_reprova():
    item = dict(BASE, cta="")
    assert any("campos vazios" in e for e in fila.validar_item(item))


def test_promessa_proibida_reprova():
    item = dict(BASE, aplicacao="Faça isso e você vai ficar rico antes do fim do ano, com certeza.")
    assert any("promessa proibida" in e for e in fila.validar_item(item))


def test_aprovado_sem_mp4_reprova():
    item = dict(BASE, status="aprovado", aprovado_por="Pablo", sha256="abc")
    assert any("MP4 não encontrado" in e for e in fila.validar_item(item))


def test_status_invalido_reprova():
    item = dict(BASE, status="pronto")
    assert any("status inválido" in e for e in fila.validar_item(item))


def test_roteiro_curto_demais_reprova():
    item = dict(BASE, gancho="Oi", reflexao="Curto", aplicacao="Curto", cta="Curto",
                texto_biblico="Curto")
    assert any("palavras" in e for e in fila.validar_item(item))


def test_sem_aprovado_disponivel_levanta_erro(monkeypatch):
    monkeypatch.setattr(fila, "carregar_fila", lambda: [dict(BASE, status="rascunho")])
    monkeypatch.setattr(fila, "carregar_publicados", lambda: [])
    with pytest.raises(RuntimeError):
        fila.proximo_episodio()
