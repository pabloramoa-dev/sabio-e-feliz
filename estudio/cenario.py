"""Fundo da manhã: parede, janela com luz, mesa, planta e caneca."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

from estudio.paleta import *


def _gradiente(tela: Image.Image) -> None:
    topo = (253, 232, 201)
    base = (233, 197, 156)
    d = ImageDraw.Draw(tela)
    for y in range(A):
        t = y / A
        cor = tuple(int(topo[i] + (base[i] - topo[i]) * t) for i in range(3))
        d.line([(0, y), (L, y)], fill=cor)


_BASE: Image.Image | None = None


def base_estatica() -> Image.Image:
    """Parte imóvel do cenário — desenhada uma vez e reaproveitada."""
    global _BASE
    if _BASE is None:
        _BASE = _construir()
    return _BASE.copy()


def _construir() -> Image.Image:
    """Cenário estático + partículas de luz que se movem com o quadro."""
    quadro = 0
    tela = Image.new("RGB", (L, A), AZUL_PETROLEO)
    _gradiente(tela)
    d = ImageDraw.Draw(tela, "RGBA")

    # --- janela ------------------------------------------------------------
    jx0, jy0, jx1, jy1 = 620, 300, 1020, 790
    d.rounded_rectangle([jx0, jy0, jx1, jy1], 24, fill=(212, 176, 132), outline=CONTORNO, width=TRACO)
    d.rounded_rectangle([jx0 + 20, jy0 + 20, jx1 - 20, jy1 - 20], 14, fill=(176, 214, 226))
    # sol nascendo
    d.ellipse([jx0 + 95, jy0 + 190, jx0 + 305, jy0 + 400], fill=SOL)
    d.line([(jx0 + (jx1 - jx0) // 2, jy0), (jx0 + (jx1 - jx0) // 2, jy1)], fill=CONTORNO, width=TRACO)
    d.line([(jx0, jy0 + (jy1 - jy0) // 2), (jx1, jy0 + (jy1 - jy0) // 2)], fill=CONTORNO, width=TRACO)

    # feixe de luz entrando
    feixe = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    df = ImageDraw.Draw(feixe)
    df.polygon([(jx0, jy1), (jx1, jy1), (jx1 + 150, A), (jx0 - 320, A)], fill=(255, 236, 178, 70))
    feixe = feixe.filter(ImageFilter.GaussianBlur(40))
    tela = Image.alpha_composite(tela.convert("RGBA"), feixe).convert("RGB")
    d = ImageDraw.Draw(tela, "RGBA")

    # --- mesa --------------------------------------------------------------
    my = 1585
    d.rectangle([0, my, L, my + 40], fill=MADEIRA, outline=CONTORNO, width=TRACO)
    d.rectangle([0, my + 40, L, A], fill=(126, 88, 60))

    # --- planta (esquerda) --------------------------------------------------
    d.rounded_rectangle([70, my - 150, 220, my], 18, fill=CREME_ESCURO, outline=CONTORNO, width=TRACO)
    for ang, dx, dy in ((0, 0, -170), (1, -85, -120), (2, 85, -125)):
        cx = 145 + dx
        d.ellipse([cx - 52, my - 150 + dy, cx + 52, my - 150 + dy + 130],
                  fill=VERDE_PLANTA, outline=CONTORNO, width=TRACO)

    # --- caneca (direita) ---------------------------------------------------
    d.rounded_rectangle([880, my - 130, 1010, my], 16, fill=CREME, outline=CONTORNO, width=TRACO)
    d.arc([995, my - 108, 1065, my - 40], -90, 90, fill=CONTORNO, width=TRACO)
    return tela


MESA_Y = 1585


def animar(tela: Image.Image, quadro: int) -> Image.Image:
    """Vapor da caneca e poeira de luz — a parte que se move."""
    import math

    d = ImageDraw.Draw(tela, "RGBA")
    my = MESA_Y
    for i in range(3):
        deslocamento = (quadro * 1.6 + i * 34) % 100
        y = my - 140 - deslocamento
        alpha = int(150 * (1 - deslocamento / 100))
        d.arc([905 + i * 30, y - 40, 945 + i * 30, y + 10], 200, 340,
              fill=(255, 255, 255, alpha), width=7)

    for i in range(14):
        px = (i * 137 + quadro * 0.6) % L
        py = 420 + (i * 211 + quadro * 0.9) % 950
        r = 3 + (i % 3) * 2
        a = int(70 + 50 * math.sin((quadro / 18.0) + i))
        d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 250, 220, max(a, 0)))
    return tela


def desenhar(quadro: int = 0) -> Image.Image:
    return animar(base_estatica(), quadro)
