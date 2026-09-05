"""
dvh_lib — Biblioteca visual do canal Delegacia Vinte e Quatro Horas (DVH).

Personagens, cenários e objetos desenhados por código em Manim. Traço grosso,
cabeça grande, rosto expressivo, fundo colorido. Custo zero, sem IA de imagem,
personagem sempre idêntico entre cenas.

Cada função de personagem devolve um dict com:
    grupo : VGroup do personagem inteiro (é o que você adiciona/anima)
    cab   : o círculo do rosto (âncora pra balões, óculos, etc.)
    oe,od : olhos (pra susto: .animate.scale(...))
    boca  : a boca (invisibilize e passe pra anexar_lipsync se o personagem fala)

Regra de ouro do movimento: NADA congela. Todo personagem em cena recebe o
updater `respirar()` pra ter um leve sobe-e-desce contínuo. Cenas paradas com
self.wait() sem updater dão a sensação de "travou" — foi reclamação real.
"""
from manim import *
import numpy as np

# ---- paleta oficial ----
PT = BLACK
AMAR = "#ffd240"
VERM = "#e2483c"
VERD = "#32a06e"
NAVY = "#0b0d16"
MUT = "#9aa3bd"
FONTE = "Poppins"   # instalada pelo setup_ambiente.sh (fonts-google-poppins)


# =====================================================================
#  LEGENDA — banda escura translúcida + texto branco Poppins Bold.
#  NÃO use contorno preto grosso no texto: embola as letras (erro real,
#  "a legenda ficou ruim"). A banda dá contraste; o texto fica limpo.
# =====================================================================
def legenda(txt, font_size=30, cor=WHITE):
    t = Text(txt, font=FONTE, weight=BOLD, font_size=font_size, color=cor)
    if t.width > 11.2:
        t.scale(11.2 / t.width)
    band = RoundedRectangle(width=t.width + 0.7, height=t.height + 0.4,
                            corner_radius=0.14, fill_color=BLACK,
                            fill_opacity=0.7, stroke_width=0)
    return VGroup(band, t).to_edge(DOWN, buff=0.4)


# =====================================================================
#  UPDATERS DE MOVIMENTO CONTÍNUO
# =====================================================================
def respirar(G, amp=0.05, periodo=2.6):
    """Sobe-e-desce sutil e infinito. Chame em TODO personagem em cena."""
    st = {'t': 0.0, 'o': 0.0}
    def _r(mo, dt):
        st['t'] += dt
        novo = amp * np.sin(st['t'] * TAU / periodo)
        mo.shift(UP * (novo - st['o']))
        st['o'] = novo
    G.add_updater(_r)
    return _r


def digitar(maoE, maoD, amp=0.05, vel=3.0):
    """Mãos alternadas subindo/descendo — pra quem digita no PC/teclado."""
    st = {'t': 0.0, 'oe': 0.0, 'od': 0.0}
    def _d(mo, dt):
        st['t'] += dt
        ne = amp * np.sin(st['t'] * TAU * vel)
        nd = amp * np.sin(st['t'] * TAU * vel + PI)
        maoE.shift(UP * (ne - st['oe'])); st['oe'] = ne
        maoD.shift(UP * (nd - st['od'])); st['od'] = nd
    return _d   # anexe no grupo: G.add_updater(digitar(g["maoE"], g["maoD"]))


# =====================================================================
#  CENÁRIOS  (fundo do frame inteiro)
# =====================================================================
def _grad(cores, direcao=UP):
    W = config.frame_width; H = config.frame_height
    r = Rectangle(width=W + 2, height=H + 2, fill_opacity=1, stroke_width=0).set_color(cores)
    r.set_sheen_direction(direcao)
    return r


