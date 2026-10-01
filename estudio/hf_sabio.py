"""Compositor HyperFrames v2 do @sabioefeliz (01/10/2026).

Recebe o item editorial e os tempos REAIS da narração (segmentos, frases e
palavras) e devolve o index.html que o HyperFrames renderiza por cima do
Sábio vivo (estudio/sabio_vivo.py).

Recursos usados:
  * capa central animada nos 2,2 s iniciais (é ela que vira a miniatura
    da grade — o Instagram recorta o quadrado do meio);
  * câmera: aproximação por momento do roteiro, deriva lenta e "punch-in";
  * gradação quente com brilho suave (bloom) na camada do Sábio;
  * cartões diferentes por momento: pergunta, pergaminho do versículo com
    selo de cera, lâmpada da reflexão, lista "pratique hoje", ações do CTA;
  * texto revelado palavra a palavra no tempo exato da fala;
  * legenda karaokê com a palavra ativa saltando em dourado;
  * transições alternadas: virada de página, faixa dourada, clarão de luz,
    abertura em círculo;
  * brilho do sol, raio de luz, poeira dourada (bokeh) e grão de papel;
  * barra de progresso com o sol caminhando;
  * encerramento com "Siga @sabioefeliz", botão sendo tocado e estrelinhas;
  * trilha original (acordes suaves + caixinha de música + passarinhos na
    abertura), abafada por baixo da voz, e efeitos sonoros sincronizados.

Nenhum texto do episódio é inventado: tudo que aparece vem do item da fila.
"""
from __future__ import annotations

import html
import json
import math
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import ImageFont

RAIZ = Path(__file__).resolve().parent.parent


def achar(nome, *pastas):
    """Arquivo de apoio (fonte, efeito, CSS): procura nas pastas organizadas e,
    se não estiver lá, em estudio/ — o upload pelo navegador põe tudo junto."""
    for pasta in (*pastas, 'estudio'):
        arq = RAIZ / pasta / nome
        if arq.is_file():
            return arq
    raise FileNotFoundError(f'{nome} não encontrado em {", ".join(pastas)} nem em estudio/')


F_BOLD = achar('Poppins-Bold.ttf', 'assets/fonts')
F_MED = achar('Poppins-Medium.ttf', 'assets/fonts')
F_LORA = achar('Lora-Italic-Variable.ttf', 'assets/fonts')

FPS = 30
CAPA = 2.2          # capa central no ar (miniatura da grade)
CAUDA = 2.6         # encerramento depois da última fala
TRANSICOES = ['folha', 'faixa', 'clarao', 'circulo']
ROTULOS = {
    'gancho': 'PARA COMEÇAR',
    'passagem': 'A PALAVRA',
    'reflexao': 'PARA PENSAR',
    'aplicacao': 'PRATIQUE HOJE',
    'cta': 'LEVE COM VOCÊ',
}
CAMERA = {  # escala, deslocamento y (px) — y negativo sobe o rosto
    'gancho': (1.07, 10), 'passagem': (1.0, 0), 'reflexao': (1.09, 14),
    'aplicacao': (1.04, 6), 'cta': (1.0, 0),
}

e = html.escape


# ---------------------------------------------------------------------
#  medida de texto
# ---------------------------------------------------------------------
def _quebrar(txt, fonte, tam, largura):
    f = ImageFont.truetype(str(fonte), tam)
    linhas, atual = [], []
    for w in txt.split():
        cand = ' '.join(atual + [w])
        if f.getlength(cand) > largura and atual:
            linhas.append(atual)
            atual = [w]
        else:
            atual.append(w)
        if f.getlength(w) > largura:
            return None
    if atual:
        linhas.append(atual)
    return linhas


def caber(txt, fonte, largura, altura, maximo, minimo, entrelinha=1.22):
    """Maior corpo de letra em que o texto cabe na caixa. Devolve (tam, linhas)."""
    txt = ' '.join(str(txt).split())
    for tam in range(maximo, minimo - 1, -1):
        ls = _quebrar(txt, fonte, tam, largura)
        if ls and len(ls) * tam * entrelinha <= altura:
            return tam, ls
    return minimo, _quebrar(txt, fonte, minimo, largura) or [txt.split()]


