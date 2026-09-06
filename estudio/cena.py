"""Cena Manim do @sabioefeliz — o Seu Ranzinza contando o provérbio do dia.

O personagem é EXATAMENTE o ranzinza() do repositório da previsão do tempo:
os dois arquivos dela (previsao_lib.py e dvh_lib.py) foram trazidos para cá sem
alteração. Mesmo mundo visual, mesmo traço, mesma família de canais.

O que muda aqui é o LUGAR: em vez do quintal com varal, uma manhã com janela,
mesa, planta e caneca — o canal de provérbios tem o cenário dele.

Como rodar (o render.py faz isso por você):
    manim -qh -r 1080,1920 --fps 30 estudio/cena.py Episodio
com a variável SABIO_JOB apontando para o JSON do episódio.
"""
from __future__ import annotations

import json
import os

from manim import *
import numpy as np

# O frame precisa ter LARGURA 8.0 para as constantes do previsao_lib
# (SEGURA, LARG_SEGURA, ZOOM_MIN) continuarem valendo. No vertical, a altura
# é que cresce.
config.frame_width = 8.0
config.frame_height = 8.0 * 1920 / 1080

from estudio import previsao_lib as P   # noqa: E402
from estudio import dvh_lib as L        # noqa: E402

PT = L.PT
FONTE = L.FONTE
FIM_CAPA = 2.2      # até quando a capa central fica no ar
DOURADO = "#d6a84a"
CREME = "#f7ecd6"
AZUL = "#174a56"


def carregar_job() -> dict:
    caminho = os.environ["SABIO_JOB"]
    return json.loads(open(caminho, encoding="utf-8").read())


# =====================================================================
#  CENÁRIO DA MANHÃ — janela com sol, mesa, planta e caneca
# =====================================================================
def cenario_manha():
    W, H = config.frame_width, config.frame_height

    fundo = Rectangle(width=W * 1.2, height=H * 1.2, stroke_width=0)
    fundo.set_fill(color=["#fde8c9", "#e9c59c"], opacity=1)
    fundo.set_sheen_direction(UP)

    janela = VGroup(
        RoundedRectangle(width=2.5, height=3.0, corner_radius=0.14,
                         fill_color="#d4b084", fill_opacity=1,
                         stroke_color=PT, stroke_width=10),
        RoundedRectangle(width=2.1, height=2.6, corner_radius=0.08,
                         fill_color="#b0d6e2", fill_opacity=1, stroke_width=0),
    )
    sol = Circle(radius=0.62, fill_color="#ffe29e", fill_opacity=1, stroke_width=0)
    sol.move_to(janela.get_center() + DOWN * 0.25)
    cruz = VGroup(
        Line(janela.get_top() + DOWN * 0.2, janela.get_bottom() + UP * 0.2,
             stroke_color=PT, stroke_width=9),
        Line(janela.get_left() + RIGHT * 0.2, janela.get_right() + LEFT * 0.2,
             stroke_color=PT, stroke_width=9),
    )
    janela = VGroup(janela, sol, cruz).move_to([2.3, 4.9, 0])

    piso_y = -4.2
    mesa = VGroup(
        Rectangle(width=W * 1.2, height=0.22, fill_color="#966a48", fill_opacity=1,
                  stroke_color=PT, stroke_width=9).move_to([0, piso_y, 0]),
        Rectangle(width=W * 1.2, height=6.0, fill_color="#7e583c", fill_opacity=1,
                  stroke_width=0).move_to([0, piso_y - 3.1, 0]),
    )

    vaso = VGroup(
        RoundedRectangle(width=0.9, height=0.7, corner_radius=0.12,
                         fill_color="#e2d0b2", fill_opacity=1,
                         stroke_color=PT, stroke_width=8),
    )
    folhas = VGroup(*[
        Ellipse(width=0.62, height=0.82, fill_color="#4a7c60", fill_opacity=1,
                stroke_color=PT, stroke_width=8).shift(RIGHT * dx + UP * dy)
        for dx, dy in ((-0.45, 0.55), (0.0, 0.80), (0.45, 0.55))
    ])
    planta = VGroup(vaso, folhas).move_to([-2.9, piso_y + 0.85, 0])

    caneca = VGroup(
        RoundedRectangle(width=0.68, height=0.72, corner_radius=0.10,
                         fill_color=CREME, fill_opacity=1, stroke_color=PT, stroke_width=8),
        Arc(radius=0.22, start_angle=-PI / 2, angle=PI,
            arc_center=RIGHT * 0.42).set_stroke(PT, 8),
    ).move_to([2.9, piso_y + 0.5, 0])

    frente = VGroup(mesa, planta, caneca)
    return VGroup(fundo, janela), frente, piso_y