def cenario_dia():
    """Céu azul, sol com raios, nuvens, prédios com janelas acesas, chão."""
    W = config.frame_width; H = config.frame_height
    g = VGroup()
    g.add(_grad(["#7fb4d6", "#4f83a8"]))
    sol = Circle(radius=0.5, fill_color="#ffe08a", fill_opacity=1, stroke_width=0)
    raios = VGroup(*[Line(RIGHT * 0.62, RIGHT * 0.95, stroke_color="#ffe08a", stroke_width=7)
                     .rotate(a, about_point=ORIGIN) for a in np.arange(0, TAU, TAU / 12)])
    g.add(VGroup(raios, sol).to_corner(UR, buff=0.7).shift(DOWN * 0.2))
    def nuvem():
        n = VGroup(*[Circle(radius=r, fill_color=WHITE, fill_opacity=0.9, stroke_width=0)
                     for r in [0.35, 0.5, 0.4]])
        n[0].shift(LEFT * 0.5); n[2].shift(RIGHT * 0.5); return n
    g.add(nuvem().to_edge(UP, buff=1.0).shift(LEFT * 3.5),
          nuvem().scale(0.8).to_edge(UP, buff=1.7).shift(RIGHT * 3))
    predios = VGroup(); x = -7.2
    while x < 7:
        w = np.random.uniform(1.0, 1.7); h = np.random.uniform(1.3, 2.6)
        p = Rectangle(width=w, height=h, fill_color="#33566e", fill_opacity=1,
                      stroke_color="#25404f", stroke_width=3)
        jan = VGroup()
        for jy in np.arange(h / 2 - 0.35, -h / 2 + 0.2, -0.5):
            for jx in np.arange(-w / 2 + 0.3, w / 2 - 0.2, 0.45):
                jan.add(Square(0.18, fill_color="#ffd98a",
                               fill_opacity=float(np.random.choice([0.9, 0.2])),
                               stroke_width=0).move_to([jx, jy, 0]))
        pg = VGroup(p, jan); pg.move_to([x + w / 2, 0, 0]); predios.add(pg); x += w + 0.1
    predios.arrange(RIGHT, buff=0.08, aligned_edge=DOWN).to_edge(DOWN, buff=0).shift(DOWN * 0.1)
    g.add(predios)
    g.add(Rectangle(width=W + 2, height=1.2, fill_color="#2a3a2f", fill_opacity=1,
                    stroke_width=0).to_edge(DOWN, buff=0))
    return g


def galpao_noite():
    """Galpão escuro: cone de luz, mural com o 'roteiro' do golpe, silhuetas ao fundo.
    O mural fica em g[3] — use Indicate(cen[3]) pra destacar 'o roteiro na parede'."""
    W = config.frame_width; H = config.frame_height
    g = VGroup()
    g.add(_grad(["#243040", "#151b24"]))
    lamp = VGroup(Line(UP * 3.8, UP * 3.4, stroke_color="#555", stroke_width=4),
                  Circle(radius=0.18, fill_color="#ffe08a", fill_opacity=1, stroke_width=0).move_to(UP * 3.35))
    cone = Polygon(UP * 3.3, DOWN * 0.2 + LEFT * 3, DOWN * 0.2 + RIGHT * 3,
                   fill_color="#ffe08a", fill_opacity=0.10, stroke_width=0)
    g.add(cone, lamp)
    mural = VGroup()
    for i in range(6):
        pap = Rectangle(width=0.7, height=0.95, fill_color="#e9e6df", fill_opacity=1,
                        stroke_color="#111", stroke_width=2)
        linhas = VGroup(*[Line(LEFT * 0.25, RIGHT * 0.25, stroke_color="#7a7a7a", stroke_width=2)
                          .shift(UP * (0.28 - j * 0.16)) for j in range(4)])
        pin = Dot(radius=0.05, color="#c33").shift(UP * 0.5)
        mural.add(VGroup(pap, linhas, pin))
    mural.arrange_in_grid(rows=2, cols=3, buff=0.3).to_edge(LEFT, buff=0.6).shift(UP * 1.4)
    g.add(mural)
    for x in [4.6, 5.8]:
        silh = VGroup(Circle(radius=0.35, fill_color="#2c3a4a", fill_opacity=1, stroke_width=0).shift(UP * 0.5),
                      Rectangle(width=0.7, height=0.9, fill_color="#2c3a4a", fill_opacity=1, stroke_width=0).shift(DOWN * 0.3),
                      Rectangle(width=0.9, height=0.5, fill_color="#1b2530", fill_opacity=1, stroke_width=0).shift(DOWN * 0.9))
        silh.scale(0.8).move_to([x, -0.2, 0]); g.add(silh)
    return g