# ---------------------------------------------------------------------
#  tempos
# ---------------------------------------------------------------------
def _limpa(w):
    return re.sub(r'[^\wÀ-ÿ]', '', w.lower())


def tempos_das_palavras(texto, palavras, ini, fim):
    """Tempo (início, fim) de cada palavra do texto escrito.

    Usa as palavras medidas na narração dentro do trecho; se a contagem não
    bater (pontuação, número por extenso), distribui pelo tamanho.
    """
    ws = texto.split()
    trecho = [p for p in palavras if ini - .02 <= float(p['inicio']) < fim + .02]
    if len(trecho) >= len(ws):
        trecho = trecho[len(trecho) - len(ws):]
        if all(_limpa(a) == _limpa(b['texto']) or not _limpa(a) for a, b in zip(ws, trecho)):
            return [(float(p['inicio']), float(p['fim'])) for p in trecho]
    a0 = trecho[-len(ws)]['inicio'] if len(trecho) >= len(ws) and ws else ini
    a0 = float(a0) if a0 else ini
    pesos = [max(2, len(w)) for w in ws]
    tot = sum(pesos) or 1
    t, out = a0, []
    for p in pesos:
        d = (fim - a0) * p / tot
        out.append((t, t + d))
        t += d
    return out


def validar(item, dados):
    dur = float(dados['duracao_s'])
    if not math.isfinite(dur) or dur <= 0:
        raise ValueError('Duração inválida')
    segs = dados['segmentos']
    if not segs:
        raise ValueError('Narração sem segmentos')
    ant = 0.0
    for s in segs:
        a, z = float(s['inicio']), float(s['fim'])
        if not (math.isfinite(a) and math.isfinite(z)) or a < ant - .001 or z <= a or z > dur + .01:
            raise ValueError('Tempos de segmento inválidos')
        ant = z
    ant = 0.0
    for f in dados['frases']:
        a, z = float(f['inicio']), float(f['fim'])
        if not (math.isfinite(a) and math.isfinite(z)) or a < ant - .001 or z <= a or z > dur + .01:
            raise ValueError('Tempos de frase inválidos')
        if not f['texto'].strip():
            raise ValueError('Frase vazia')
        ant = z
    return round(dur + CAUDA, 3)


def _versiculo(ref):
    m = re.match(r'PRO-(\d+)-(\d+)', str(ref))
    return (int(m.group(1)), int(m.group(2))) if m else None


# ---------------------------------------------------------------------
#  peças
# ---------------------------------------------------------------------
SOL_SVG = ('<svg viewBox="0 0 100 100"><g fill="#f4c55b">'
           + ''.join(f'<rect x="47" y="2" width="6" height="18" rx="3" transform="rotate({a} 50 50)"/>'
                     for a in range(0, 360, 45))
           + '</g><circle cx="50" cy="50" r="22" fill="#ffd978" stroke="#174a56" stroke-width="5"/></svg>')

LAMPADA = ('<svg class="ic" viewBox="0 0 120 150"><circle class="glow" cx="60" cy="58" r="56" fill="#ffe28a" opacity=".45"/>'
           '<path d="M60 14a40 40 0 0 0-24 72c6 5 9 11 9 18h30c0-7 3-13 9-18a40 40 0 0 0-24-72z" fill="#ffe08a" '
           'stroke="#174a56" stroke-width="6"/><path d="M48 112h24M50 124h20" stroke="#174a56" stroke-width="7" '
           'stroke-linecap="round"/><path d="M52 92l8-26 8 26" fill="none" stroke="#d48a2e" stroke-width="5"/></svg>')

PERGUNTA = ('<svg class="ic" viewBox="0 0 120 120"><circle cx="60" cy="60" r="54" fill="#174a56"/>'
            '<text x="60" y="84" text-anchor="middle" font-size="76" font-family="SabioBold" fill="#f4c55b">?</text></svg>')

CORACAO = ('<svg class="ic" viewBox="0 0 120 110"><path class="pulsa" d="M60 104L14 58C-4 38 12 8 36 12c11 2 18 9 24 18 '
           '6-9 13-16 24-18 24-4 40 26 22 46z" fill="#c9545f" stroke="#174a56" stroke-width="6"/></svg>')