def vapor(scene, caneca_topo, n=3):
    """Fumacinha subindo da caneca — nada na cena pode ficar 100% parado."""
    for i in range(n):
        arco = Arc(radius=0.16, start_angle=PI * 0.15, angle=PI * 0.7,
                   arc_center=caneca_topo + RIGHT * (i - 1) * 0.16)
        arco.set_stroke(WHITE, 5, opacity=0.0)
        st = {"t": i * 0.9}

        def _sobe(mo, dt, st=st, base=caneca_topo + RIGHT * (i - 1) * 0.16):
            st["t"] += dt
            f = (st["t"] % 2.7) / 2.7
            mo.move_to(base + UP * (0.25 + f * 1.15))
            mo.set_stroke(opacity=0.55 * (1 - f))
        arco.add_updater(_sobe)
        scene.add(arco)


# =====================================================================
#  O ROSTO DO CANAL
# =====================================================================
def rosto_sabio(dm):
    """Troca a cara de bravo pela de quem já viu muito e está em paz.

    O previsao_lib.py fica intocado: o personagem nasce igual ao do canal do
    tempo e a expressão é ajustada aqui, em cima. Assim os dois canais
    continuam compartilhando o mesmo desenho sem um mexer no outro.

    O que muda: a boca vira sorriso, as sobrancelhas param de franzir e
    ganham arco, e entram bochechas rosadas — é o detalhe que faz o rosto
    ler como simpático na miniatura, onde ninguém enxerga sutileza.
    """
    c = dm["cab"].get_center()

    dm["boca"].become(
        ArcBetweenPoints(c + DOWN * 0.62 + LEFT * 0.27, c + DOWN * 0.62 + RIGHT * 0.27,
                         angle=PI / 2.7).set_stroke(PT, 9))

    dm["sobE"].become(
        ArcBetweenPoints(c + LEFT * 0.54 + UP * 0.30, c + LEFT * 0.14 + UP * 0.40,
                         angle=-PI / 3.2).set_stroke(P.GRIS, 13))
    dm["sobD"].become(
        ArcBetweenPoints(c + RIGHT * 0.14 + UP * 0.40, c + RIGHT * 0.54 + UP * 0.30,
                         angle=-PI / 3.2).set_stroke(P.GRIS, 13))

    bochechas = VGroup(*[
        Ellipse(width=0.38, height=0.24, fill_color="#e79a86", fill_opacity=0.6,
                stroke_width=0).move_to(c + RIGHT * (lado * 0.54) + DOWN * 0.28)
        for lado in (-1, 1)])
    subs = dm["grupo"].submobjects
    subs.insert(subs.index(dm["cab"]) + 1, bochechas)   # atrás de nariz, óculos e bigode
    return dm


# =====================================================================
#  CAPA, SELO E MARCA
# =====================================================================
def capa(referencia: str, titulo: str):
    """O cartão dos primeiros segundos — e, por tabela, a miniatura da grade.

    O Instagram recorta o QUADRADO DO MEIO do Reel para montar a grade do
    perfil. Cartela no topo simplesmente não aparece lá: some no corte. Por
    isso a capa mora no centro, com a referência e o assunto grandes — é o
    que faz cada quadradinho da grade ser diferente do outro e dizer do que
    o vídeo trata.
    """
    ref = Text(referencia.upper(), font=FONTE, weight=BOLD, font_size=44, color=DOURADO)
    tit = Text(titulo.upper(), font=FONTE, weight=BOLD, font_size=68, color=WHITE)

    larg = P.LARG_SEGURA - 0.7
    if tit.width > larg:                      # título comprido: quebra em duas linhas
        palavras = titulo.upper().split()
        meio = len(palavras) // 2 + len(palavras) % 2
        tit = VGroup(
            Text(" ".join(palavras[:meio]), font=FONTE, weight=BOLD, font_size=68, color=WHITE),
            Text(" ".join(palavras[meio:]), font=FONTE, weight=BOLD, font_size=68, color=WHITE),
        ).arrange(DOWN, buff=0.16)
    if tit.width > larg:
        tit.scale(larg / tit.width)
    if ref.width > larg:
        ref.scale(larg / ref.width)

    risco = Line(LEFT * 1.1, RIGHT * 1.1, stroke_color=DOURADO, stroke_width=6)
    miolo = VGroup(ref, risco, tit).arrange(DOWN, buff=0.30)

    banda = RoundedRectangle(width=max(miolo.width + 0.9, 6.4), height=miolo.height + 0.95,
                             corner_radius=0.28, fill_color=AZUL, fill_opacity=0.95,
                             stroke_color=DOURADO, stroke_width=8)
    return VGroup(banda, miolo.move_to(banda.get_center()))


