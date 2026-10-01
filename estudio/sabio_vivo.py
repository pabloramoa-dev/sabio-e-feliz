"""Sábio vivo — camada Manim da versão HyperFrames v2 (01/10/2026).

O desenho do Sábio continua o MESMO (ranzinza do previsao_lib + rosto
sábio e feliz da cena.py). O que muda aqui é que ele deixa de ser um boneco
parado que só mexe a boca:

* expressão por momento do roteiro (curioso, lendo, pensativo, ensinando, feliz);
* cabeça que acompanha a fala (aceno nas sílabas fortes) e inclina de lado;
* olhos que piscam, olham para o livro, para cima e para quem assiste;
* braços com gesto: mão no queixo, livro aberto nas mãos, dedo erguido,
  palmas abertas e tchau no final.

E o cenário vira uma manhã de verdade: janela em arco com céu de nascer do
sol, sol com halo, nuvens andando, passarinhos, morros, cortinas verdes, raios de
luz com poeira dourada, planta pendurada que balança, mesa
de madeira com Bíblia aberta, caneca com vapor e vasinho.

Tudo é determinístico (sem aleatório): o mesmo roteiro gera o mesmo vídeo.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

from manim import *
import numpy as np

config.frame_width = 8
config.frame_height = 128 / 9
config.pixel_width = int(os.environ.get('SABIO_BASE_WIDTH', '720'))
config.pixel_height = round(config.pixel_width * 16 / 9)
config.frame_rate = 30

from estudio import previsao_lib as P   # noqa: E402
from estudio.cena import rosto_sabio    # noqa: E402

PT = P.PT
DOURADO = "#d6a84a"
CREME = "#f7ecd6"
AZUL = "#174a56"

ESCALA = 1.95                 # tamanho do Sábio
CABECA_Y = 0.55               # centro da cabeça na tela (unidades Manim)
MESA_Y = -3.35                # tampo da mesa


def suave(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return a + (b - a) * k


# =====================================================================
#  CENÁRIO
# =====================================================================
def _gradiente(w, h, cores, centro, direcao=UP):
    r = Rectangle(width=w, height=h, stroke_width=0).move_to(centro)
    r.set_fill(color=cores, opacity=1)
    r.set_sheen_direction(direcao)
    return r


def _nuvem(escala=1.0, cor="#fffaf0"):
    partes = [(0, 0, .42), (.42, .08, .34), (-.42, .02, .32), (.18, .3, .3), (-.2, .26, .28)]
    n = VGroup(*[Circle(radius=r, fill_color=cor, fill_opacity=.95, stroke_width=0).move_to([x, y, 0])
                 for x, y, r in partes])
    base = RoundedRectangle(width=1.5, height=.38, corner_radius=.19, fill_color=cor,
                            fill_opacity=.95, stroke_width=0).move_to([0, -.16, 0])
    return VGroup(n, base).scale(escala)


def _passaro():
    asaE = ArcBetweenPoints(LEFT * .2, ORIGIN, angle=-PI / 2.4).set_stroke("#3a3442", 5)
    asaD = ArcBetweenPoints(ORIGIN, RIGHT * .2, angle=-PI / 2.4).set_stroke("#3a3442", 5)
    return VGroup(asaE, asaD)


def _livro_estante(x, y, w, h, cor):
    lomb = Rectangle(width=w, height=h, fill_color=cor, fill_opacity=1, stroke_color=PT, stroke_width=4)
    faixa = Line(LEFT * w * .35, RIGHT * w * .35, stroke_color=DOURADO, stroke_width=4).shift(UP * h * .28)
    return VGroup(lomb, faixa).move_to([x, y + h / 2, 0])


def montar_cenario(scene, dur):
    W, H = config.frame_width, config.frame_height
    t0 = {'t': 0.0}

    def relogio(m, dt):
        t0['t'] += dt
    clock = Dot(fill_opacity=0, stroke_width=0)
    clock.add_updater(relogio)
    scene.add(clock)
    T = lambda: t0['t']  # noqa: E731

    # ---- parede com papel de parede listrado suave ----
    parede = _gradiente(W * 1.3, H * 1.3, ["#f3d9b5", "#e8c095"], ORIGIN)
    listras = VGroup(*[Rectangle(width=.22, height=H * 1.3, fill_color="#ffffff", fill_opacity=.07,
                                 stroke_width=0).move_to([x, 0, 0])
                       for x in np.arange(-W * .65, W * .65, .62)])
    rodape = Rectangle(width=W * 1.3, height=.18, fill_color="#c79b6c", fill_opacity=1,
                       stroke_width=0).move_to([0, MESA_Y + .9, 0])
    scene.add(parede)

    # ---- janela em arco, grande, atrás do Sábio ----
    jw, jy0, jy1 = 5.0, MESA_Y + .2, 4.6
    jh = jy1 - jy0
    def arco(w, h, y0):
        caixa = Rectangle(width=w, height=h - w / 2).move_to([0, y0 + (h - w / 2) / 2, 0])
        topo = Arc(radius=w / 2, start_angle=0, angle=PI).move_to([0, y0 + h - w / 4, 0])
        forma = Union(caixa, Circle(radius=w / 2).move_to([0, y0 + h - w / 2, 0]))
        return forma
    vidro = arco(jw, jh, jy0)
    moldura = Difference(arco(jw + .5, jh + .25, jy0 - .05), vidro).set_fill("#c9925f", 1).set_stroke(PT, 10)
    ceu = _gradiente(jw + .2, jh + .2, ["#ffd7a0", "#ffc6a6", "#a9d4e4", "#86c0dc"], [0, jy0 + jh / 2, 0])

    # tudo que fica "lá fora" é recortado pelo vidro
    fora = VGroup()
    fora.add(ceu)
    # sol nascendo, com halo pulsando
    sol_c = np.array([1.15, jy0 + 2.35, 0])
    halos = VGroup(*[Circle(radius=r, fill_color="#fff1c2", fill_opacity=o, stroke_width=0).move_to(sol_c)
                     for r, o in ((1.55, .16), (1.15, .24), (.85, .38))])
    sol = Circle(radius=.62, fill_color="#ffe08a", fill_opacity=1, stroke_color="#f6b94a",
                 stroke_width=6).move_to(sol_c)
    fora.add(halos, sol)

    # nuvens andando devagar
    nuvens = []
    for k, (y, esc, vel, x0) in enumerate(((jy0 + 4.0, .9, .10, -1.6), (jy0 + 3.2, .65, .16, 1.9),
                                           (jy0 + 4.6, .55, .07, .4))):
        n = _nuvem(esc).move_to([x0, y, 0])
        nuvens.append((n, vel, x0, y))
        fora.add(n)

    # morros e arvorezinhas no horizonte
    morro1 = Ellipse(width=6.5, height=2.2, fill_color="#9cc59a", fill_opacity=1, stroke_width=0).move_to([-1.4, jy0 + .25, 0])
    morro2 = Ellipse(width=6.0, height=1.8, fill_color="#7fb184", fill_opacity=1, stroke_width=0).move_to([2.0, jy0 + .05, 0])
    arvores = VGroup(*[VGroup(Rectangle(width=.06, height=.28, fill_color="#6b4a2f", fill_opacity=1, stroke_width=0),
                              Circle(radius=.2, fill_color="#5e9a6a", fill_opacity=1, stroke_width=0).shift(UP * .24))
                       .move_to([x, jy0 + .78 + .1 * math.sin(x * 3), 0]) for x in (-2.0, -1.5, 1.4, 1.85)])
    fora.add(morro1, morro2, arvores)

    passaros = []
    for k in range(3):
        b = _passaro().scale(.9 - k * .15)
        passaros.append(b)
        fora.add(b)

    # ---- animação do lado de fora ----
    def _ceu(m, dt):
        t = T()
        sobe = .35 * suave(t / max(dur, 1))
        s = 1 + .05 * math.sin(t * 1.6)
        for i, h in enumerate(halos):
            h.move_to(sol_c + UP * sobe)
            h.set_fill(opacity=[.16, .24, .38][i] * (0.85 + .25 * math.sin(t * 1.3 + i)))
        sol.move_to(sol_c + UP * sobe)
        for n, vel, x0, y in nuvens:
            x = ((x0 + vel * t + 3.6) % 7.2) - 3.6
            n.move_to([x, y + .04 * math.sin(t * .7 + x0), 0])
        for k, b in enumerate(passaros):
            ciclo = 9.0
            f = ((t + k * .7) % ciclo) / ciclo
            x = -3.2 + 6.4 * f
            y = jy0 + 3.0 + k * .32 + .25 * math.sin(f * PI * 2)
            bat = math.sin(t * 11 + k)
            b.become(VGroup(
                ArcBetweenPoints(LEFT * .2, ORIGIN, angle=-PI / 2.4 * bat).set_stroke("#3a3442", 5),
                ArcBetweenPoints(ORIGIN, RIGHT * .2, angle=-PI / 2.4 * bat).set_stroke("#3a3442", 5),
            ).scale(.9 - k * .15).move_to([x, y, 0]).set_opacity(1 if .04 < f < .96 else 0))
    fora.add_updater(_ceu)

    # recorte: tudo que sobra para fora do vidro é coberto pela parede
    # (Manim não tem máscara; a parede em volta é desenhada por cima)
    scene.add(fora)
    mascara = Difference(Rectangle(width=W * 1.3, height=H * 1.3), vidro)
    mascara.set_fill(["#f3d9b5", "#e8c095"], 1).set_stroke(width=0)
    mascara.set_sheen_direction(UP)
    listras2 = listras.copy()
    scene.add(mascara)
    # reaplica a textura da parede só fora do vidro (listras finas ficam por baixo do vidro? não: por cima da máscara)
    scene.add(listras2)
    scene.add(moldura)
    vidro_brilho = VGroup(
        Line([-1.8, jy0 + 1.0, 0], [-1.0, jy0 + 2.2, 0], stroke_color=WHITE, stroke_width=10, stroke_opacity=.35),
        Line([-1.5, jy0 + .8, 0], [-1.1, jy0 + 1.4, 0], stroke_color=WHITE, stroke_width=6, stroke_opacity=.3))
    caixilho = VGroup(
        Line([0, jy0, 0], [0, jy1 - .05, 0], stroke_color=PT, stroke_width=9),
        Line([-jw / 2, jy0 + 2.1, 0], [jw / 2, jy0 + 2.1, 0], stroke_color=PT, stroke_width=9))
    peitoril = RoundedRectangle(width=jw + 1.1, height=.28, corner_radius=.08, fill_color="#b88152",
                                fill_opacity=1, stroke_color=PT, stroke_width=7).move_to([0, jy0 - .05, 0])
    scene.add(vidro_brilho, caixilho, peitoril, rodape)

    # cortinas que balançam com a brisa
    def cortina(lado):
        x = lado * (jw / 2 + .15)
        pts = []
        return x
    cortE = VMobject(); cortD = VMobject()
    for c in (cortE, cortD):
        c.set_fill(["#7fb3a6", "#4f8578"], 1).set_stroke(PT, 7); c.set_sheen_direction(RIGHT)
    def _cortina(m, lado):
        t = T()
        x_in = lado * (jw / 2 + .05)
        x_out = lado * (W / 2 + .2)
        top = jy1 + 1.2
        bot = jy0 + .1
        onda = .10 * math.sin(t * 1.2 + lado)
        interno = []
        for k in range(25):
            y = top - (top - bot) * k / 24
            amarra = 1 - .5 * math.exp(-((y - (jy0 + 1.5)) ** 2) / .35)
            xi = lerp(x_out, x_in, amarra) + lado * onda * (k / 24) ** 2
            interno.append(np.array([xi, y, 0]))
        pts = [np.array([x_out, top, 0])] + interno + [np.array([x_out, bot, 0]), np.array([x_out, top, 0])]
        m.set_points_as_corners(pts)
    cortE.add_updater(lambda m, dt: _cortina(m, -1))
    cortD.add_updater(lambda m, dt: _cortina(m, 1))
    _cortina(cortE, -1); _cortina(cortD, 1)
    varao = Line([-W / 2 - .2, jy1 + 1.2, 0], [W / 2 + .2, jy1 + 1.2, 0], stroke_color="#7a5230", stroke_width=12)
    scene.add(cortE, cortD, varao)

    # planta pendurada que balança: corda, vaso de barro e ramos caindo
    gancho_p = np.array([-1.75, jy1 + 1.15, 0])
    vaso_c = gancho_p + DOWN * 1.55
    cordas = VGroup(*[Line(gancho_p, vaso_c + np.array([dx, .18, 0]), stroke_color="#7a5230", stroke_width=3)
                      for dx in (-.3, 0, .3)])
    vaso_p = Polygon(vaso_c + np.array([-.36, .2, 0]), vaso_c + np.array([.36, .2, 0]),
                     vaso_c + np.array([.26, -.28, 0]), vaso_c + np.array([-.26, -.28, 0]),
                     fill_color="#d78a5c", fill_opacity=1, stroke_color=PT, stroke_width=6)
    ramos = VGroup()
    for k, (dx, comp) in enumerate(((-.3, 1.4), (-.1, 1.0), (.12, 1.6), (.3, 1.15))):
        ini = vaso_c + np.array([dx, .15, 0])
        fim = ini + np.array([dx * .8, -comp, 0])
        ramo = ArcBetweenPoints(ini, fim, angle=.5 if dx < 0 else -.5).set_stroke("#4f8a5e", 6)
        ramos.add(ramo)
        for f in (.35, .6, .85):
            pt = ramo.point_from_proportion(f)
            ramos.add(Ellipse(width=.2, height=.12, fill_color="#6aa874", fill_opacity=1, stroke_color=PT,
                              stroke_width=3).rotate((-1) ** k * .6).move_to(pt + RIGHT * (-1) ** k * .07))
    copa = VGroup(*[Ellipse(width=.3, height=.18, fill_color="#5e9a6a", fill_opacity=1, stroke_color=PT,
                            stroke_width=3).rotate(a).move_to(vaso_c + np.array([x, .28, 0]))
                    for x, a in ((-.25, .5), (0, 0), (.25, -.5))])
    pendente = VGroup(cordas, ramos, vaso_p, copa)
    pend_ref = pendente.copy()
    def _pend(m, dt):
        m.become(pend_ref.copy().rotate(.07 * math.sin(T() * 1.1), about_point=gancho_p))
    pendente.add_updater(_pend)
    scene.add(pendente)

    # raios de sol entrando pela janela + poeira dourada
    raios = VGroup()
    for k in range(4):
        x = .3 + k * .75
        raio = Polygon([x, jy1 - .2, 0], [x + .45, jy1 - .2, 0], [x - 2.2, MESA_Y, 0], [x - 3.0, MESA_Y, 0],
                       fill_color="#fff3c4", fill_opacity=.0, stroke_width=0)
        raios.add(raio)
    def _raios(m, dt):
        t = T()
        for k, r in enumerate(m):
            r.set_fill(opacity=.07 + .05 * math.sin(t * .8 + k * 1.7))
    raios.add_updater(_raios)

    poeira = VGroup(*[Dot(radius=.025 + (k % 3) * .01, fill_color="#fff6d0", fill_opacity=.0) for k in range(22)])
    def _poeira(m, dt):
        t = T()
        for k, d in enumerate(m):
            fase = k * 2.399
            x = -2.4 + (k * .37) % 4.6 + .18 * math.sin(t * .5 + fase)
            y = MESA_Y + .6 + ((k * .53 + t * (.10 + .02 * (k % 4))) % 5.6)
            d.move_to([x, y, 0])
            d.set_fill(opacity=.55 * (.5 + .5 * math.sin(t * 1.4 + fase)))
    poeira.add_updater(_poeira)
    return raios, poeira, T


def montar_mesa(scene, T):
    W = config.frame_width
    tampo = RoundedRectangle(width=W * 1.25, height=.32, corner_radius=.06, fill_color="#a7744c", fill_opacity=1,
                             stroke_color=PT, stroke_width=9).move_to([0, MESA_Y, 0])
    frente = Rectangle(width=W * 1.25, height=5.0, fill_color="#83583a", fill_opacity=1, stroke_width=0
                       ).move_to([0, MESA_Y - 2.66, 0])
    veios = VGroup(*[ArcBetweenPoints([-W * .6, MESA_Y - .45 - k * .42, 0], [W * .6, MESA_Y - .5 - k * .42, 0],
                                      angle=.05 * (-1) ** k).set_stroke("#6f4a31", 4, opacity=.6) for k in range(6)])
    # Bíblia aberta à esquerda
    biblia = VGroup(
        Polygon([-.95, 0, 0], [0, -.12, 0], [0, .12, 0], [-.9, .26, 0], fill_color="#fbf3df", fill_opacity=1,
                stroke_color=PT, stroke_width=5),
        Polygon([.95, 0, 0], [0, -.12, 0], [0, .12, 0], [.9, .26, 0], fill_color="#fbf3df", fill_opacity=1,
                stroke_color=PT, stroke_width=5),
        Line([-.7, .1, 0], [-.15, .03, 0], stroke_color="#b9a37a", stroke_width=3),
        Line([.15, .03, 0], [.7, .1, 0], stroke_color="#b9a37a", stroke_width=3),
        Line([0, .12, 0], [.08, -.35, 0], stroke_color="#b83b3b", stroke_width=5),
    ).move_to([-2.45, MESA_Y + .3, 0])
    # caneca com vapor
    caneca = VGroup(
        RoundedRectangle(width=.62, height=.7, corner_radius=.1, fill_color=AZUL, fill_opacity=1,
                         stroke_color=PT, stroke_width=7),
        Arc(radius=.2, start_angle=-PI / 2, angle=PI, arc_center=RIGHT * .38).set_stroke(PT, 8),
        Line(LEFT * .18, RIGHT * .18, stroke_color=DOURADO, stroke_width=5),
    ).move_to([2.55, MESA_Y + .5, 0])
    vaso = VGroup(
        Polygon([-.3, 0, 0], [.3, 0, 0], [.22, -.42, 0], [-.22, -.42, 0], fill_color="#e7cfa9", fill_opacity=1,
                stroke_color=PT, stroke_width=6),
    ).move_to([3.45, MESA_Y + .37, 0])
    folhas = VGroup(*[Ellipse(width=.3, height=.62, fill_color="#5b9469", fill_opacity=1, stroke_color=PT,
                              stroke_width=5).rotate(a).move_to(vaso.get_top() + np.array([math.sin(a) * -.25, .3, 0]))
                      for a in (-.5, 0, .5)])
    base_folhas = folhas.copy()
    piv = vaso.get_top()
    def _folhas(m, dt):
        m.become(base_folhas.copy().rotate(.06 * math.sin(T() * 1.7), about_point=piv))
    folhas.add_updater(_folhas)

    vapor = VGroup(*[Arc(radius=.14, start_angle=PI * .15, angle=PI * .7) for _ in range(3)])
    topo = caneca.get_top()
    def _vapor(m, dt):
        t = T()
        for i, a in enumerate(m):
            f = ((t + i * .9) % 2.7) / 2.7
            a.move_to(topo + RIGHT * ((i - 1) * .14 + .06 * math.sin(t * 2 + i)) + UP * (.2 + f * 1.0))
            a.set_stroke(WHITE, 5, opacity=.6 * (1 - f) * min(1, f * 6))
    vapor.add_updater(_vapor)
    scene.add(frente, veios, tampo, biblia, caneca, vapor, vaso, folhas)


# =====================================================================
#  O SÁBIO VIVO
# =====================================================================
# pose = (mão esquerda local, mão direita local, dedo, livro, olhos, sobr., sorriso, olhar, inclinação)
# coordenadas locais: unidades do desenho original, origem no centro da cabeça
REPOUSO_E, REPOUSO_D = (-1.1, -1.92), (1.1, -1.92)
POSES = {
    'repouso':  dict(e=REPOUSO_E, d=REPOUSO_D, dedo=0, livro=0, feliz=0, sob=(0, 0), sorriso=.8, olhar=(0, 0), incl=0),
    'queixo':   dict(e=REPOUSO_E, d=(.42, -1.05), dedo=0, livro=0, feliz=0, sob=(.05, .22), sorriso=.45, olhar=(.06, .05), incl=-.06),
    'livro':    dict(e=(-.62, -1.35), d=(.62, -1.35), dedo=0, livro=1, feliz=0, sob=(.05, .05), sorriso=.7, olhar=(0, -.07), incl=.05),
    'dedo':     dict(e=REPOUSO_E, d=(1.45, -.05), dedo=1, livro=0, feliz=0, sob=(.16, .16), sorriso=.6, olhar=(.03, .03), incl=-.04),
    'palmas':   dict(e=(-1.5, -1.15), d=(1.5, -1.15), dedo=0, livro=0, feliz=.0, sob=(.1, .1), sorriso=1.0, olhar=(0, 0), incl=.03),
    'tchau':    dict(e=REPOUSO_E, d=(1.5, .35), dedo=0, livro=0, feliz=1, sob=(.12, .12), sorriso=1.25, olhar=(0, 0), incl=.07),
    'livro_alto': dict(e=(-.62, -1.05), d=(.62, -1.05), dedo=0, livro=1, feliz=1, sob=(.14, .14), sorriso=1.2, olhar=(0, 0), incl=.0),
}


def roteiro_de_poses(segmentos, formato):
    """Converte os segmentos falados em uma lista (inicio, fim, pose)."""
    mapa = {'gancho': 'queixo', 'passagem': 'livro', 'reflexao': 'dedo', 'aplicacao': 'palmas', 'cta': 'tchau'}
    if formato == 'D':
        mapa.update(reflexao='livro', aplicacao='livro', cta='livro_alto')
    saida = []
    for s in segmentos:
        saida.append((float(s['inicio']), float(s['fim']), mapa.get(s['papel'], 'repouso'), s['papel']))
    return saida


def _pose_no_tempo(t, plano):
    """Pose misturada: transição suave de 0,45 s entre um momento e outro."""
    atual, anterior, k = 'repouso', 'repouso', 1.0
    for i, (a, z, nome, _) in enumerate(plano):
        if t >= a - .15:
            anterior = atual
            atual = nome
            k = suave((t - (a - .15)) / .45)
    A, B = POSES[anterior], POSES[atual]
    mix = {}
    for chave in A:
        va, vb = A[chave], B[chave]
        if isinstance(va, tuple):
            mix[chave] = tuple(lerp(x, y, k) for x, y in zip(va, vb))
        else:
            mix[chave] = lerp(va, vb, k)
    mix['nome'] = atual
    return mix


def sabio_vivo(scene, job, T):
    env = job['envelope']
    fps = 30
    plano = roteiro_de_poses(job['segmentos'], job.get('formato'))

    dm = rosto_sabio(P.ranzinza('desconfiado'))
    G = dm['grupo']
    G.scale(ESCALA)
    G.shift(UP * (CABECA_Y - dm['cab'].get_center()[1]))
    s = ESCALA
    c0 = dm['cab'].get_center().copy()

    sub = list(G.submobjects)
    # índices do desenho original (ver previsao_lib.ranzinza)
    pesc, calca, pe, pd, chE, chD, camisa, trama, susp, gola, be, bd, beng, maoE, maoD = sub[:15]
    resto = sub[15:]                         # orelhas, tufos, cabeça, bochechas, fios, nariz, óculos, ...
    dinamicos = {id(dm[k]) for k in ('sobE', 'sobD', 'oe', 'od', 'boca')}
    cabeca = VGroup(*[m for m in resto if id(m) not in dinamicos])
    corpo = VGroup(pesc, calca, pe, pd, chE, chD, camisa, trama, susp, gola)
    corpo_ref, cabeca_ref = corpo.copy(), cabeca.copy()
    pesc_base = pesc.get_end().copy()
    quadril = c0 + DOWN * 3.3 * s

    L = lambda x, y: c0 + np.array([x * s, y * s, 0])  # noqa: E731

    sobE, sobD, olhoE, olhoD = VMobject(), VMobject(), VMobject(), VMobject()
    boca = VMobject()
    braçoE, braçoD = VMobject(), VMobject()
    maoE2, maoD2 = VMobject(), VMobject()
    dedo = VMobject()
    livro = VMobject()
    scene.add(corpo, cabeca, sobE, sobD, olhoE, olhoD, boca, livro, braçoE, braçoD, maoE2, maoD2, dedo)

    suav = {'env': 0.0}

    def frame(mo, dt):
        t = T()
        i = min(int(t * fps), len(env) - 1)
        a = env[i] if i >= 0 else 0.0
        suav['env'] = lerp(suav['env'], a, .35)
        e = suav['env']
        p = _pose_no_tempo(t, plano)

        # corpo: respiração + leve balanço
        resp = .045 * math.sin(t * 2 * PI / 3.2)
        balanco = .025 * math.sin(t * .9)
        corpo.become(corpo_ref.copy().rotate(balanco * .4, about_point=quadril).shift(UP * resp * .6))
        pesc_top = pesc_base + UP * resp * .6

        # cabeça: inclinação da pose + aceno na fala + olhar ao redor
        aceno = -.06 * e * s
        incl = p['incl'] + .045 * math.sin(t * .75) + .03 * math.sin(t * 2.3) * e
        desloc = UP * (resp + aceno) + RIGHT * balanco * .8
        piv = pesc_top
        def H(m):
            return m.rotate(incl, about_point=piv).shift(desloc)
        cabeca.become(H(cabeca_ref.copy()))

        # olhos: piscar, olhar, modo feliz (^ ^)
        ciclo = (t + .3) % 3.7
        pisc = 1.0 if ciclo > .14 else .12
        ox, oy = p['olhar']
        ox += .03 * math.sin(t * .6)
        for lado, olho in ((-1, olhoE), (1, olhoD)):
            centro = c0 + np.array([(lado * .32 + ox) * s, (.04 + oy) * s, 0])
            aberto = Ellipse(width=.2 * s, height=.2 * s * pisc, fill_color=PT, fill_opacity=1, stroke_width=0
                             ).move_to(centro)
            brilho = Dot(centro + np.array([.035 * s, .04 * s, 0]), radius=.025 * s, color=WHITE
                         ).set_opacity(1 if pisc > .5 else 0)
            fechado = ArcBetweenPoints(centro + LEFT * .12 * s, centro + RIGHT * .12 * s, angle=-PI / 1.6
                                       ).set_stroke(PT, 9)
            f = p['feliz']
            novo = VGroup(aberto.set_opacity(1 - f), brilho.set_opacity((1 - f) * (1 if pisc > .5 else 0)),
                          fechado.set_stroke(opacity=f))
            olho.become(H(novo))

        # sobrancelhas: sobem com a pose e com a ênfase da fala
        ergue = .07 * e
        for lado, sob, val in ((-1, sobE, p['sob'][0]), (1, sobD, p['sob'][1])):
            dy = (val + ergue) * s
            ini = c0 + np.array([lado * .54 * s, .30 * s + dy, 0])
            fim = c0 + np.array([lado * .14 * s, .40 * s + dy + val * .2 * s, 0])
            arco = ArcBetweenPoints(ini if lado < 0 else fim, fim if lado < 0 else ini, angle=-PI / 3.2
                                    ).set_stroke(P.GRIS, 13)
            sob.become(H(arco))

        # boca: sorriso + abertura pela amplitude
        sorr = p['sorriso']
        bc = c0 + DOWN * .62 * s
        if a < .12:
            nova = ArcBetweenPoints(bc + LEFT * .27 * s, bc + RIGHT * .27 * s, angle=PI / 2.7 * sorr
                                    ).set_stroke(PT, 9)
        else:
            nova = VGroup(
                Ellipse(width=(.36 + .1 * a) * s, height=(.1 + .32 * a) * s, fill_color="#5a2a28", fill_opacity=1,
                        stroke_color=PT, stroke_width=6).move_to(bc + DOWN * .03 * s),
                Ellipse(width=.18 * s, height=.07 * s * a, fill_color="#d9706a", fill_opacity=1, stroke_width=0
                        ).move_to(bc + DOWN * (.03 + .1 * a) * s),
            )
        boca.become(H(nova))

        # braços: ombro -> cotovelo (curva) -> mão
        ombE = corpo[0].get_end() + np.array([-.5 * s, -.25 * s, 0])
        ombD = corpo[0].get_end() + np.array([.5 * s, -.25 * s, 0])
        hx, hy = p['e']
        mE = L(hx, hy) + np.array([0, .03 * math.sin(t * 2.1) * s, 0])
        hx, hy = p['d']
        mD = L(hx, hy)
        nome = p['nome']
        if nome == 'tchau':
            mD = mD + np.array([.22 * s * math.sin(t * 7.0), .05 * s * abs(math.sin(t * 7.0)), 0])
        elif nome == 'dedo':
            mD = mD + np.array([0, .06 * s * math.sin(t * 3.0), 0])
        elif nome == 'palmas':
            abre = .18 * s * math.sin(t * 2.2)
            mE = mE + LEFT * abre
            mD = mD + RIGHT * abre
        elif nome == 'queixo':
            mD = mD + np.array([.03 * s * math.sin(t * 4), 0, 0])
        mE = mE + desloc * .5
        mD = mD + desloc * .5

        def braco(omb, mao, lado):
            meio = (omb + mao) / 2
            d = mao - omb
            perp = np.array([-d[1], d[0], 0])
            n = np.linalg.norm(perp) or 1
            cot = meio + perp / n * .32 * s * (-lado)
            if cot[1] > meio[1] + .2 and mao[1] < omb[1]:
                cot = meio + perp / n * .32 * s * lado
            v = VMobject().set_points_smoothly([omb, cot, mao]).set_stroke(PT, 15)
            return v
        braçoE.become(braco(ombE, mE, -1))
        braçoD.become(braco(ombD, mD, 1))
        maoE2.become(Circle(radius=.14 * s, fill_color=P.PELE, fill_opacity=1, stroke_color=PT, stroke_width=5
                            ).move_to(mE))
        maoD2.become(Circle(radius=.14 * s, fill_color=P.PELE, fill_opacity=1, stroke_color=PT, stroke_width=5
                            ).move_to(mD))
        d = p['dedo']
        dedo.become(RoundedRectangle(width=.1 * s, height=.32 * s, corner_radius=.05 * s, fill_color=P.PELE,
                                     fill_opacity=1, stroke_color=PT, stroke_width=4)
                    .move_to(mD + UP * .2 * s).rotate(-.15).set_opacity(d))

        # livro nas mãos (aparece/some com a pose; vira página a cada momento)
        lv = p['livro']
        meio = (mE + mD) / 2 + UP * .12 * s
        larg = max(.2, np.linalg.norm(mD - mE) / s * .62)
        virar = 0.0
        for a0, z0, nm, papel in plano:
            if nm.startswith('livro') and a0 <= t < a0 + .5:
                virar = math.sin(PI * (t - a0) / .5)
        capa = Polygon(L(0, 0) * 0 + meio + np.array([-larg * s, -.42 * s, 0]),
                       meio + np.array([larg * s, -.42 * s, 0]),
                       meio + np.array([larg * s * 1.04, .44 * s, 0]),
                       meio + np.array([-larg * s * 1.04, .44 * s, 0]),
                       fill_color="#7a2f2a", fill_opacity=1, stroke_color=PT, stroke_width=6)
        pagE = Polygon(meio + np.array([-larg * .94 * s, -.36 * s, 0]), meio + np.array([0, -.4 * s, 0]),
                       meio + np.array([0, .38 * s, 0]), meio + np.array([-larg * .96 * s, .4 * s, 0]),
                       fill_color="#fbf3df", fill_opacity=1, stroke_color=PT, stroke_width=4)
        pagD = pagE.copy().flip(UP, about_point=meio)
        linhas = VGroup(*[Line(meio + np.array([sx * .12 * s, (.22 - k * .14) * s, 0]),
                               meio + np.array([sx * larg * .78 * s, (.24 - k * .14) * s, 0]),
                               stroke_color="#b9a37a", stroke_width=3) for sx in (-1, 1) for k in range(4)])
        folha = pagD.copy().stretch(max(.05, 1 - 2 * virar), 0, about_point=meio)
        fita = Line(meio + UP * .38 * s, meio + DOWN * .62 * s + RIGHT * .05 * s, stroke_color="#d6a84a",
                    stroke_width=6)
        livro.become(VGroup(capa, pagE, pagD, linhas, folha, fita).set_opacity(lv) if lv > .02 else VGroup())
        # mãos por cima do livro: já estão (ordem de desenho)

    motor = Dot(fill_opacity=0, stroke_width=0)
    motor.add_updater(frame)
    scene.add(motor)
    frame(motor, 0)
    return dm


class SabioVivo(Scene):
    def construct(self):
        job = json.loads(Path(os.environ['SABIO_JOB']).read_text())
        dur = float(job['duration'])
        raios, poeira, T = montar_cenario(self, dur)
        sabio_vivo(self, job, T)
        montar_mesa(self, T)
        self.add(raios, poeira)
        self.wait(dur)