def rua_bg():
    """Rua ao entardecer: casa à esquerda, asfalto com faixa. Pra cena do motoboy."""
    W = config.frame_width; H = config.frame_height
    g = VGroup()
    g.add(_grad(["#f0a878", "#7a6fa0"]))
    g.add(Circle(radius=0.7, fill_color="#ffd27a", fill_opacity=1, stroke_width=0).to_edge(UP, buff=0.7).shift(RIGHT * 3))
    casa = VGroup(Rectangle(width=3.2, height=3.4, fill_color="#c9a88a", fill_opacity=1, stroke_color=PT, stroke_width=6),
                  Polygon([-1.8, 1.7, 0], [1.8, 1.7, 0], [0, 2.7, 0], fill_color="#8a5a44", fill_opacity=1, stroke_color=PT, stroke_width=6))
    porta = RoundedRectangle(width=0.9, height=1.7, corner_radius=0.1, fill_color="#6a4a34", fill_opacity=1, stroke_color=PT, stroke_width=5).move_to([-0.7, -0.85, 0])
    jan = Square(0.8, fill_color="#bfe0ef", fill_opacity=1, stroke_color=PT, stroke_width=5).move_to([0.8, -0.2, 0])
    casa.add(porta, jan); casa.scale(0.95).to_edge(LEFT, buff=-0.3).to_edge(DOWN, buff=1.0); g.add(casa)
    g.add(Rectangle(width=W + 2, height=2.0, fill_color="#3a3d44", fill_opacity=1, stroke_width=0).to_edge(DOWN, buff=0))
    g.add(VGroup(*[Rectangle(width=0.6, height=0.1, fill_color="#ffd98a", fill_opacity=1, stroke_width=0).move_to([x, -2.9, 0]) for x in np.arange(-7, 8, 1.4)]))
    g.add(Rectangle(width=W + 2, height=0.4, fill_color="#8a8d94", fill_opacity=1, stroke_width=0).move_to([0, -2.0, 0]))
    return g


def delegacia_bg():
    """Delegacia: mural de fotos com linha vermelha, placa DELEGACIA, chão."""
    W = config.frame_width; H = config.frame_height; g = VGroup()
    g.add(_grad(["#5b6470", "#3a4048"]))
    mural = RoundedRectangle(width=3.2, height=2.2, corner_radius=0.1, fill_color="#8a6a4a", fill_opacity=1, stroke_color=PT, stroke_width=5).to_edge(LEFT, buff=0.7).shift(UP * 1.4)
    fotos = VGroup(*[Rectangle(width=0.6, height=0.5, fill_color="#dcd7cf", fill_opacity=1, stroke_color=PT, stroke_width=2) for _ in range(4)])
    fotos.arrange_in_grid(rows=2, cols=2, buff=0.25).move_to(mural)
    linha = Line(fotos[0].get_center(), fotos[3].get_center(), stroke_color=VERM, stroke_width=3)
    g.add(mural, fotos, linha)
    placa = VGroup(RoundedRectangle(width=3.0, height=0.7, corner_radius=0.1, fill_color="#1e2e60", fill_opacity=1, stroke_width=0),
                   Text("DELEGACIA", font=FONTE, weight=BOLD, font_size=28, color=WHITE)).to_edge(UP, buff=0.5).shift(RIGHT * 3)
    g.add(placa)
    g.add(Rectangle(width=W + 2, height=1.4, fill_color="#2f343b", fill_opacity=1, stroke_width=0).to_edge(DOWN, buff=0))
    return g


def cadeia_bg():
    """Parede de tijolos cinza — fundo da cena de prisão. As grades você anima
    por cima com GrowFromEdge (ver exemplo no método)."""
    W = config.frame_width; H = config.frame_height; g = VGroup()
    g.add(Rectangle(width=W + 2, height=H + 2, fill_color="#2b2f36", fill_opacity=1, stroke_width=0))
    g.add(VGroup(*[Rectangle(width=1.2, height=0.5, fill_opacity=0, stroke_color="#3a3f47", stroke_width=2).move_to([x, y, 0])
                   for y in np.arange(-3, 3, 0.55) for x in np.arange(-7, 7, 1.25)]))
    return g


def grades_cadeia():
    """VGroup de barras verticais. Anime com LaggedStart(GrowFromEdge(b,UP))."""
    return VGroup(*[Line(UP * 4, DOWN * 4, stroke_color="#11141a", stroke_width=14).shift(RIGHT * x)
                    for x in np.arange(-6, 7, 1.5)])


