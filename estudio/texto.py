"""Cartela, selo de referência e legenda karaokê palavra por palavra."""
from __future__ import annotations

from pathlib import Path

from PIL import ImageDraw, ImageFont

from estudio.paleta import *

CANDIDATOS_FONTE = [
    Path(__file__).resolve().parent.parent / "assets/fonts/Fonte-Bold.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
]
_cache: dict[int, ImageFont.FreeTypeFont] = {}


def fonte(tamanho: int) -> ImageFont.FreeTypeFont:
    if tamanho not in _cache:
        for c in CANDIDATOS_FONTE:
            if c.exists():
                _cache[tamanho] = ImageFont.truetype(str(c), tamanho)
                break
        else:  # pragma: no cover
            _cache[tamanho] = ImageFont.load_default(tamanho)
    return _cache[tamanho]


def _largura(d: ImageDraw.ImageDraw, txt: str, f) -> int:
    return int(d.textlength(txt, font=f))


def quebrar(d, palavras: list[str], f, largura_max: int) -> list[list[int]]:
    """Agrupa índices de palavras em linhas que cabem na largura."""
    linhas: list[list[int]] = []
    atual: list[int] = []
    for i, p in enumerate(palavras):
        teste = " ".join(palavras[j] for j in atual + [i])
        if atual and _largura(d, teste, f) > largura_max:
            linhas.append(atual)
            atual = [i]
        else:
            atual.append(i)
    if atual:
        linhas.append(atual)
    return linhas


def blocos_legenda(tela_ref, palavras: list[dict], por_bloco: int = 7) -> list[dict]:
    """Divide a fala em blocos curtos de no máximo duas linhas."""
    d = ImageDraw.Draw(tela_ref)
    f = fonte(64)
    blocos = []
    i = 0
    while i < len(palavras):
        pedaco = palavras[i:i + por_bloco]
        textos = [p["texto"] for p in pedaco]
        linhas = quebrar(d, textos, f, L - 200)
        while len(linhas) > 2 and len(pedaco) > 2:
            pedaco = pedaco[:-1]
            textos = [p["texto"] for p in pedaco]
            linhas = quebrar(d, textos, f, L - 200)
        blocos.append({
            "inicio": pedaco[0]["inicio"],
            "fim": pedaco[-1]["fim"],
            "palavras": pedaco,
            "linhas": linhas,
        })
        i += len(pedaco)
    return blocos


def desenhar_legenda(tela, bloco: dict, t: float) -> None:
    """Legenda karaokê: banda escura no terço central, palavra atual em dourado."""
    d = ImageDraw.Draw(tela, "RGBA")
    f = fonte(64)
    palavras = bloco["palavras"]
    linhas = bloco["linhas"]
    altura_linha = 84
    total = len(linhas) * altura_linha
    topo = CENTRO_LEGENDA - total // 2

    d.rounded_rectangle(
        [70, topo - 34, L - 70, topo + total + 26], 28, fill=(24, 26, 30, 205)
    )

    for n, indices in enumerate(linhas):
        textos = [palavras[i]["texto"] for i in indices]
        largura = _largura(d, " ".join(textos), f)
        x = (L - largura) // 2
        y = topo + n * altura_linha
        for i in indices:
            palavra = palavras[i]["texto"]
            ativa = palavras[i]["inicio"] <= t <= palavras[i]["fim"] + 0.05
            d.text((x, y), palavra, font=f, fill=DOURADO_CLARO if ativa else BRANCO)
            x += _largura(d, palavra + " ", f)


def desenhar_cartela(tela, titulo: str, alpha: float) -> None:
    """Cartela com o assunto do episódio — é o frame que aparece na grade."""
    if alpha <= 0.01:
        return
    d = ImageDraw.Draw(tela, "RGBA")
    a = int(255 * min(alpha, 1.0))
    f = fonte(78)
    linhas = quebrar(d, titulo.upper().split(), f, L - 260)
    altura = len(linhas) * 96
    topo = 300

    d.rounded_rectangle([90, topo - 46, L - 90, topo + altura + 30], 30,
                        fill=(23, 74, 86, int(a * 0.92)))
    d.rounded_rectangle([90, topo - 46, L - 90, topo + altura + 30], 30,
                        outline=(214, 168, 74, a), width=8)
    for n, indices in enumerate(linhas):
        txt = " ".join(titulo.upper().split()[i] for i in indices)
        largura = _largura(d, txt, f)
        d.text(((L - largura) // 2, topo + n * 96), txt, font=f, fill=(255, 255, 255, a))


def desenhar_selo(tela, referencia: str, alpha: float) -> None:
    """Selo com a referência bíblica, visível durante a leitura da passagem."""
    if alpha <= 0.01:
        return
    d = ImageDraw.Draw(tela, "RGBA")
    a = int(255 * min(alpha, 1.0))
    f = fonte(52)
    largura = _largura(d, referencia, f)
    x0 = (L - largura) // 2 - 44
    y0 = 250
    d.rounded_rectangle([x0, y0, x0 + largura + 88, y0 + 92], 46,
                        fill=(214, 168, 74, a), outline=(26, 28, 32, a), width=7)
    d.text((x0 + 44, y0 + 18), referencia, font=f, fill=(26, 28, 32, a))


def desenhar_assinatura(tela) -> None:
    d = ImageDraw.Draw(tela, "RGBA")
    f = fonte(38)
    txt = "@sabioefeliz"
    largura = _largura(d, txt, f)
    d.text(((L - largura) // 2, A - 322), txt, font=f, fill=(255, 255, 255, 205))
