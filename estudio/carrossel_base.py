"""Base do estúdio de carrosséis do @sabioefeliz — o que é comum a qualquer
direção de arte.

Aqui moram os tokens (medidas, paleta de apoio, tipografia com fallback), as
texturas, as primitivas de texto — quebra de linha, entrelinha e tracking, que
o Pillow não tem prontas — e componentes que sobrevivem a qualquer pele.

A pele que o canal usa está em estudio/carrossel.py.

    1. PALETA e TIPOGRAFIA .... tokens de design e busca de fontes
    2. TEXTURA ................ gradiente, grão, vinheta, brilho
    3. PRIMITIVAS ............. escrever com tracking, quebrar, parágrafo
    4. COMPONENTES ............ moldura, régua, ornamento, selo, avatar
"""
from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# =====================================================================
#  1. PALETA E TIPOGRAFIA
# =====================================================================
LARGURA, ALTURA = 1080, 1350

AZUL_FUNDO   = (14, 54, 63)      # #0e363f  fundo escuro, quase petróleo
AZUL_TOPO    = (23, 74, 86)      # #174a56  o azul do canal, usado no gradiente
CREME        = (247, 236, 214)   # #f7ecd6
CREME_CLARO  = (253, 247, 235)   # #fdf7eb
DOURADO      = (214, 168, 74)    # #d6a84a
DOURADO_SUAVE= (232, 200, 135)   # #e8c887
TINTA        = (20, 47, 54)      # #142f36  texto sobre creme
TINTA_SUAVE  = (79, 99, 105)

MARGEM = 92          # respiro externo
MOLDURA = 46         # distância do filete até a borda

# A dupla do canal: EB Garamond (serifada, para a palavra) e Montserrat
# (geométrica, para os rótulos). As duas saem de pacotes apt — fonts-ebgaramond
# e fonts-montserrat — então o que é aprovado aqui é idêntico ao que o runner
# do GitHub Actions gera. O EBGaramond12-Bold do Debian NÃO tem acentuação:
# por isso o display usa o Regular em corpo grande, que é o certo em serifada.
_BUSCA_FONTES = {
    "serif":         ["EBGaramond12-Regular.otf", "EBGaramond-Regular.ttf", "DejaVuSerif.ttf"],
    "serif_italic":  ["EBGaramond12-Italic.otf", "EBGaramond-Italic.ttf", "DejaVuSerif-Italic.ttf"],
    "serif_display": ["EBGaramond12-Regular.otf", "EBGaramond-Regular.ttf", "DejaVuSerif.ttf"],
    "sans_light":    ["Montserrat-Light.ttf", "Poppins-Light.ttf", "DejaVuSans.ttf"],
    "sans":          ["Montserrat-Regular.ttf", "Poppins-Regular.ttf", "DejaVuSans.ttf"],
    "sans_medium":   ["Montserrat-Medium.ttf", "Poppins-Medium.ttf", "DejaVuSans.ttf"],
    "sans_semi":     ["Montserrat-SemiBold.ttf", "Poppins-SemiBold.ttf", "DejaVuSans-Bold.ttf"],
    "sans_bold":     ["Montserrat-Bold.ttf", "Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"],
}
_RAIZES = [
    Path(__file__).resolve().parent.parent / "assets" / "fonts",
    Path("/usr/share/fonts"),
]
_cache_fonte: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _achar(nome: str) -> str | None:
    for raiz in _RAIZES:
        if not raiz.exists():
            continue
        for p in raiz.rglob(nome):
            return str(p)
    return None


def fonte(papel: str, tamanho: int) -> ImageFont.FreeTypeFont:
    """Devolve a melhor fonte disponível para o papel pedido.

    A ordem em _BUSCA_FONTES é a ordem de preferência: se a Poppins estiver
    em assets/fonts ela ganha; senão cai na Inter do sistema; no pior caso,
    DejaVu. O layout não muda — só o desenho das letras.
    """
    chave = (papel, tamanho)
    if chave in _cache_fonte:
        return _cache_fonte[chave]
    for nome in _BUSCA_FONTES[papel]:
        caminho = _achar(nome)
        if caminho:
            f = ImageFont.truetype(caminho, tamanho)
            _cache_fonte[chave] = f
            return f
    raise RuntimeError(f"nenhuma fonte encontrada para {papel}")


# =====================================================================
#  2. TEXTURA — o que tira o "chapado" do fundo
# =====================================================================
def gradiente(de: tuple, para: tuple, altura: int = ALTURA) -> Image.Image:
    faixa = Image.new("RGB", (1, altura))
    px = faixa.load()
    for y in range(altura):
        t = y / max(1, altura - 1)
        px[0, y] = tuple(int(de[i] + (para[i] - de[i]) * t) for i in range(3))
    return faixa.resize((LARGURA, altura), Image.BILINEAR)