# =====================================================================
#  PERSONAGENS
# =====================================================================
def idosa(cabelo_cor="#c9c4bd", blusa_cor="#b0708f"):
    """Senhora de cabelo grisalho com coque, óculos redondos, bochechas rosadas,
    blusa mauve, segurando um celular de tela verde. (A 'Dona Marlene'.)"""
    cabelo = Circle(radius=1.02, fill_color=cabelo_cor, fill_opacity=1, stroke_color=PT, stroke_width=10).shift(UP * 1.5)
    bun = Circle(radius=0.3, fill_color=cabelo_cor, fill_opacity=1, stroke_color=PT, stroke_width=8).move_to(cabelo.get_top() + UP * 0.02)
    cab = Circle(radius=0.9, stroke_color=PT, stroke_width=15, fill_color=WHITE, fill_opacity=1).shift(UP * 1.4)
    oc_e = Circle(radius=0.24, stroke_color=PT, stroke_width=7).move_to(cab.get_center() + LEFT * 0.33 + UP * 0.02)
    oc_d = Circle(radius=0.24, stroke_color=PT, stroke_width=7).move_to(cab.get_center() + RIGHT * 0.33 + UP * 0.02)
    ponte = Line(oc_e.get_right(), oc_d.get_left(), stroke_color=PT, stroke_width=6)
    oe = Dot(oc_e.get_center(), radius=0.1, color=PT); od = Dot(oc_d.get_center(), radius=0.1, color=PT)
    bE = Ellipse(width=0.28, height=0.18, fill_color="#f2a6a0", fill_opacity=0.7, stroke_width=0).move_to(cab.get_center() + LEFT * 0.55 + DOWN * 0.25)
    bD = Ellipse(width=0.28, height=0.18, fill_color="#f2a6a0", fill_opacity=0.7, stroke_width=0).move_to(cab.get_center() + RIGHT * 0.55 + DOWN * 0.25)
    boca = Arc(radius=0.2, start_angle=PI * 0.2, angle=PI * 0.6, arc_center=cab.get_center() + DOWN * 0.42, stroke_color=PT, stroke_width=7)
    pesc = Line(cab.get_bottom(), cab.get_bottom() + DOWN * 0.2, stroke_color=PT, stroke_width=15)
    top = pesc.get_end()
    blusa = Polygon(top + LEFT * 0.35, top + RIGHT * 0.35, top + DOWN * 1.5 + RIGHT * 0.7, top + DOWN * 1.5 + LEFT * 0.7, fill_color=blusa_cor, fill_opacity=1, stroke_color=PT, stroke_width=10)
    gola = VGroup(Line(top + LEFT * 0.2, top + DOWN * 0.35, stroke_color=PT, stroke_width=6), Line(top + RIGHT * 0.2, top + DOWN * 0.35, stroke_color=PT, stroke_width=6))
    q = top + DOWN * 1.5
    pe = Line(q + LEFT * 0.35, q + DOWN * 1.35 + LEFT * 0.55, stroke_color=PT, stroke_width=15)
    pd = Line(q + RIGHT * 0.35, q + DOWN * 1.35 + RIGHT * 0.55, stroke_color=PT, stroke_width=15)
    se = Ellipse(width=0.4, height=0.2, fill_color=PT, fill_opacity=1, stroke_width=0).move_to(pe.get_end() + DOWN * 0.02 + LEFT * 0.08)
    sd = Ellipse(width=0.4, height=0.2, fill_color=PT, fill_opacity=1, stroke_width=0).move_to(pd.get_end() + DOWN * 0.02 + RIGHT * 0.08)
    omb = top + DOWN * 0.15
    be = Line(omb + LEFT * 0.3, omb + DOWN * 0.85 + LEFT * 0.7, stroke_color=PT, stroke_width=15)
    bd = Line(omb + RIGHT * 0.3, omb + UP * 0.35 + RIGHT * 0.7, stroke_color=PT, stroke_width=15)
    fbody = RoundedRectangle(width=0.42, height=0.82, corner_radius=0.08, fill_color="#222", fill_opacity=1, stroke_color=PT, stroke_width=6)
    fscr = RoundedRectangle(width=0.32, height=0.62, corner_radius=0.05, fill_color="#7ec16a", fill_opacity=1, stroke_width=0)
    fone = VGroup(fbody, fscr).move_to(bd.get_end() + UP * 0.12)
    grupo = VGroup(pesc, blusa, gola, pe, pd, se, sd, be, bd, cabelo, bun, cab, oc_e, oc_d, ponte, bE, bD, oe, od, boca, fone)
    return dict(grupo=grupo, cab=cab, oe=oe, od=od, boca=boca, fone=fone)


marlene = idosa   # alias histórico


