"""O Sábio — personagem do canal @sabioefeliz.

Mesma família visual dos outros canais do Pablo: cabeça grande, traço grosso,
identidade por acessório (barba grisalha curta, óculos redondos, colete
azul-petróleo e o livrinho dourado) e nunca por anatomia.

Tudo é desenhado por código: custo zero, sem IA de imagem, personagem
sempre idêntico entre um episódio e outro.
"""
from __future__ import annotations

import math

from PIL import ImageDraw

from estudio.paleta import *

# --- geometria fixa ---------------------------------------------------------
CX, CY = 540, 900          # centro da cabeça
R = 205                    # raio da cabeça
OMBRO_Y = CY + R + 120
BASE_TRONCO = 1620

EXPRESSOES = {
    "acolhimento": {"sobrancelha": 0, "boca_curva": 14, "olho": 1.0},
    "reflexao":    {"sobrancelha": -10, "boca_curva": 2, "olho": 0.85},
    "alerta":      {"sobrancelha": -18, "boca_curva": -6, "olho": 1.1},
    "duvida":      {"sobrancelha": -14, "boca_curva": 0, "olho": 0.95},
    "alegria":     {"sobrancelha": 8, "boca_curva": 26, "olho": 0.9},
    "surpresa":    {"sobrancelha": 22, "boca_curva": 6, "olho": 1.2},
    "seriedade":   {"sobrancelha": -6, "boca_curva": -2, "olho": 0.95},
    "paz":         {"sobrancelha": 4, "boca_curva": 18, "olho": 0.9},
}


