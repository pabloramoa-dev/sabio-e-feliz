import json
import math
from pathlib import Path

import pytest

from estudio import hf_sabio as S, roteiro
from estudio.sabio_vivo import POSES, roteiro_de_poses, _pose_no_tempo

FILA = json.loads((Path(__file__).resolve().parents[1] / 'conteudo/fila.json').read_text())


def dados(item):
    """Narração sintética: um segmento por papel, frases e palavras com tempo."""
    t, segs, frases, palavras = .5, [], [], []
    for seg in roteiro.montar(item):
        ini = t
        for fr in [x for x in seg['texto'].replace('. ', '.|').split('|') if x.strip()]:
            ws = fr.split()
            a = t
            for w in ws:
                palavras.append({'texto': w, 'inicio': round(t, 3), 'fim': round(t + .3, 3)})
                t += .32
            frases.append({'texto': fr, 'inicio': round(a, 3), 'fim': round(t, 3), 'papel': seg['papel']})
        t += .28
        segs.append({'papel': seg['papel'], 'inicio': round(ini, 3), 'fim': round(t, 3)})
    return {'duracao_s': round(t + 1.3, 3), 'frases': frases, 'segmentos': segs, 'palavras': palavras, 'voz': 'mudo'}


@pytest.mark.parametrize('item', FILA, ids=lambda i: i['id'])
def test_composicao_v2_usa_so_o_conteudo_do_item(item, tmp_path):
    d = dados(item)
    dur, sons = S.compor(item, d, tmp_path)
    doc = (tmp_path / 'index.html').read_text()
    assert math.isclose(dur, d['duracao_s'] + S.CAUDA, abs_tol=1e-6)
    assert 'data-composition-id="sabio-hf2"' in doc
    assert "window.__timelines['sabio-hf2']=tl" in doc
    assert 'id="capa"' in doc and 'id="fim"' in doc
    for palavra in item['texto_biblico'].split():
        assert palavra.replace('"', '&quot;') in doc or palavra in doc
    assert all(0 <= t <= dur for _, t, _ in sons)
    if item['formato'] == 'D':
        assert doc.count('class="card pergaminho"') == 3
    else:
        assert doc.count('class="card pergaminho"') == 1


def test_tempos_das_palavras_casam_com_a_narracao():
    pal = [{'texto': 'Olá', 'inicio': 1.0, 'fim': 1.2}, {'texto': 'mundo.', 'inicio': 1.3, 'fim': 1.6}]
    assert S.tempos_das_palavras('Olá mundo.', pal, .9, 2.0) == [(1.0, 1.2), (1.3, 1.6)]
    # contagem diferente: distribui proporcionalmente, em ordem
    t = S.tempos_das_palavras('um dois três', pal, .9, 2.0)
    assert len(t) == 3 and all(a < b for a, b in t) and t[0][1] <= t[1][0] + 1e-9


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -1, 999])
def test_rejeita_tempo_invalido(bad):
    d = dados(FILA[0])
    d['frases'][0]['fim'] = bad
    with pytest.raises(ValueError):
        S.validar(FILA[0], d)


def test_poses_do_sabio_cobrem_todos_os_momentos():
    for formato in ('B', 'D'):
        plano = roteiro_de_poses(dados(FILA[0])['segmentos'], formato)
        assert all(p in POSES for _, _, p, _ in plano)
        for t in (0, 2, 5, 10, 20, 40):
            pose = _pose_no_tempo(t, plano)
            assert pose['nome'] in POSES