def golpista():
    """Homem de moletom com capuz, headset com microfone, topete, sorriso torto
    e sobrancelha erguida (deboche). Devolve maoE/maoD pra updater `digitar`."""
    cabelo = Circle(radius=0.98, fill_color="#2b2b33", fill_opacity=1, stroke_color=PT, stroke_width=8).shift(UP * 1.55)
    cab = Circle(radius=0.9, stroke_color=PT, stroke_width=15, fill_color=WHITE, fill_opacity=1).shift(UP * 1.4)
    top = VGroup(*[Line(cab.get_top() + LEFT * 0.3 + i * RIGHT * 0.2, cab.get_top() + UP * 0.18 + LEFT * 0.25 + i * RIGHT * 0.2, stroke_color="#2b2b33", stroke_width=8) for i in range(4)])
    banda = Arc(radius=1.0, start_angle=PI * 0.15, angle=PI * 0.7, arc_center=cab.get_center(), stroke_color="#222", stroke_width=10)
    conE = RoundedRectangle(width=0.28, height=0.5, corner_radius=0.08, fill_color="#222", fill_opacity=1, stroke_color=PT, stroke_width=4).move_to(cab.get_center() + LEFT * 0.92)
    conD = RoundedRectangle(width=0.28, height=0.5, corner_radius=0.08, fill_color="#222", fill_opacity=1, stroke_color=PT, stroke_width=4).move_to(cab.get_center() + RIGHT * 0.92)
    mic = VGroup(ArcBetweenPoints(conE.get_bottom(), cab.get_center() + DOWN * 0.35 + LEFT * 0.45, angle=-PI / 3).set_stroke("#222", 6),
                 Dot(cab.get_center() + DOWN * 0.35 + LEFT * 0.42, radius=0.07, color="#222"))
    oe = Dot(cab.get_center() + LEFT * 0.3 + UP * 0.02, radius=0.11, color=PT)
    od = Dot(cab.get_center() + RIGHT * 0.3 + UP * 0.02, radius=0.11, color=PT)
    sob = Line(cab.get_center() + RIGHT * 0.15 + UP * 0.28, cab.get_center() + RIGHT * 0.45 + UP * 0.36, stroke_color=PT, stroke_width=6)
    smirk = ArcBetweenPoints(cab.get_center() + DOWN * 0.4 + LEFT * 0.25, cab.get_center() + DOWN * 0.28 + RIGHT * 0.3, angle=-PI / 3).set_stroke(PT, 7)
    pesc = Line(cab.get_bottom(), cab.get_bottom() + DOWN * 0.22, stroke_color=PT, stroke_width=15)
    t = pesc.get_end()
    capuz = VGroup(ArcBetweenPoints(t + LEFT * 0.55, t + RIGHT * 0.55, angle=-PI * 0.7).set_stroke(PT, 8).set_fill("#3a4a6b", 1))
    corpo = Polygon(t + LEFT * 0.55, t + RIGHT * 0.55, t + DOWN * 1.4 + RIGHT * 0.85, t + DOWN * 1.4 + LEFT * 0.85, fill_color="#3a4a6b", fill_opacity=1, stroke_color=PT, stroke_width=10)
    ziper = Line(t + DOWN * 0.1, t + DOWN * 1.3, stroke_color=PT, stroke_width=4)
    cordao = VGroup(Line(t + LEFT * 0.12, t + DOWN * 0.5 + LEFT * 0.12, stroke_color="#dcdcdc", stroke_width=4),
                    Line(t + RIGHT * 0.12, t + DOWN * 0.5 + RIGHT * 0.12, stroke_color="#dcdcdc", stroke_width=4))
    omb = t + DOWN * 0.2
    be = Line(omb + LEFT * 0.55, omb + DOWN * 0.7 + LEFT * 0.25, stroke_color="#3a4a6b", stroke_width=22)
    bd = Line(omb + RIGHT * 0.55, omb + DOWN * 0.7 + RIGHT * 0.25, stroke_color="#3a4a6b", stroke_width=22)
    maoE = Dot(be.get_end(), radius=0.12, color=WHITE); maoD = Dot(bd.get_end(), radius=0.12, color=WHITE)
    grupo = VGroup(cabelo, cab, top, banda, conE, conD, mic, corpo, capuz, ziper, cordao, be, bd, maoE, maoD, pesc, oe, od, sob, smirk)
    return dict(grupo=grupo, cab=cab, oe=oe, od=od, smirk=smirk, boca=smirk, maoE=maoE, maoD=maoD)