CHECK = ('<svg class="caixa" viewBox="0 0 80 80"><rect x="6" y="6" width="68" height="68" rx="14" fill="#fff8e8" '
         'stroke="#174a56" stroke-width="6"/><path class="risco" d="M20 42l14 14 28-32" fill="none" stroke="#3f8a5b" '
         'stroke-width="10" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="80" '
         'stroke-dashoffset="80"/></svg>')

MAO = ('<svg viewBox="0 0 64 80"><path d="M22 6c4 0 7 3 7 7v24l4-2c4-1 7 1 8 4l2-1c4-1 7 1 8 4 4-1 7 2 7 6v14'
       'c0 12-9 22-21 22h-4c-8 0-14-4-18-11L5 52c-2-4 0-8 4-9 3-1 6 1 8 3l-2 0V13c0-4 3-7 7-7z" fill="#fff" '
       'stroke="#174a56" stroke-width="4" stroke-linejoin="round"/></svg>')


def _spans(palavras, pref, classe='w'):
    return ' '.join(f'<span id="{pref}{k}" class="{classe}">{e(w)}</span>' for k, w in enumerate(palavras))


def _linhas_html(linhas, pref, classe='w'):
    k = 0
    out = []
    for ln in linhas:
        out.append(' '.join(f'<span id="{pref}{k + j}" class="{classe}">{e(w)}</span>' for j, w in enumerate(ln)))
        k += len(ln)
    return '<br>'.join(out)