def desenhar(
    tela,
    boca: float = 0.0,
    piscada: float = 0.0,
    expressao: str = "acolhimento",
    gesto: str = "livro",
    respiracao: float = 0.0,
    olhar: tuple[float, float] = (0.0, 0.0),
):
    """Desenha o Sábio sobre `tela` (PIL Image em RGB).

    boca: 0 fechada, 1 totalmente aberta (vem da amplitude do áudio)
    piscada: 0 olhos abertos, 1 olhos fechados
    respiracao: -1..1, sobe e desce o tronco alguns pixels
    """
    d = ImageDraw.Draw(tela, "RGBA")
    e = EXPRESSOES.get(expressao, EXPRESSOES["acolhimento"])
    dy = int(respiracao * 8)
    cy = CY + dy

    # --- tronco -------------------------------------------------------------
    ombro_y = OMBRO_Y + dy
    d.polygon(
        [(CX - 330, BASE_TRONCO), (CX - 250, ombro_y + 30), (CX - 120, ombro_y - 10),
         (CX + 120, ombro_y - 10), (CX + 250, ombro_y + 30), (CX + 330, BASE_TRONCO)],
        fill=AZUL_PETROLEO, outline=CONTORNO, width=TRACO,
    )
    # camisa creme aparecendo no V do colete
    d.polygon(
        [(CX - 105, ombro_y + 5), (CX + 105, ombro_y + 5), (CX + 40, ombro_y + 210),
         (CX - 40, ombro_y + 210)],
        fill=CREME, outline=CONTORNO, width=TRACO,
    )
    # pingente dourado discreto
    d.ellipse([CX - 22, ombro_y + 150, CX + 22, ombro_y + 194], fill=DOURADO, outline=CONTORNO, width=8)

    # --- pescoço ------------------------------------------------------------
    d.rounded_rectangle([CX - 62, cy + R - 60, CX + 62, ombro_y + 20], 24,
                        fill=PELE_SOMBRA, outline=CONTORNO, width=TRACO)

    # --- braços e gesto -----------------------------------------------------
    _gesto(d, gesto, ombro_y)

    # --- cabeça -------------------------------------------------------------
    d.ellipse([CX - R, cy - R, CX + R, cy + R], fill=PELE, outline=CONTORNO, width=TRACO)
    # orelhas
    for lado in (-1, 1):
        d.ellipse([CX + lado * R - 26, cy - 34, CX + lado * R + 26, cy + 54],
                  fill=PELE, outline=CONTORNO, width=TRACO)

    # --- cabelo grisalho: faixa de têmpora a têmpora, testa livre -----------
    d.pieslice([CX - R, cy - R, CX + R, cy + R], 182, 358, fill=GRISALHO,
               outline=CONTORNO, width=TRACO)
    d.pieslice([CX - R + 44, cy - R + 54, CX + R - 44, cy + R + 54], 182, 358, fill=PELE)
    d.arc([CX - R + 44, cy - R + 54, CX + R - 44, cy + R + 54], 190, 350,
          fill=CONTORNO, width=10)

    # --- barba grisalha curta: queixo e maxilar, bochechas livres -----------
    d.ellipse([CX - 156, cy + 46, CX + 156, cy + R + 16], fill=GRISALHO,
              outline=CONTORNO, width=TRACO)

    # --- nariz --------------------------------------------------------------
    d.line([(CX, cy - 2), (CX - 6, cy + 44)], fill=PELE_SOMBRA, width=12)
    d.arc([CX - 34, cy + 6, CX + 24, cy + 62], 30, 175, fill=PELE_SOMBRA, width=12)

    # --- bigode -------------------------------------------------------------
    d.pieslice([CX - 84, cy + 56, CX + 84, cy + 132], 184, 356,
               fill=GRISALHO_ESCURO, outline=CONTORNO, width=8)

    # --- olhos --------------------------------------------------------------
    ox, oy = 78, 24
    altura = max(4, int(46 * e["olho"] * (1 - piscada)))
    for lado in (-1, 1):
        ex = CX + lado * ox
        ey = cy - oy
        d.ellipse([ex - 40, ey - altura, ex + 40, ey + altura], fill=BRANCO, outline=CONTORNO, width=9)
        if piscada < 0.6:
            px = ex + int(olhar[0] * 12)
            py = ey + int(olhar[1] * 8)
            d.ellipse([px - 17, py - 17, px + 17, py + 17], fill=CONTORNO)

    # --- sobrancelhas -------------------------------------------------------
    sob = int(e["sobrancelha"])
    for lado in (-1, 1):
        ex = CX + lado * ox
        d.line([(ex - 46, cy - oy - 92 - sob + (7 if lado < 0 else 0)),
                (ex + 46, cy - oy - 98 - sob + (0 if lado < 0 else 7))],
               fill=GRISALHO_ESCURO, width=15)

    # --- óculos redondos ----------------------------------------------------
    for lado in (-1, 1):
        ex = CX + lado * ox
        d.ellipse([ex - 56, cy - oy - 50, ex + 56, cy - oy + 58], outline=(72, 62, 52), width=9)
    d.line([(CX - 20, cy - oy + 4), (CX + 20, cy - oy + 4)], fill=(72, 62, 52), width=9)

    # --- boca ---------------------------------------------------------------
    abertura = max(0.0, min(1.0, boca))
    by = cy + 142
    if abertura < 0.08:
        curva = e["boca_curva"]
        d.arc([CX - 52, by - 26 - curva, CX + 52, by + 26], 20, 160, fill=(108, 52, 48), width=13)
    else:
        h = int(12 + 52 * abertura)
        w = int(46 + 14 * abertura)
        d.ellipse([CX - w, by - h // 2, CX + w, by + h // 2], fill=(112, 56, 52), outline=CONTORNO, width=8)
        if abertura > 0.45:  # língua só na vogal aberta
            d.ellipse([CX - w + 16, by + h // 6, CX + w - 16, by + h // 2 - 4], fill=(178, 92, 96))

    return tela


def _gesto(d, gesto: str, ombro_y: int) -> None:
    """Braços. Um gesto por cena; repouso no fim."""
    if gesto == "livro":
        # braços descendo do ombro até as mãos
        for lado in (-1, 1):
            d.line([(CX + lado * 235, ombro_y + 60), (CX + lado * 205, ombro_y + 300)],
                   fill=AZUL_ESCURO, width=70)
        # mãos segurando o livrinho dourado
        lx0, ly0, lx1, ly1 = CX - 142, ombro_y + 240, CX + 142, ombro_y + 366
        d.rounded_rectangle([lx0, ly0, lx1, ly1], 16, fill=DOURADO, outline=CONTORNO, width=TRACO)
        d.rounded_rectangle([lx0 + 14, ly0 + 14, lx1 - 14, ly1 - 14], 10, fill=CREME, outline=CONTORNO, width=8)
        d.line([(CX, ly0 + 14), (CX, ly1 - 14)], fill=CONTORNO, width=8)
        for lado in (-1, 1):
            d.ellipse([CX + lado * 162 - 46, ly0 + 20, CX + lado * 162 + 46, ly0 + 108],
                      fill=PELE, outline=CONTORNO, width=TRACO)
    elif gesto == "apontar":
        d.line([(CX + 236, ombro_y + 90), (CX + 300, ombro_y - 30)], fill=AZUL_ESCURO, width=72)
        d.line([(CX + 300, ombro_y - 30), (CX + 250, ombro_y - 190)], fill=PELE_SOMBRA, width=58)
        d.ellipse([CX + 196, ombro_y - 258, CX + 306, ombro_y - 148], fill=PELE,
                  outline=CONTORNO, width=TRACO)
        d.line([(CX + 250, ombro_y - 210), (CX + 250, ombro_y - 300)], fill=PELE, width=34)
        d.ellipse([CX + 233, ombro_y - 318, CX + 267, ombro_y - 284], fill=PELE,
                  outline=CONTORNO, width=8)
    elif gesto == "coracao":
        d.line([(CX - 246, ombro_y + 80), (CX - 70, ombro_y + 232)], fill=AZUL_ESCURO, width=70)
        d.ellipse([CX - 128, ombro_y + 186, CX - 8, ombro_y + 300], fill=PELE,
                  outline=CONTORNO, width=TRACO)
    elif gesto == "explicando":
        for lado in (-1, 1):
            d.line([(CX + lado * 250, ombro_y + 70), (CX + lado * 330, ombro_y + 190)],
                   fill=AZUL_ESCURO, width=60)
            d.ellipse([CX + lado * 330 - 48, ombro_y + 150, CX + lado * 330 + 48, ombro_y + 246],
                      fill=PELE, outline=CONTORNO, width=TRACO)
    # "repouso": nada além do tronco