def delegado():
    """Policial: quepe azul com distintivo, bigode, estrela dourada no peito,
    uniforme azul-marinho. A boca é grupo[-1] (Line) — passe pro lip sync."""
    cab = Circle(radius=0.9, stroke_color=PT, stroke_width=15, fill_color=WHITE, fill_opacity=1).shift(UP * 1.4)
    aba = Ellipse(width=2.0, height=0.4, fill_color="#1e2a4a", fill_opacity=1, stroke_color=PT, stroke_width=6).move_to(cab.get_top() + DOWN * 0.05)
    copa = Polygon(cab.get_center() + UP * 0.35 + LEFT * 0.9, cab.get_center() + UP * 0.35 + RIGHT * 0.9, cab.get_center() + UP * 0.95 + RIGHT * 0.6, cab.get_center() + UP * 0.95 + LEFT * 0.6, fill_color="#26356b", fill_opacity=1, stroke_color=PT, stroke_width=6)
    dist = Rectangle(width=0.3, height=0.2, fill_color=AMAR, fill_opacity=1, stroke_color=PT, stroke_width=3).move_to(cab.get_center() + UP * 0.6)
    sobE = Line(cab.get_center() + LEFT * 0.5 + UP * 0.28, cab.get_center() + LEFT * 0.2 + UP * 0.28, stroke_color=PT, stroke_width=6)
    sobD = Line(cab.get_center() + RIGHT * 0.2 + UP * 0.28, cab.get_center() + RIGHT * 0.5 + UP * 0.28, stroke_color=PT, stroke_width=6)
    oe = Dot(cab.get_center() + LEFT * 0.32 + UP * 0.05, radius=0.11, color=PT); od = Dot(cab.get_center() + RIGHT * 0.32 + UP * 0.05, radius=0.11, color=PT)
    big = RoundedRectangle(width=0.7, height=0.18, corner_radius=0.06, fill_color="#555", fill_opacity=1, stroke_width=0).move_to(cab.get_center() + DOWN * 0.28)
    boca = Line(cab.get_center() + DOWN * 0.5 + LEFT * 0.2, cab.get_center() + DOWN * 0.5 + RIGHT * 0.2, stroke_color=PT, stroke_width=6)
    pesc = Line(cab.get_bottom(), cab.get_bottom() + DOWN * 0.2, stroke_color=PT, stroke_width=15)
    t = pesc.get_end()
    cam = Polygon(t + LEFT * 0.55, t + RIGHT * 0.55, t + DOWN * 1.5 + RIGHT * 0.8, t + DOWN * 1.5 + LEFT * 0.8, fill_color="#26356b", fill_opacity=1, stroke_color=PT, stroke_width=10)
    gola = VGroup(Line(t + LEFT * 0.2, t + DOWN * 0.35, stroke_color=PT, stroke_width=6), Line(t + RIGHT * 0.2, t + DOWN * 0.35, stroke_color=PT, stroke_width=6))
    estrela = Star(n=6, outer_radius=0.16, fill_color=AMAR, fill_opacity=1, stroke_width=0).move_to(t + DOWN * 0.6 + LEFT * 0.3)
    omb = t + DOWN * 0.2
    be = Line(omb + LEFT * 0.4, omb + DOWN * 0.9 + LEFT * 0.55, stroke_color=PT, stroke_width=15)
    bd = Line(omb + RIGHT * 0.4, omb + DOWN * 0.9 + RIGHT * 0.55, stroke_color=PT, stroke_width=15)
    q = t + DOWN * 1.5
    pe = Line(q + LEFT * 0.3, q + DOWN * 1.2 + LEFT * 0.5, stroke_color=PT, stroke_width=15); pd = Line(q + RIGHT * 0.3, q + DOWN * 1.2 + RIGHT * 0.5, stroke_color=PT, stroke_width=15)
    grupo = VGroup(pesc, cam, gola, estrela, pe, pd, be, bd, cab, copa, aba, dist, sobE, sobD, oe, od, big, boca)
    return dict(grupo=grupo, cab=cab, oe=oe, od=od, boca=boca)