def compor(item, dados, pasta: Path):
    dur = validar(item, dados)
    fim_voz = float(dados['duracao_s'])
    segs = dados['segmentos']
    frases = dados['frases']
    palavras = dados.get('palavras') or []
    formato = item.get('formato')
    refs = [_versiculo(r) for r in item.get('referencias', [])]
    ref_txt = item['referencia_exibida']

    partes, anim, sons = [], [], []
    A = anim.append

    # ---------- câmera e luz de fundo ----------
    A('tl.fromTo("#cam",{scale:1.0,y:0},{scale:1.03,y:0,duration:%.3f,ease:"none"},0);' % CAPA)
    A('tl.fromTo("#sunglow",{opacity:.2,scale:.9},{opacity:.45,scale:1.08,duration:%.3f,ease:"sine.inOut",yoyo:true,repeat:%d},0);'
      % (3.2, max(1, int(dur / 3.2))))
    A('tl.fromTo("#raio",{opacity:.0,x:-60},{opacity:.4,x:40,duration:%.3f,ease:"sine.inOut",yoyo:true,repeat:%d},0);'
      % (4.5, max(1, int(dur / 4.5))))

    # poeira dourada / bokeh
    bokeh = ''
    for k in range(18):
        x = (k * 173) % 1000 + 40
        y = 600 + (k * 271) % 1100
        r = 8 + (k * 7) % 22
        bokeh += f'<i id="bk{k}" class="bokeh" style="left:{x}px;top:{y}px;width:{r}px;height:{r}px"></i>'
        sobe = 220 + (k * 37) % 260
        A(f'tl.fromTo("#bk{k}",{{y:0,x:0,opacity:0}},{{y:-{sobe},x:{(k % 5 - 2) * 24},opacity:{.35 + (k % 4) * .12:.2f},'
          f'duration:{dur / 2:.3f},ease:"sine.inOut",yoyo:true,repeat:1}},{(k * .37) % 2:.2f});')

    # ---------- capa central (miniatura da grade) ----------
    tam_t, lin_t = caber(item['titulo'].upper(), F_BOLD, 820, 300, 104, 54, 1.08)
    titulo_capa = '<br>'.join(' '.join(f'<span class="cw">{e(w)}</span>' for w in ln) for ln in lin_t)
    raios = ''.join(f'<i style="transform:rotate({a}deg)"></i>' for a in range(0, 360, 20))
    partes.append(
        f'<section id="capa" class="clip" data-start="0" data-duration="{CAPA + .45}" data-track-index="5">'
        f'<div id="burst">{raios}</div>'
        f'<div id="capa-card"><div class="fita"></div><div id="capa-ref">{e(ref_txt.upper())}</div>'
        f'<h1 id="capa-tit" style="font-size:{tam_t}px">{titulo_capa}</h1>'
        f'<div id="capa-risco"></div><div id="capa-sub">UM PROVÉRBIO · UMA DECISÃO MELHOR</div></div></section>')
    A('tl.fromTo("#burst",{rotation:0,scale:.6,opacity:0},{rotation:40,scale:1.15,opacity:1,duration:%.2f,ease:"power1.out"},0);' % (CAPA + .4))
    A('tl.fromTo("#capa-card",{scale:.55,rotation:-6,opacity:0},{scale:1,rotation:-1.5,opacity:1,duration:.55,ease:"back.out(1.6)"},0.05);')
    A('tl.fromTo("#capa-ref",{y:-30,opacity:0},{y:0,opacity:1,duration:.4,ease:"power2.out"},0.35);')
    A('tl.fromTo("#capa-tit .cw",{y:60,opacity:0,rotation:4},{y:0,opacity:1,rotation:0,duration:.45,stagger:.07,ease:"back.out(1.7)"},0.5);')
    A('tl.fromTo("#capa-risco",{scaleX:0},{scaleX:1,duration:.5,ease:"power2.out"},1.0);')
    A('tl.fromTo("#capa-sub",{opacity:0,y:16},{opacity:1,y:0,duration:.4},1.2);')
    A('tl.to("#capa-card",{y:-520,scale:.45,opacity:0,duration:.45,ease:"power2.in"},%.2f);' % CAPA)
    A('tl.to("#burst",{opacity:0,scale:1.6,duration:.45,ease:"power1.in"},%.2f);' % CAPA)
    sons += [('whoosh-cinematic', 0.0, .22), ('pop', .1, .35), ('chime', 1.0, .18)]

    # ---------- cartões por momento ----------
    for i, s in enumerate(segs):
        papel = s['papel']
        a = max(float(s['inicio']), CAPA if i == 0 else float(s['inicio']))
        z = float(segs[i + 1]['inicio']) if i + 1 < len(segs) else dur
        d = z - a
        leitura = papel in ('passagem', 'reflexao', 'aplicacao') and formato == 'D' or papel == 'passagem'
        rot = ROTULOS.get(papel, '')
        corpo_txt = item['texto_biblico'] if papel == 'passagem' else str(item.get(papel, '')).strip()
        if formato == 'D' and papel in ('reflexao', 'aplicacao'):
            corpo_txt = item[papel]
        ws = corpo_txt.split()
        tempos = tempos_das_palavras(corpo_txt, palavras, float(s['inicio']), float(s['fim']))
        selo = ''
        if leitura:
            k_ref = {'passagem': 0, 'reflexao': 1, 'aplicacao': 2}.get(papel, 0)
            r = refs[k_ref] if k_ref < len(refs) and refs[k_ref] else None
            selo_txt = (f'{r[0]}:{r[1]}' if r else ref_txt.split()[-1])
            topo = ref_txt.upper() if formato != 'D' else f'PROVÉRBIOS {r[0]} · VERSÍCULO {r[1]}' if r else ref_txt.upper()
            rot = ROTULOS['passagem']
            tam, ls = caber(corpo_txt, F_LORA, 770, 300, 58, 30, 1.25)
            corpo = (f'<div class="perg"><div class="perg-topo">{e(topo)}</div>'
                     f'<div class="verso" style="font-size:{tam}px">“{_linhas_html(ls, f"v{i}_", "w lw")}”</div>'
                     f'<div class="selo" id="selo{i}"><span>{e(selo_txt)}</span></div></div>')
            tipo = 'pergaminho'
        else:
            if papel == 'gancho':
                tam, ls = caber(corpo_txt, F_BOLD, 640, 250, 56, 30)
                corpo = f'<div class="lado">{PERGUNTA}<div class="txt" style="font-size:{tam}px">{_linhas_html(ls, f"v{i}_")}</div></div>'
                rot = item['titulo'].upper()
            elif papel == 'reflexao':
                tam, ls = caber(corpo_txt, F_BOLD, 640, 270, 52, 28)
                corpo = f'<div class="lado">{LAMPADA}<div class="txt" style="font-size:{tam}px">{_linhas_html(ls, f"v{i}_")}</div></div>'
            elif papel == 'aplicacao':
                tam, ls = caber(corpo_txt, F_BOLD, 660, 270, 50, 28)
                corpo = f'<div class="lado">{CHECK}<div class="txt" style="font-size:{tam}px">{_linhas_html(ls, f"v{i}_")}</div></div>'
            else:  # cta
                if formato == 'D':
                    rot = 'LEIA O CAPÍTULO'
                tam, ls = caber(corpo_txt, F_BOLD, 640, 170, 48, 28)
                chips = ''.join(f'<b class="chip" id="chip{i}_{k}">{t}</b>' for k, t in
                                enumerate(['♡ SALVE', '➤ ENVIE', '+ SIGA']))
                corpo = (f'<div class="lado">{CORACAO}<div class="txt" style="font-size:{tam}px">{_linhas_html(ls, f"v{i}_")}</div></div>'
                         f'<div class="chips">{chips}</div>')
            tipo = papel
        partes.append(
            f'<section id="p{i}" class="clip painel" data-start="{a:.3f}" data-duration="{d:.3f}" data-track-index="2">'
            f'<div id="c{i}" class="card {tipo}"><div class="fita"></div>'
            f'<div class="rotulo"><i></i>{e(rot)}</div>{corpo}<div class="barra" id="bar{i}"></div></div></section>')

        # entrada / transição
        tr = TRANSICOES[(i - 1) % len(TRANSICOES)] if i else 'capa'
        if tr == 'capa':
            A(f'tl.fromTo("#c{i}",{{y:420,scale:.55,opacity:0}},{{y:0,scale:1,opacity:1,duration:.55,ease:"back.out(1.3)"}},{a:.3f});')
        elif tr == 'folha':
            A(f'tl.fromTo("#c{i}",{{rotationY:-100,transformPerspective:1400,transformOrigin:"0% 50%",opacity:.3}},'
              f'{{rotationY:0,opacity:1,duration:.6,ease:"power3.out"}},{a:.3f});')
            sons.append(('whoosh-short', a - .05, .3))
        elif tr == 'faixa':
            A(f'tl.fromTo("#faixa",{{x:"-130%"}},{{x:"130%",duration:.6,ease:"power2.inOut"}},{a - .3:.3f});')
            A(f'tl.fromTo("#c{i}",{{x:700,rotation:4,opacity:0}},{{x:0,rotation:0,opacity:1,duration:.5,ease:"power3.out"}},{a:.3f});')
            sons.append(('whoosh-short', a - .3, .32))
        elif tr == 'clarao':
            A(f'tl.fromTo("#clarao",{{opacity:0}},{{opacity:.75,duration:.16,yoyo:true,repeat:1,ease:"power1.out"}},{a - .12:.3f});')
            A(f'tl.fromTo("#c{i}",{{scale:1.25,opacity:0,filter:"blur(12px)"}},{{scale:1,opacity:1,filter:"blur(0px)",duration:.5,ease:"power2.out"}},{a:.3f});')
            sons.append(('whoosh-cinematic', a - .25, .16))
        else:  # círculo
            A(f'tl.fromTo("#c{i}",{{clipPath:"circle(0% at 50% 50%)"}},{{clipPath:"circle(85% at 50% 50%)",duration:.6,ease:"power2.out"}},{a:.3f});')
            sons.append(('pop', a, .32))
        # saída suave antes do próximo
        if i + 1 < len(segs):
            A(f'tl.to("#c{i}",{{y:-30,opacity:0,scale:.96,duration:.25,ease:"power1.in"}},{z - .25:.3f});')
        else:
            A(f'tl.to("#c{i}",{{y:-60,opacity:0,duration:.35,ease:"power1.in"}},{fim_voz:.3f});')

        # rótulo e barra
        A(f'tl.fromTo("#c{i} .rotulo",{{x:-40,opacity:0}},{{x:0,opacity:1,duration:.4,ease:"power2.out"}},{a + .15:.3f});')
        A(f'tl.fromTo("#bar{i}",{{scaleX:0}},{{scaleX:1,duration:{max(.3, float(s["fim"]) - a):.3f},ease:"none"}},{a:.3f});')

        # palavras acendendo no tempo da fala
        for k, (w0, w1) in enumerate(tempos):
            if k >= len(ws):
                break
            t0 = max(w0, a + .05)
            if leitura:
                A(f'tl.fromTo("#v{i}_{k}",{{opacity:.18,y:6}},{{opacity:1,y:0,duration:.22,ease:"power1.out"}},{t0:.3f});')
            else:
                A(f'tl.fromTo("#v{i}_{k}",{{opacity:.28}},{{opacity:1,duration:.18}},{t0:.3f});')

        # efeitos próprios de cada cartão
        if leitura:
            ts = a + .5
            A(f'tl.fromTo("#selo{i}",{{scale:2.6,rotation:-30,opacity:0}},{{scale:1,rotation:-12,opacity:1,duration:.32,ease:"back.out(2.2)"}},{ts:.3f});')
            A(f'tl.fromTo("#cam",{{x:0}},{{x:6,duration:.05,yoyo:true,repeat:3}},{ts + .3:.3f});')
            sons.append(('chime', ts + .2, .2))
        elif papel == 'reflexao':
            A(f'tl.fromTo("#c{i} .glow",{{opacity:.15,scale:.7,transformOrigin:"50% 50%"}},{{opacity:.75,scale:1.15,duration:.8,yoyo:true,repeat:{max(1, int(d / .8))}}},{a + .3:.3f});')
        elif papel == 'aplicacao':
            A(f'tl.to("#c{i} .risco",{{strokeDashoffset:0,duration:.5,ease:"power2.out"}},{max(a + .6, float(s["fim"]) - 1.2):.3f});')
            sons.append(('pop', max(a + .6, float(s['fim']) - 1.2), .3))
        elif papel == 'gancho':
            A(f'tl.fromTo("#c{i} .ic",{{rotation:-15,scale:.6}},{{rotation:8,scale:1,duration:.5,ease:"back.out(2)"}},{a + .1:.3f});')
            A(f'tl.to("#c{i} .ic",{{rotation:-6,duration:.9,yoyo:true,repeat:{max(1, int(d / .9))},ease:"sine.inOut"}},{a + .6:.3f});')
        elif papel == 'cta':
            A(f'tl.fromTo("#c{i} .pulsa",{{scale:1,transformOrigin:"50% 50%"}},{{scale:1.14,duration:.35,yoyo:true,repeat:{max(1, int(d / .35))},ease:"sine.inOut"}},{a:.3f});')
            for k in range(3):
                tk = a + .5 + k * .35
                A(f'tl.fromTo("#chip{i}_{k}",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:.35,ease:"back.out(2.4)"}},{tk:.3f});')
                sons.append(('pop', tk, .22))

        # câmera por momento
        esc, dy = CAMERA.get(papel, (1.05, 0))
        A(f'tl.to("#cam",{{scale:{esc},y:{dy},duration:.9,ease:"power2.inOut"}},{a:.3f});')
        A(f'tl.to("#cam",{{scale:{esc + .02},duration:{max(.2, d - 1.0):.3f},ease:"none"}},{a + .9:.3f});')

    # ---------- legendas karaokê ----------
    for n, f in enumerate(frases):
        fa, fz = float(f['inicio']), float(f['fim'])
        if fz <= CAPA:
            continue
        ws = f['texto'].split()
        tempos = tempos_das_palavras(f['texto'], palavras, fa, fz)
        grupos, g = [], []
        fonte = ImageFont.truetype(str(F_BOLD), 50)
        for k, w in enumerate(ws):
            if g and fonte.getlength(' '.join([ws[j] for j in g] + [w])) > 880:
                grupos.append(g)
                g = []
            g.append(k)
            if len(g) >= 5 and w[-1] in ',;:.!?':
                grupos.append(g)
                g = []
        if g:
            grupos.append(g)
        for m, g in enumerate(grupos):
            g0 = max(CAPA, tempos[g[0]][0] - .05 if m else fa)
            g1 = tempos[grupos[m + 1][0]][0] - .05 if m + 1 < len(grupos) else fz
            if g1 <= g0 + .05:
                continue
            spans = ' '.join(f'<span id="k{n}_{k}">{e(ws[k])}</span>' for k in g)
            partes.append(f'<div id="cap{n}_{m}" class="clip legenda" data-start="{g0:.3f}" data-duration="{g1 - g0:.3f}" '
                          f'data-track-index="3"><div class="pal">{spans}</div></div>')
            A(f'tl.fromTo("#cap{n}_{m} .pal",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.2,ease:"power2.out"}},{g0:.3f});')
            for k in g:
                w0, w1 = tempos[k]
                w0 = max(w0, g0)
                A(f'tl.fromTo("#k{n}_{k}",{{color:"#ffffff",scale:1}},{{color:"#f4c55b",scale:1.05,duration:.1,ease:"power2.out"}},{w0:.3f});')
                A(f'tl.to("#k{n}_{k}",{{scale:1,duration:.15}},{max(w0 + .1, w1):.3f});')

    # ---------- encerramento ----------
    estrelas = ''
    for k in range(26):
        x = 540 + 30 * math.cos(k)
        cor = ['#f4c55b', '#fff4d6', '#3f8a5b', '#c9545f'][k % 4]
        estrelas += f'<i id="st{k}" class="estrela" style="left:{x:.0f}px;background:{cor}"></i>'
        ang = k * 2 * math.pi / 26
        A(f'tl.fromTo("#st{k}",{{x:0,y:0,opacity:1,scale:1,rotation:0}},{{x:{math.cos(ang) * (260 + k % 5 * 40):.0f},'
          f'y:{math.sin(ang) * (260 + k % 3 * 50) + 120:.0f},rotation:{k * 47},scale:.4,opacity:0,duration:1.4,ease:"power2.out"}},'
          f'{fim_voz + .55 + (k % 3) * .04:.3f});')
    partes.append(
        f'<section id="fim" class="clip" data-start="{fim_voz:.3f}" data-duration="{dur - fim_voz:.3f}" data-track-index="5">'
        f'<div id="fim-card"><div class="sol">{SOL_SVG}</div><div class="fim-a">SIGA</div><div class="fim-b">@sabioefeliz</div>'
        f'<div class="fim-c">Um provérbio por dia, toda manhã.</div><div id="seguir">Seguir</div>'
        f'<div id="mao">{MAO}</div></div>{estrelas}</section>')
    A(f'tl.fromTo("#fim-card",{{y:300,scale:.7,opacity:0}},{{y:0,scale:1,opacity:1,duration:.5,ease:"back.out(1.5)"}},{fim_voz:.3f});')
    A(f'tl.fromTo("#fim .sol",{{rotation:-90,scale:.3}},{{rotation:0,scale:1,duration:.7,ease:"back.out(2)"}},{fim_voz + .1:.3f});')
    A(f'tl.to("#fim .sol",{{rotation:60,duration:{dur - fim_voz:.3f},ease:"none"}},{fim_voz + .8:.3f});')
    A(f'tl.fromTo("#mao",{{x:220,y:200,opacity:0}},{{x:0,y:0,opacity:1,duration:.45,ease:"power2.out"}},{fim_voz + .7:.3f});')
    A(f'tl.to("#mao",{{scale:.85,duration:.1,yoyo:true,repeat:1}},{fim_voz + 1.2:.3f});')
    A(f'tl.to("#seguir",{{scale:.92,backgroundColor:"#3f8a5b",duration:.1,yoyo:true,repeat:1}},{fim_voz + 1.2:.3f});')
    A(f'tl.set("#seguir",{{backgroundColor:"#3f8a5b"}},{fim_voz + 1.42:.3f});')
    A(f'tl.to("#cam",{{scale:1.0,y:0,duration:.6}},{fim_voz:.3f});')
    sons += [('sparkle', fim_voz + .45, .3), ('click-soft', fim_voz + 1.2, .6), ('chime', fim_voz + 1.3, .15)]

    # progresso
    A(f'tl.fromTo("#prog",{{scaleX:0}},{{scaleX:1,duration:{dur:.3f},ease:"none"}},0);')
    A(f'tl.fromTo("#progsol",{{x:0,rotation:0}},{{x:928,rotation:360,duration:{dur:.3f},ease:"none"}},0);')

    doc = f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="composition.css"></head><body>