def grao(img: Image.Image, forca: float = 7.0) -> Image.Image:
    """Ruído fino e monocromático. Sem isso o PNG chapado parece plástico."""
    r = random.Random(20260906)
    ruido = Image.new("L", (LARGURA // 2, ALTURA // 2))
    ruido.putdata([r.gauss(128, forca * 4) for _ in range(ruido.width * ruido.height)])
    ruido = ruido.resize((LARGURA, ALTURA), Image.BILINEAR)
    return Image.blend(img, Image.merge("RGB", (ruido, ruido, ruido)), forca / 100)


def vinheta(img: Image.Image, forca: float = 0.30) -> Image.Image:
    mascara = Image.new("L", (LARGURA, ALTURA), 0)
    d = ImageDraw.Draw(mascara)
    d.ellipse([-LARGURA * 0.35, -ALTURA * 0.22,
               LARGURA * 1.35, ALTURA * 1.22], fill=255)
    mascara = mascara.filter(ImageFilter.GaussianBlur(190))
    escuro = Image.new("RGB", (LARGURA, ALTURA), (0, 0, 0))
    return Image.composite(img, Image.blend(img, escuro, forca), mascara)


def brilho(img: Image.Image, centro: tuple[int, int], raio: int,
           cor: tuple = DOURADO, forca: float = 0.18) -> Image.Image:
    """Um halo suave — a 'luz da manhã' que o canal usa nos vídeos."""
    camada = Image.new("L", (LARGURA, ALTURA), 0)
    d = ImageDraw.Draw(camada)
    d.ellipse([centro[0] - raio, centro[1] - raio,
               centro[0] + raio, centro[1] + raio], fill=int(255 * forca))
    camada = camada.filter(ImageFilter.GaussianBlur(raio // 2))
    return Image.composite(Image.new("RGB", img.size, cor), img, camada)


# =====================================================================
#  3. PRIMITIVAS DE TEXTO
# =====================================================================
def _largura(d: ImageDraw.ImageDraw, txt: str, f, tracking: float = 0) -> float:
    if not tracking:
        return d.textlength(txt, font=f)
    return sum(d.textlength(c, font=f) for c in txt) + tracking * max(0, len(txt) - 1)


def escrever(d: ImageDraw.ImageDraw, xy, txt: str, f, cor,
             tracking: float = 0, ancora: str = "la"):
    """Desenha texto com tracking (espaçamento entre letras) opcional.

    O Pillow não tem letter-spacing, então em maiúsculas — onde o tracking
    largo faz toda a diferença — desenhamos caractere a caractere.
    """
    x, y = xy
    if not tracking:
        d.text((x, y), txt, font=f, fill=cor, anchor=ancora)
        return
    total = _largura(d, txt, f, tracking)
    if ancora[0] == "m":
        x -= total / 2
    elif ancora[0] == "r":
        x -= total
    va = "a" if len(ancora) < 2 else ancora[1]
    for c in txt:
        d.text((x, y), c, font=f, fill=cor, anchor="l" + va)
        x += d.textlength(c, font=f) + tracking


def quebrar(d: ImageDraw.ImageDraw, txt: str, f, largura: float,
            tracking: float = 0) -> list[str]:
    linhas, atual = [], ""
    for palavra in txt.split():
        teste = f"{atual} {palavra}".strip()
        if _largura(d, teste, f, tracking) <= largura or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def paragrafo(d: ImageDraw.ImageDraw, txt: str, f, cor, x: float, y: float,
              largura: float, entrelinha: float = 1.42,
              tracking: float = 0, alinhar: str = "centro") -> float:
    """Escreve um bloco e devolve o y final. Entrelinha em múltiplos do corpo."""
    linhas = quebrar(d, txt, f, largura, tracking)
    passo = f.size * entrelinha
    for i, linha in enumerate(linhas):
        yy = y + i * passo
        if alinhar == "centro":
            escrever(d, (x, yy), linha, f, cor, tracking, "ma")
        else:
            escrever(d, (x, yy), linha, f, cor, tracking, "la")
    return y + len(linhas) * passo


def altura_paragrafo(d, txt, f, largura, entrelinha=1.42, tracking=0) -> float:
    return len(quebrar(d, txt, f, largura, tracking)) * f.size * entrelinha


# =====================================================================
#  4. COMPONENTES
# =====================================================================
def moldura(d: ImageDraw.ImageDraw, cor=DOURADO, opacidade: int = 90,
            recuo: int = MOLDURA):
    """Filete fino. É ele que dá o ar de 'peça impressa' e não de print."""
    d.rectangle([recuo, recuo, LARGURA - recuo, ALTURA - recuo],
                outline=cor + (opacidade,), width=2)


def ornamento(d: ImageDraw.ImageDraw, x: float, y: float, r: float = 9,
              cor=DOURADO):
    """Losango de quatro pontas — o separador da marca."""
    d.polygon([(x, y - r), (x + r * 0.42, y), (x, y + r), (x - r * 0.42, y)], fill=cor)
    d.polygon([(x - r, y), (x, y - r * 0.42), (x + r, y), (x, y + r * 0.42)], fill=cor)


def regua(d: ImageDraw.ImageDraw, y: float, meia: float = 120, cor=DOURADO,
          com_ornamento: bool = True):
    cx = LARGURA / 2
    folga = 26 if com_ornamento else 0
    d.line([cx - meia, y, cx - folga, y], fill=cor, width=2)
    d.line([cx + folga, y, cx + meia, y], fill=cor, width=2)
    if com_ornamento:
        ornamento(d, cx, y, 9, cor)


def selo(d: ImageDraw.ImageDraw, y: float, texto: str, cor_texto=DOURADO,
         cor_traco=DOURADO, corpo: int = 27, tracking: float = 7.5):
    """Rótulo em maiúsculas dentro de uma cápsula de contorno fino."""
    f = fonte("sans_semi", corpo)
    txt = texto.upper()
    larg = _largura(d, txt, f, tracking)
    pad_x, alt = 30, corpo + 26
    caixa = [LARGURA / 2 - larg / 2 - pad_x, y - alt / 2,
             LARGURA / 2 + larg / 2 + pad_x, y + alt / 2]
    d.rounded_rectangle(caixa, radius=alt / 2, outline=cor_traco, width=2)
    escrever(d, (LARGURA / 2 + tracking / 2, y + 1), txt, f, cor_texto, tracking, "mm")


def progresso(d: ImageDraw.ImageDraw, i: int, n: int, y: float, cor=DOURADO):
    passo, r = 22, 4
    x0 = LARGURA / 2 - (n - 1) * passo / 2
    for k in range(n):
        x = x0 + k * passo
        if k == i:
            d.rounded_rectangle([x - 11, y - r, x + 11, y + r], radius=r, fill=cor)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=cor + (110,))


def rodape(d: ImageDraw.ImageDraw, i: int, n: int, cor=DOURADO,
           arraste: bool = True, dourado_pontos=None):
    """Assinatura + indicador de página. Nos fundos claros o texto vai em
    tinta suave (o dourado sobre creme some) e só os pontos ficam dourados."""
    y = ALTURA - 126
    progresso(d, i, n, y, dourado_pontos or cor)
    f = fonte("sans_medium", 24)
    escrever(d, (LARGURA / 2, y + 52), "@SABIOEFELIZ", f, cor + (205,), 6.5, "ma")
    if arraste and i < n - 1:
        fs = fonte("sans_medium", 23)
        escrever(d, (LARGURA - MOLDURA - 34, y + 4), "ARRASTE  →", fs,
                 cor + (185,), 3.5, "rm")


def avatar(base: Image.Image, centro: tuple[int, int], raio: int,
           caminho: str, anel=DOURADO):
    """O rosto do Sábio recortado em círculo, com anel dourado."""
    if not os.path.exists(caminho):
        return
    rosto = Image.open(caminho).convert("RGB").resize((raio * 2, raio * 2), Image.LANCZOS)
    mascara = Image.new("L", (raio * 2, raio * 2), 0)
    ImageDraw.Draw(mascara).ellipse([0, 0, raio * 2, raio * 2], fill=255)
    base.paste(rosto, (centro[0] - raio, centro[1] - raio), mascara)
    d = ImageDraw.Draw(base, "RGBA")
    d.ellipse([centro[0] - raio, centro[1] - raio,
               centro[0] + raio, centro[1] + raio], outline=anel, width=6)


def _tela(escura: bool) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    if escura:
        img = gradiente(AZUL_TOPO, AZUL_FUNDO)
        img = brilho(img, (LARGURA // 2, 250), 520, DOURADO, 0.16)
        img = vinheta(img, 0.34)
        img = grao(img, 6.5)
    else:
        img = gradiente(CREME_CLARO, CREME)
        img = vinheta(img, 0.10)
        img = grao(img, 5.0)
    return img, ImageDraw.Draw(img, "RGBA")