def filha():
    """Mulher jovem, cabelo castanho com rabo de cavalo, blusa teal, sem óculos."""
    cabelo = Circle(radius=1.0, fill_color="#6b4a2f", fill_opacity=1, stroke_color=PT, stroke_width=9).shift(UP * 1.5)
    rabo = Ellipse(width=0.5, height=1.1, fill_color="#6b4a2f", fill_opacity=1, stroke_color=PT, stroke_width=7).move_to(cabelo.get_center() + RIGHT * 0.95 + DOWN * 0.2)
    cab = Circle(radius=0.9, stroke_color=PT, stroke_width=15, fill_color=WHITE, fill_opacity=1).shift(UP * 1.4)
    sE = Line(cab.get_center() + LEFT * 0.5 + UP * 0.3, cab.get_center() + LEFT * 0.15 + UP * 0.34, stroke_color=PT, stroke_width=6)
    sD = Line(cab.get_center() + RIGHT * 0.15 + UP * 0.34, cab.get_center() + RIGHT * 0.5 + UP * 0.3, stroke_color=PT, stroke_width=6)
    oe = Dot(cab.get_center() + LEFT * 0.3 + UP * 0.02, radius=0.12, color=PT); od = Dot(cab.get_center() + RIGHT * 0.3 + UP * 0.02, radius=0.12, color=PT)
    boca = Line(cab.get_center() + DOWN * 0.42 + LEFT * 0.18, cab.get_center() + DOWN * 0.42 + RIGHT * 0.18, stroke_color=PT, stroke_width=6)
    pesc = Line(cab.get_bottom(), cab.get_bottom() + DOWN * 0.2, stroke_color=PT, stroke_width=15); t = pesc.get_end()
    blusa = Polygon(t + LEFT * 0.4, t + RIGHT * 0.4, t + DOWN * 1.5 + RIGHT * 0.75, t + DOWN * 1.5 + LEFT * 0.75, fill_color="#2f8f8a", fill_opacity=1, stroke_color=PT, stroke_width=10)
    q = t + DOWN * 1.5
    pe = Line(q + LEFT * 0.3, q + DOWN * 1.3 + LEFT * 0.5, stroke_color=PT, stroke_width=15); pd = Line(q + RIGHT * 0.3, q + DOWN * 1.3 + RIGHT * 0.5, stroke_color=PT, stroke_width=15)
    omb = t + DOWN * 0.18
    be = Line(omb + LEFT * 0.35, omb + DOWN * 0.85 + LEFT * 0.55, stroke_color=PT, stroke_width=15); bd = Line(omb + RIGHT * 0.35, omb + DOWN * 0.85 + RIGHT * 0.55, stroke_color=PT, stroke_width=15)
    grupo = VGroup(pesc, blusa, pe, pd, be, bd, cabelo, rabo, cab, sE, sD, oe, od, boca)
    return dict(grupo=grupo, cab=cab, oe=oe, od=od, boca=boca)


# =====================================================================
#  OBJETOS
# =====================================================================
def mesa_pc():
    """Devolve (monitor_group, mesa, teclado_pc). Monitor tem tela verde 'matrix'."""
    mesa = Rectangle(width=6.5, height=1.6, fill_color="#3a2f28", fill_opacity=1, stroke_color=PT, stroke_width=8).to_edge(DOWN, buff=0.2)
    mon = RoundedRectangle(width=2.2, height=1.5, corner_radius=0.08, fill_color="#111", fill_opacity=1, stroke_color=PT, stroke_width=6).move_to(mesa.get_top() + UP * 0.75)
    scr = Rectangle(width=1.9, height=1.2, fill_color="#1c9c6b", fill_opacity=1, stroke_width=0).move_to(mon)
    txt = VGroup(*[Line(LEFT * 0.7, RIGHT * 0.6, stroke_color="#0c5c40", stroke_width=3).shift(UP * (0.4 - j * 0.22)) for j in range(5)]).move_to(scr)
    tec = RoundedRectangle(width=2.0, height=0.5, corner_radius=0.06, fill_color="#2a2a2a", fill_opacity=1, stroke_color=PT, stroke_width=4).move_to(mesa.get_top() + DOWN * 0.1 + RIGHT * 1.4)
    return VGroup(mon, scr, txt), mesa, tec


def teclado_telefone():
    """Dialpad grande de telefone. dict com grupo, tela, keys[0..11] (1,2,3,...,#).
    Ilumine keys[i][0] pra mostrar dígito sendo teclado."""
    corpo = RoundedRectangle(width=2.8, height=4.6, corner_radius=0.25, fill_color="#15161c", fill_opacity=1, stroke_color=PT, stroke_width=8)
    tela = RoundedRectangle(width=2.3, height=0.9, corner_radius=0.08, fill_color="#0e2a20", fill_opacity=1, stroke_width=0).move_to(corpo.get_top() + DOWN * 0.7)
    keys = VGroup(); labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]; kk = []
    for lab in labels:
        k = RoundedRectangle(width=0.62, height=0.5, corner_radius=0.1, fill_color="#2a2c36", fill_opacity=1, stroke_color="#444", stroke_width=3)
        t = Text(lab, font=FONTE, weight=BOLD, font_size=26, color=WHITE).move_to(k)
        kv = VGroup(k, t); keys.add(kv); kk.append(kv)
    keys.arrange_in_grid(rows=4, cols=3, buff=0.16).move_to(corpo.get_center() + DOWN * 0.55)
    return dict(grupo=VGroup(corpo, tela, keys), tela=tela, keys=kk)


