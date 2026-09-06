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
#  CARTELA, SELO E MARCA
# =====================================================================
def cartela(titulo: str):
    t = Text(titulo.upper(), font=FONTE, weight=BOLD, font_size=64, color=WHITE)
    if t.width > P.LARG_SEGURA:
        t.scale(P.LARG_SEGURA / t.width)
    banda = RoundedRectangle(width=t.width + 0.7, height=t.height + 0.6,
                             corner_radius=0.22, fill_color=AZUL, fill_opacity=0.94,
                             stroke_color=DOURADO, stroke_width=7)
    return VGroup(banda, t)


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
        dm = P.ranzinza("desconfiado")
        G = dm["grupo"]
        G.scale(1.95)
        G.shift(UP * (3.2 - dm["cab"].get_center()[1]))
        self.add(G)
        L.respirar(G, amp=0.045, periodo=3.0)

        self.add(frente)
        vapor(self, np.array([2.9, piso_y + 0.9, 0]))

        lip_sync(self, dm, envelope, fps)

        # legenda karaokê frase a frase, no terço central
        itens = []
        for f in job["frases"]:
            itens += P.legenda_karaoke(f["texto"], f["inicio"], f["fim"],
                                       y=-1.6, fs=52, por_bloco=3)
        self.add(P.trilha_temporal(itens))

        # cartela do assunto nos primeiros segundos — é o frame da grade
        cart = cartela(job["titulo"]).move_to([0, 6.0, 0])
        selo = selo_referencia(job["referencia"]).move_to([0, 6.0, 0])
        passagem = next((s for s in job["segmentos"] if s["papel"] == "passagem"), None)
        topo = [(0.0, 2.4, cart)]
        if passagem:
            topo.append((passagem["inicio"], passagem["fim"], selo))
        self.add(P.trilha_temporal(topo, pop=0.10))

        m = marca().move_to([0, -config.frame_height / 2 + 2.4, 0])
        self.add(m)

        P.camera_push_in(self, dur=2.2, duracao=dur)
        self.wait(dur)