def selo_referencia(referencia: str):
    t = Text(referencia, font=FONTE, weight=BOLD, font_size=44, color=PT)
    banda = RoundedRectangle(width=t.width + 0.8, height=t.height + 0.45,
                             corner_radius=0.30, fill_color=DOURADO, fill_opacity=1,
                             stroke_color=PT, stroke_width=6)
    return VGroup(banda, t)


def marca():
    t = Text("@sabioefeliz", font=FONTE, weight=BOLD, font_size=30, color=WHITE)
    banda = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.3,
                             corner_radius=0.14, fill_color=BLACK, fill_opacity=0.55,
                             stroke_width=0)
    return VGroup(banda, t)


# =====================================================================
#  LIP SYNC — boca aberta pela amplitude do áudio
# =====================================================================
def lip_sync(scene, dm, envelope, fps):
    """A boca do previsao_lib é um arco de sorriso. Aqui ela ganha a versão
    aberta e um motor invisível alterna as duas pela amplitude.

    O updater NÃO pode ficar pendurado no personagem: animar um submobjeto
    tira o grupo de scene.mobjects e mata todos os updaters dele, sem erro.
    Por isso o motor é um Dot invisível.
    """
    boca = dm["boca"]
    # o deslocamento da boca em relação à cabeça: assim a boca aberta segue a
    # respiração e cai no lugar certo em qualquer personagem, sem número mágico
    desloc = boca.get_center() - dm["cab"].get_center()
    aberta = Ellipse(width=0.42, height=0.12, fill_color="#5a2a28", fill_opacity=1,
                     stroke_color=PT, stroke_width=6).move_to(boca.get_center())
    aberta.set_opacity(0)
    scene.add(aberta)

    st = {"t": 0.0}

    def _boca(mo, dt):
        st["t"] += dt
        i = min(int(st["t"] * fps), len(envelope) - 1)
        a = envelope[i] if i >= 0 else 0.0
        alvo = dm["cab"].get_center() + desloc
        if a < 0.14:
            aberta.set_opacity(0)
            boca.set_stroke(opacity=1)
        else:
            boca.set_stroke(opacity=0)
            aberta.set_opacity(1)
            aberta.stretch_to_fit_height(0.12 + 0.36 * a)
            aberta.stretch_to_fit_width(0.40 + 0.10 * a)
            aberta.move_to(alvo)

    motor = Dot(fill_opacity=0, stroke_width=0)
    motor.add_updater(_boca)
    scene.add(motor)


# =====================================================================
#  A CENA
# =====================================================================
class Episodio(MovingCameraScene):
    def construct(self):
        job = carregar_job()
        dur = float(job["duracao_s"])
        fps = int(job.get("fps", 30))
        envelope = job["envelope"]

        fundo, frente, piso_y = cenario_manha()
        self.add(fundo)

        # o Seu Ranzinza fica ATRÁS da mesa: plano médio, rosto grande na tela.
        # "desconfiado" em vez de "bravo": aqui ele não está reclamando do
        # tempo, está desconfiado da pressa de quem vai responder com raiva.
        dm = rosto_sabio(P.ranzinza("desconfiado"))
        G = dm["grupo"]
        G.scale(1.95)
        G.shift(UP * (3.2 - dm["cab"].get_center()[1]))
        self.add(G)
        L.respirar(G, amp=0.045, periodo=3.0)

        self.add(frente)
        vapor(self, np.array([2.9, piso_y + 0.9, 0]))

        lip_sync(self, dm, envelope, fps)

        # legenda karaokê frase a frase, no terço central.
        # Enquanto a capa está no ar a legenda fica fora: as duas no mesmo
        # lugar viram sopa. Quem assiste sem som lê o título na capa.
        itens = []
        for f in job["frases"]:
            itens += P.legenda_karaoke(f["texto"], f["inicio"], f["fim"],
                                       y=-1.6, fs=52, por_bloco=3)
        itens = [(max(i, FIM_CAPA), f, m) for (i, f, m) in itens if f > FIM_CAPA]
        self.add(P.trilha_temporal(itens))

        # capa no CENTRO nos primeiros segundos: é ela que vira a miniatura
        # da grade. A câmera abre olhando para y=1.0, então a capa nasce ali.
        cap = capa(job["referencia"], job["titulo"]).move_to([0, -0.25, 0])
        self.add(P.trilha_temporal([(0.0, FIM_CAPA, cap)], pop=0.0))

        # selo com a referência enquanto ele lê a passagem
        selo = selo_referencia(job["referencia"]).move_to([0, 6.0, 0])
        passagem = next((s for s in job["segmentos"] if s["papel"] == "passagem"), None)
        if passagem:
            self.add(P.trilha_temporal([(passagem["inicio"], passagem["fim"], selo)], pop=0.10))

        m = marca().move_to([0, -config.frame_height / 2 + 2.4, 0])
        self.add(m)

        P.camera_push_in(self, dur=2.2, duracao=dur)
        self.wait(dur)