def cartao(cor="#2a6ad0"):
    """Cartão de crédito com chip dourado."""
    c = RoundedRectangle(width=0.9, height=0.58, corner_radius=0.07, fill_color=cor, fill_opacity=1, stroke_color=PT, stroke_width=4)
    c.add(RoundedRectangle(width=0.22, height=0.16, corner_radius=0.03, fill_color=AMAR, fill_opacity=1, stroke_width=0).move_to(c.get_center() + LEFT * 0.25 + UP * 0.1))
    return c


def moto_motoboy():
    """Moto vermelha virada pra esquerda + motoboy de capacete sentado.
    Entra deslizando: MM.animate.shift(LEFT*6.2), rate_func=rush_into."""
    rr = 0.55
    tras = Circle(radius=rr, fill_color="#1c1c1c", fill_opacity=1, stroke_color=PT, stroke_width=6).shift(RIGHT * 1.1)
    frente = Circle(radius=rr, fill_color="#1c1c1c", fill_opacity=1, stroke_color=PT, stroke_width=6).shift(LEFT * 1.1)
    hub1 = Circle(radius=0.15, fill_color="#999", fill_opacity=1, stroke_width=0).move_to(tras); hub2 = Circle(radius=0.15, fill_color="#999", fill_opacity=1, stroke_width=0).move_to(frente)
    corpo = Polygon([1.1, 0.1, 0], [0.2, 0.5, 0], [-0.7, 0.5, 0], [-1.1, 0.15, 0], [-0.7, 0.0, 0], [0.2, 0.0, 0], fill_color="#c23a30", fill_opacity=1, stroke_color=PT, stroke_width=6)
    tanque = Polygon([-0.1, 0.5, 0], [0.5, 0.5, 0], [0.4, 0.75, 0], [0.0, 0.75, 0], fill_color="#a52a22", fill_opacity=1, stroke_color=PT, stroke_width=5)
    guidao = Line([-1.0, 0.3, 0], [-1.3, 0.75, 0], stroke_color=PT, stroke_width=7); guidao2 = Line([-1.3, 0.75, 0], [-1.1, 0.72, 0], stroke_color=PT, stroke_width=7)
    farol = Circle(radius=0.16, fill_color="#ffe08a", fill_opacity=1, stroke_color=PT, stroke_width=4).move_to([-1.25, 0.35, 0])
    moto = VGroup(tras, frente, hub1, hub2, corpo, tanque, guidao, guidao2, farol)
    corpo_m = Polygon([0.1, 0.55, 0], [0.7, 0.55, 0], [0.6, 1.5, 0], [0.2, 1.5, 0], fill_color="#2a3a55", fill_opacity=1, stroke_color=PT, stroke_width=6).shift(LEFT * 0.1)
    cab = Circle(radius=0.55, fill_color="#d23b30", fill_opacity=1, stroke_color=PT, stroke_width=7).move_to([0.3, 1.9, 0])
    visor = RoundedRectangle(width=0.6, height=0.28, corner_radius=0.08, fill_color="#223", fill_opacity=1, stroke_color=PT, stroke_width=4).move_to(cab.get_center() + DOWN * 0.05 + LEFT * 0.05)
    braco = Line([0.35, 1.3, 0], [-1.0, 0.75, 0], stroke_color="#2a3a55", stroke_width=16)
    mb = VGroup(corpo_m, braco, cab, visor)
    return VGroup(moto, mb)


def cctv():
    """Câmera de segurança com luz REC vermelha (rec = grupo[-1])."""
    base = Rectangle(width=0.3, height=0.5, fill_color="#333", fill_opacity=1, stroke_color=PT, stroke_width=4)
    corpo = Polygon([0.2, 0.2, 0], [1.4, 0.35, 0], [1.5, -0.1, 0], [0.25, -0.25, 0], fill_color="#d0d4dc", fill_opacity=1, stroke_color=PT, stroke_width=6).next_to(base, RIGHT, buff=0)
    lente = Circle(radius=0.22, fill_color="#111", fill_opacity=1, stroke_color=PT, stroke_width=6).move_to(corpo.get_right() + LEFT * 0.05)
    rec = Dot(radius=0.08, color=VERM).move_to(corpo.get_center() + UP * 0.05)
    return VGroup(base, corpo, lente, rec)


def algemas(pontoE, pontoD):
    """Par de algemas ligando dois pontos (as mãos do preso)."""
    return VGroup(Circle(radius=0.18, color="#bbb", stroke_width=6).move_to(pontoE),
                  Circle(radius=0.18, color="#bbb", stroke_width=6).move_to(pontoD),
                  Line(pontoE, pontoD, color="#bbb", stroke_width=4))