<div id="root" data-composition-id="sabio-hf2" data-width="1080" data-height="1920" data-duration="{dur}" data-fps="{FPS}">
<div id="cam"><video id="base" class="clip" src="assets/base.mp4" data-start="0" data-duration="{dur}" data-track-index="0" muted playsinline></video></div>
<div id="sunglow"></div><div id="raio"></div>{bokeh}<div class="wash"></div>
<header><div class="brand"><span class="mini">{SOL_SVG}</span>SÁBIO E FELIZ</div><div class="tag">{e(ref_txt.upper())}</div></header>
{''.join(partes)}
<footer><span>Um provérbio. Uma decisão melhor.</span><small>@sabioefeliz</small></footer>
<div id="trilho"><div id="prog"></div><div id="progsol">{SOL_SVG}</div></div>
<div id="grain"></div><div id="faixa"></div><div id="clarao"></div>
<audio id="voice" src="assets/mix.wav" data-start="0" data-duration="{dur}" data-track-index="4"></audio>
<script src="assets/gsap.min.js"></script><script>const tl=gsap.timeline({{paused:true}});{''.join(anim)}
window.__timelines=window.__timelines||{{}};window.__timelines['sabio-hf2']=tl;</script></div></body></html>'''
    (pasta / 'index.html').write_text(doc, encoding='utf-8')
    return dur, sons


# ---------------------------------------------------------------------
#  trilha e efeitos
# ---------------------------------------------------------------------
SR = 48000


def _ler(arquivo):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(arquivo), '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'])
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def _nota(f, dur, amp, ataque=.01, decai=2.0):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / ataque) * np.exp(-t * decai)
    onda = np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t) + .08 * np.sin(6 * np.pi * f * t)
    return amp * env * onda


def _passarinho(amp, semente):
    rng = np.random.default_rng(semente)
    out = []
    for _ in range(int(rng.integers(2, 4))):
        d = rng.uniform(.06, .11)
        t = np.arange(int(d * SR)) / SR
        f0, f1 = rng.uniform(2800, 3600), rng.uniform(4200, 5200)
        fase = 2 * np.pi * np.cumsum(np.linspace(f0, f1, len(t))) / SR
        out.append(amp * np.sin(fase) * np.sin(np.pi * t / d) ** 2)
        out.append(np.zeros(int(rng.uniform(.03, .07) * SR)))
    return np.concatenate(out)


def mixar(voz_wav: Path, dur: float, sons, destino: Path):
    n = int(math.ceil(dur * SR))
    trilha = np.zeros(n)
    sfx = np.zeros(n)

    def add(buf, t, sinal):
        i = int(max(0, t) * SR)
        k = min(len(sinal), n - i)
        if k > 0:
            buf[i:i + k] += sinal[:k]

    # acordes suaves (I–V–vi–IV em Dó), 2,4 s cada, + caixinha de música
    prog = [(261.63, 329.63, 392.0), (196.0, 246.94, 392.0), (220.0, 261.63, 329.63), (174.61, 220.0, 349.23)]
    mel = [784, 659, 698, 587, 659, 523, 587, 494, 523, 659, 587, 523]
    for k, t0 in enumerate(np.arange(0, dur, 2.4)):
        for f in prog[k % 4]:
            add(trilha, t0, _nota(f, 3.0, .010, ataque=.5, decai=.9))
            add(trilha, t0, _nota(f / 2, 3.0, .006, ataque=.6, decai=.8))
        for j in range(4):
            add(trilha, t0 + j * .6, _nota(mel[(k * 4 + j) % len(mel)] * (1 if j % 2 == 0 else 1), .9, .0075, decai=5))
    # passarinhos na abertura e de vez em quando
    for k, t0 in enumerate([.15, .7, 1.4, 9.0, 17.5]):
        if t0 < dur:
            add(trilha, t0, _passarinho(.012, 7 + k))

    # efeitos
    for nome, t, vol in sons:
        try:
            arq = achar(f'{nome}.mp3', 'assets/sfx')
        except FileNotFoundError:
            arq = None
        if arq:
            add(sfx, t, _ler(arq) * vol)

    voz = _ler(voz_wav)
    voz = np.pad(voz, (0, max(0, n - len(voz))))[:n]
    # abafar a trilha embaixo da voz (sidechain simples, envelope de 120 ms)
    janela = int(.12 * SR)
    energia = np.sqrt(np.convolve(voz ** 2, np.ones(janela) / janela, mode='same'))
    duck = 1 - .55 * np.clip(energia / (energia.max() or 1) * 4, 0, 1)
    duck = np.convolve(duck, np.ones(janela) / janela, mode='same')
    fade = np.minimum(1, np.arange(n) / (SR * .4)) * np.minimum(1, (n - np.arange(n)) / (SR * 1.0))
    mix = voz + trilha * duck * fade * 1.4 + sfx
    pico = np.max(np.abs(mix)) or 1
    if pico > .97:
        mix = mix / pico * .97
    import soundfile as sf
    sf.write(str(destino), mix.astype(np.float32), SR)
