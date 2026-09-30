import json
from pathlib import Path
import pytest
from estudio.hyperframes import montar_timeline

FILA=json.loads((Path(__file__).resolve().parents[1]/'conteudo/fila.json').read_text())

def dados(item):
    campos=['gancho','texto_biblico','reflexao','aplicacao','cta']
    papeis=['gancho','passagem','reflexao','aplicacao','cta']
    return {'duracao_s':27,'frases':[{'papel':p,'texto':item[c], 'inicio':.5+5*i,'fim':5+5*i} for i,(p,c) in enumerate(zip(papeis,campos))]}

@pytest.mark.parametrize('item',FILA,ids=lambda i:i['id'])
def test_todos_episodios_preservam_conteudo(item):
    d=dados(item)
    ep,segs=montar_timeline(item,d)
    assert [b['fala'] for b in ep['batidas']]==[f['texto'] for f in d['frases']]
    assert ep['fim']==item['cta']
    assert all(b['hf']['selo']==item['referencia_exibida'].upper() for b in ep['batidas'])
    assert segs[-1]['fim']==27
    if item['formato']=='D':
        assert all(b['arte'][0]=='livro' for b in ep['batidas'])
        for b in ep['batidas'][1:4]:
            assert b['hf']['titulo']==b['fala'].upper()

@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-1,30])
def test_rejeita_tempo_invalido(bad):
    d=dados(FILA[0]);d['frases'][0]['fim']=bad
    with pytest.raises(ValueError):montar_timeline(FILA[0],d)

def test_rejeita_frases_sobrepostas():
    d=dados(FILA[0]);d['frases'][1]['inicio']=1
    with pytest.raises(ValueError):montar_timeline(FILA[0],d)
