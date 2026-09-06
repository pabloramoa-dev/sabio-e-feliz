"""Estúdio de carrosséis do @sabioefeliz — direção "Manhã", aprovada em
2026-09-06.

Um carrossel são sete imagens de 1080x1350 (4:5, o formato que ocupa mais
altura no feed): capa, versículo, três desdobramentos, pergunta e assinatura.
O motor é Pillow — peças estáticas não precisam do Manim, e assim o publicador
da tarde não carrega o motor de vídeo.

A pele continua o Reel: o mesmo Sábio, o areia da parede do cenário, o teal do
canal e o tijolo do suéter. Tipografia sans pesada (Montserrat) e conteúdo
dentro de cartões de cor sólida com canto bem arredondado.

As primitivas (fontes, texturas, texto com tracking) vêm de carrossel_base.py.

    python -m estudio.carrossel conteudo/carrosseis.json CAR-001 saida/
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from estudio.carrossel_base import (
    LARGURA, ALTURA, fonte, escrever, paragrafo, altura_paragrafo,
    _largura, grao, avatar,
)

# ---------------------------------------------------------------- paleta
AREIA        = (244, 227, 200)   # #f4e3c8  o bege da parede do cenário
AREIA_CLARA  = (250, 240, 223)
TEAL         = (23, 74, 86)      # #174a56
TEAL_ESCURO  = (16, 55, 64)
TIJOLO       = (163, 68, 60)     # #a3443c  o suéter do Sábio
DOURADO      = (214, 168, 74)
DOURADO_VIVO = (232, 183, 78)
BRANCO       = (255, 251, 244)
GRAFITE      = (46, 62, 66)
VERDE        = (58, 94, 74)      # a plantinha da mesa do cenário

# A capa alterna entre três cores da mesma casa. Sozinha, a capa é bonita;
# em sequência, é isso que impede a grade do perfil de virar uma parede só.
CORES_CAPA = [TEAL, TIJOLO, VERDE]

MARGEM = 84
RAIO = 54                        # o raio dos cartões — a assinatura da pele

_ROSTO = Path(__file__).resolve().parent.parent / "assets" / "marca" / "sabio-rosto.png"


# ------------------------------------------------------------ fundos
def fundo_areia() -> Image.Image:
    img = Image.new("RGB", (LARGURA, ALTURA), AREIA)
    return grao(img, 4.0)


# ------------------------------------------------------------ componentes
def cartao(img: Image.Image, caixa, cor, raio: int = RAIO, sombra: bool = True):
    """Bloco de cor sólida com canto arredondado e sombra difusa por baixo."""
    if sombra:
        camada = Image.new("L", (LARGURA, ALTURA), 0)
        ImageDraw.Draw(camada).rounded_rectangle(
            [caixa[0] + 6, caixa[1] + 16, caixa[2] + 6, caixa[3] + 18], radius=raio, fill=64)
        camada = camada.filter(ImageFilter.GaussianBlur(26))
        img.paste(Image.composite(Image.new("RGB", img.size, (30, 28, 24)), img, camada))
    ImageDraw.Draw(img).rounded_rectangle(caixa, radius=raio, fill=cor)


def pilula(d: ImageDraw.ImageDraw, y: float, texto: str, fundo=DOURADO,
           tinta=TEAL_ESCURO, corpo: int = 30, tracking: float = 4.0):
    f = fonte("sans_bold", corpo)
    txt = texto.upper()
    larg = _largura(d, txt, f, tracking)
    pad, alt = 38, corpo + 32
    d.rounded_rectangle([LARGURA / 2 - larg / 2 - pad, y - alt / 2,
                         LARGURA / 2 + larg / 2 + pad, y + alt / 2],
                        radius=alt / 2, fill=fundo)
    escrever(d, (LARGURA / 2 + tracking / 2, y + 2), txt, f, tinta, tracking, "mm")


def pontinhos(d: ImageDraw.ImageDraw, i: int, n: int, y: float, cor, apagado):
    passo, r = 20, 4
    x0 = LARGURA / 2 - (n - 1) * passo / 2
    for k in range(n):
        x = x0 + k * passo
        if k == i:
            d.rounded_rectangle([x - 10, y - r, x + 10, y + r], radius=r, fill=cor)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=apagado)


def rodape(img: Image.Image, i: int, n: int, claro: bool):
    d = ImageDraw.Draw(img, "RGBA")
    cor = BRANCO if claro else TEAL
    apagado = BRANCO + (110,) if claro else TEAL + (90,)
    y = ALTURA - 108
    pontinhos(d, i, n, y, cor, apagado)
    f = fonte("sans_bold", 25)
    escrever(d, (LARGURA / 2, y + 46), "@SABIOEFELIZ", f, cor + (215,), 6.0, "ma")
    if i < n - 1:
        fs = fonte("sans_semi", 23)
        escrever(d, (LARGURA - MARGEM, y + 4), "ARRASTE  →", fs, cor + (185,), 3.0, "rm")


# ------------------------------------------------------------ slides
def _disco(img: Image.Image, topo_cartao: float, maximo: int = 224,
           folga: int = 46, minimo: int = 118):
    """O Sábio em disco, dimensionado pelo espaço livre acima do cartão."""
    espaco = topo_cartao - folga - 40
    raio = int(max(minimo, min(maximo, espaco / 2)))
    centro_y = int(40 + espaco / 2)
    avatar(img, (LARGURA // 2, centro_y), raio, str(_ROSTO), DOURADO)


def cor_capa(job) -> tuple:
    """Cor do cartão da capa, presa ao id: o mesmo carrossel tem sempre a
    mesma cor, e a fila inteira sai alternada sem ninguém escolher à mão."""
    try:
        k = int(str(job["id"]).split("-")[-1]) - 1
    except (KeyError, ValueError):
        k = 0
    # o deslocamento por linha (k//3) evita que a grade de 3 colunas do
    # Instagram fique com faixas verticais de uma cor só — sai em diagonal
    return CORES_CAPA[(k + k // 3) % len(CORES_CAPA)]


def slide_capa(job, i, n):
    """Sábio em disco no alto, cartão de cor na base. O disco resolve o
    recorte do cenário (nada de emenda visível) e vira a marca da capa."""
    img = fundo_areia()
    d = ImageDraw.Draw(img, "RGBA")

    ft = fonte("sans_bold", 84)
    fk = fonte("sans_medium", 28)
    larg = LARGURA - 2 * MARGEM - 96
    h_tit = altura_paragrafo(d, job["titulo"], ft, larg, 1.18)
    h_gan = altura_paragrafo(d, job["gancho"], fk, larg - 30, 1.5)
    alto = 96 + h_tit + 34 + h_gan + 66
    topo = ALTURA - 176 - alto

    # O disco se ajusta ao que sobrou: título longo empurra o cartão para
    # cima, e o Sábio encolhe em vez de ser cortado.
    _disco(img, topo, maximo=224)
    cartao(img, [MARGEM - 20, topo, LARGURA - MARGEM + 20, topo + alto], cor_capa(job))

    d = ImageDraw.Draw(img, "RGBA")
    pilula(d, topo + 54, job["referencia_exibida"], DOURADO, TEAL_ESCURO, 26, 4.5)
    fim = paragrafo(d, job["titulo"], ft, BRANCO, LARGURA / 2, topo + 106, larg, 1.18)
    paragrafo(d, job["gancho"], fk, DOURADO_VIVO, LARGURA / 2, fim + 34, larg - 30, 1.5)

    rodape(img, i, n, claro=False)
    return img


def slide_versiculo(job, i, n):
    img = fundo_areia()
    d = ImageDraw.Draw(img, "RGBA")

    ft = fonte("sans_medium", 56)
    larg = LARGURA - 2 * MARGEM - 110
    h = altura_paragrafo(d, job["texto_biblico"], ft, larg, 1.52)
    alto = h + 300
    topo = (ALTURA - 120 - alto) / 2
    cartao(img, [MARGEM, topo, LARGURA - MARGEM, topo + alto], TEAL)

    d = ImageDraw.Draw(img, "RGBA")
    fa = fonte("sans_bold", 150)
    escrever(d, (LARGURA / 2, topo + 44), "“", fa, DOURADO + (190,), 0, "ma")
    fim = paragrafo(d, job["texto_biblico"], ft, BRANCO, LARGURA / 2,
                    topo + 172, larg, 1.52)
    pilula(d, fim + 78, job["referencia_exibida"], DOURADO, TEAL_ESCURO, 28, 4.5)

    rodape(img, i, n, claro=False)
    return img


def slide_ponto(job, ponto, ordem, i, n):
    img = fundo_areia()
    d = ImageDraw.Draw(img, "RGBA")

    ft = fonte("sans_bold", 66)
    fc = fonte("sans_medium", 44)
    larg = LARGURA - 2 * MARGEM - 120

    h_tit = altura_paragrafo(d, ponto["titulo"], ft, larg, 1.22)
    h_cor = altura_paragrafo(d, ponto["corpo"], fc, larg, 1.58)
    alto = 200 + h_tit + 44 + h_cor + 100
    topo = (ALTURA - 120 - alto) / 2
    cartao(img, [MARGEM, topo, LARGURA - MARGEM, topo + alto], AREIA_CLARA)

    d = ImageDraw.Draw(img, "RGBA")
    cx, cy, r = LARGURA / 2, topo + 96, 62
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DOURADO)
    fnum = fonte("sans_bold", 60)
    escrever(d, (cx, cy + 2), f"{ordem}", fnum, TEAL_ESCURO, 0, "mm")

    fk = fonte("sans_bold", 24)
    escrever(d, (cx, topo + 190), ponto["etiqueta"].upper(), fk, TIJOLO, 6.5, "ma")

    fim = paragrafo(d, ponto["titulo"], ft, TEAL_ESCURO, cx, topo + 246, larg, 1.22)
    paragrafo(d, ponto["corpo"], fc, GRAFITE, cx, fim + 44, larg, 1.58)

    rodape(img, i, n, claro=False)
    return img


def slide_pergunta(job, i, n):
    img = Image.new("RGB", (LARGURA, ALTURA), TIJOLO)
    img = grao(img, 5.0)
    d = ImageDraw.Draw(img, "RGBA")

    pilula(d, 250, "pergunta de hoje", DOURADO_VIVO, TEAL_ESCURO, 28, 5.0)

    ft = fonte("sans_bold", 76)
    larg = LARGURA - 2 * MARGEM - 40
    h = altura_paragrafo(d, job["pergunta"], ft, larg, 1.28)
    paragrafo(d, job["pergunta"], ft, BRANCO, LARGURA / 2, 660 - h / 2, larg, 1.28)

    rodape(img, i, n, claro=True)
    return img


def slide_assinatura(job, i, n):
    img = fundo_areia()
    d = ImageDraw.Draw(img, "RGBA")

    ft = fonte("sans_bold", 70)
    fs = fonte("sans_medium", 29)
    larg = LARGURA - 2 * MARGEM - 96
    h_cta = altura_paragrafo(d, job["cta"], ft, larg, 1.22)
    h_sub = altura_paragrafo(d, "Salve para reler amanhã e mande para quem precisa ouvir isso hoje.",
                             fs, larg - 40, 1.5)
    alto = 58 + h_cta + 34 + h_sub + 96
    topo = ALTURA - 176 - alto
    _disco(img, topo, maximo=190)
    cartao(img, [MARGEM - 20, topo, LARGURA - MARGEM + 20, topo + alto], TEAL)

    d = ImageDraw.Draw(img, "RGBA")
    fim = paragrafo(d, job["cta"], ft, BRANCO, LARGURA / 2, topo + 58, larg, 1.22)
    paragrafo(d, "Salve para reler amanhã e mande para quem precisa ouvir isso hoje.",
              fs, DOURADO_VIVO, LARGURA / 2, fim + 34, larg - 40, 1.5)
    ff = fonte("sans", 20)
    paragrafo(d, "Texto bíblico: João Ferreira de Almeida, domínio público.",
              ff, BRANCO + (150,), LARGURA / 2, fim + 34 + h_sub + 22, larg, 1.4)

    rodape(img, i, n, claro=False)
    return img


def slide_leitura(job, verso, ordem, i, n):
    """Um versículo por slide, no formato D. Sem paráfrase: o cartão traz o
    texto bíblico e a referência exata, e nada mais."""
    img = fundo_areia()
    d = ImageDraw.Draw(img, "RGBA")

    ft = fonte("sans_medium", 50)
    larg = LARGURA - 2 * MARGEM - 110
    h = altura_paragrafo(d, verso["texto"], ft, larg, 1.54)
    alto = h + 330
    topo = (ALTURA - 120 - alto) / 2
    cor = CORES_CAPA[(ordem - 1) % len(CORES_CAPA)]
    cartao(img, [MARGEM, topo, LARGURA - MARGEM, topo + alto], cor)

    d = ImageDraw.Draw(img, "RGBA")
    cx, cy, r = LARGURA / 2, topo + 88, 52
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DOURADO)
    escrever(d, (cx, cy + 2), str(ordem), fonte("sans_bold", 52), TEAL_ESCURO, 0, "mm")

    fim = paragrafo(d, verso["texto"], ft, BRANCO, cx, topo + 172, larg, 1.54)
    pilula(d, fim + 76, verso["referencia"], DOURADO, TEAL_ESCURO, 26, 4.0)

    rodape(img, i, n, claro=False)
    return img


# ------------------------------------------------------------ montagem
def montar(job):
    if job.get("formato") == "D":
        versos = job["versiculos"]
        total = len(versos) + 2
        paginas = [slide_capa(job, 0, total)]
        for k, verso in enumerate(versos):
            paginas.append(slide_leitura(job, verso, k + 1, 1 + k, total))
        paginas.append(slide_assinatura(job, total - 1, total))
        return paginas

    pontos = job["pontos"]
    total = 3 + len(pontos) + 1
    paginas = [slide_capa(job, 0, total), slide_versiculo(job, 1, total)]
    for k, ponto in enumerate(pontos):
        paginas.append(slide_ponto(job, ponto, k + 1, 2 + k, total))
    paginas.append(slide_pergunta(job, 2 + len(pontos), total))
    paginas.append(slide_assinatura(job, 3 + len(pontos), total))
    return paginas


def gravar(job, destino):
    Path(destino).mkdir(parents=True, exist_ok=True)
    saidas = []
    for k, img in enumerate(montar(job), start=1):
        caminho = os.path.join(destino, f"{job['id']}-{k:02d}.jpg")
        img.convert("RGB").save(caminho, "JPEG", quality=93, subsampling=0,
                                optimize=True, progressive=True)
        saidas.append(caminho)
    return saidas


if __name__ == "__main__":
    dados = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if isinstance(dados, dict) and "carrosseis" in dados:
        itens = dados["carrosseis"]
    elif isinstance(dados, dict):
        itens = [dados]
    else:
        itens = dados
    alvo = next((a for a in sys.argv[2:] if a.startswith("CAR-")), None)
    destino = next((a for a in sys.argv[2:] if not a.startswith("CAR-")), "output/carrossel")
    for item in itens:
        if alvo and item["id"] != alvo:
            continue
        for caminho in gravar(item, os.path.join(destino, item["id"])):
            print(caminho)
