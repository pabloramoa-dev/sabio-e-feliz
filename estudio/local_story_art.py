"""Ilustrações pictográficas locais para vídeo avulso sem chave de imagem.
Imagens originais, sem textos e sem dependências de rede. Não simula foto real.
"""
from __future__ import annotations
import io
import math
from PIL import Image, ImageDraw, ImageFilter

INK = '#34293d'
CREAM = '#fff3dd'
PINK = '#f47783'
GOLD = '#ffcc55'
BLUE = '#4d9dbb'
LIGHT = '#e2f2f5'
MINT = '#73bea8'


def icon(kind):
    im = Image.new('RGBA', (600, 600), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    def rr(box, fill, radius=25, outline=INK, width=9):
        d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    def oval(box, fill, outline=INK, width=8):
        d.ellipse(box, fill=fill, outline=outline, width=width)
    def poly(coords, fill, outline=INK, width=8):
        d.polygon(coords, fill=fill)
        d.line(list(coords)+[coords[0]], fill=outline, width=width, joint='curve')

    if kind in ('phone', 'call', 'message'):
        rr((173, 54, 424, 543), '#fcfbf5', 38)
        rr((195, 108, 401, 452), LIGHT, 18, BLUE, 4)
        d.rounded_rectangle((253, 75, 344, 87), radius=5, fill=INK)
        oval((280, 479, 319, 518), GOLD, INK, 4)
        if kind == 'message':
            rr((221, 185, 375, 270), '#f7ffff', 28, MINT, 5)
            d.line([(249, 217), (340, 217)], fill=BLUE, width=12)
            d.line([(249, 242), (304, 242)], fill=PINK, width=10)
        else:
            oval((241, 205, 358, 321), GOLD, INK, 6)
            d.arc((260, 223, 338, 302), 30, 290, fill=INK, width=12)
            if kind == 'call':
                d.arc((109, 150, 488, 390), 215, 319, fill=PINK, width=13)
                d.arc((82, 110, 520, 430), 215, 325, fill=BLUE, width=12)
    elif kind in ('car','drive'):
        rr((82, 252, 515, 405), BLUE, 52)
        poly([(175, 253),(233, 169),(387, 169),(460, 253)], BLUE)
        rr((226, 189, 303, 252), LIGHT, 12, INK, 6)
        rr((313, 189, 382, 252), LIGHT, 12, INK, 6)
        oval((138, 369, 227, 459), INK, INK, 5)
        oval((371, 369, 460, 459), INK, INK, 5)
        oval((161, 392, 205, 436), CREAM, INK, 4)
        oval((394, 392, 438, 436), CREAM, INK, 4)
        rr((96, 290, 152, 319), GOLD, 10, INK, 4)
        rr((449, 290, 500, 319), GOLD, 10, INK, 4)
    elif kind in ('station','building'):
        poly([(97, 184),(299, 88),(506, 184)], PINK)
        rr((117, 184, 485, 472), CREAM, 15)
        for x in (147, 265, 385):
            rr((x, 225, x+77, 317), LIGHT, 15, BLUE, 5)
        rr((254, 342, 350, 472), GOLD, 8)
        d.line([(103,481),(501,481)], fill=INK, width=12)
    elif kind in ('gift','present'):
        rr((125, 249, 470, 482), PINK, 18)
        rr((101, 196, 496, 266), GOLD, 12)
        rr((261, 196, 332, 481), CREAM, 5, INK, 5)
        d.arc((190, 113, 303, 217), 200, 355, fill=INK, width=14)
        d.arc((290, 113, 399, 217), 183, 348, fill=INK, width=14)
        oval((276, 180, 322, 224), PINK)
    elif kind in ('home','house','door'):
        poly([(83, 284),(299, 110),(515, 284)], PINK)
        rr((128, 277, 473, 491), CREAM, 12)
        rr((255, 335, 347, 490), BLUE, 12)
        oval((320, 411, 334, 425), GOLD, INK, 3)
        rr((155, 337, 228, 403), LIGHT, 9, BLUE, 5)
        rr((375, 337, 447, 403), LIGHT, 9, BLUE, 5)
    elif kind in ('letter','note','document','receipt'):
        poly([(111, 208),(482, 208),(482, 461),(111, 461)], CREAM)
        poly([(111, 208),(294, 342),(482, 208)], LIGHT)
        d.line([(115,457),(298,320),(477,457)], fill=INK, width=8)
        rr((172, 98, 430, 286), '#fffdfa', 11, BLUE, 5)
        for y,l in ((151,195),(184,167),(219,180)):
            d.line([(213,y),(213+l,y)], fill=BLUE, width=13)
    elif kind in ('family','people','person','hug'):
        for x,color in ((138,BLUE),(331,PINK)):
            oval((x+38,117,x+141,220), CREAM)
            rr((x,232,x+181,467), color, 76)
            d.arc((x+37,144,x+140,218), 15, 165, fill=INK, width=4)
        if kind == 'hug':
            d.arc((152,246,450,481), 15, 155, fill=GOLD, width=21)
    elif kind in ('clock','time'):
        oval((92,101,507,520), CREAM)
        oval((116,125,484,495), LIGHT, INK, 4)
        for n in range(12):
            a=n*math.pi/6
            x=300+160*math.sin(a); y=308-160*math.cos(a)
            oval((x-7,y-7,x+7,y+7), GOLD, INK, 2)
        d.line([(300,308),(300,191)], fill=INK, width=15)
        d.line([(300,308),(385,355)], fill=INK, width=15)
        oval((282,290,317,325), PINK)
    elif kind in ('heart','love'):
        oval((144,189,322,366), PINK)
        oval((275,189,452,366), PINK)
        poly([(140,284),(302,481),(455,284)], PINK)
    elif kind in ('microphone','mic'):
        rr((232,105,375,339), PINK, 68)
        d.arc((187,203,419,450), 0, 180, fill=INK, width=16)
        d.line([(300,446),(300,511)], fill=INK, width=16)
        d.line([(233,511),(367,511)], fill=INK, width=16)
    elif kind in ('folder','files'):
        rr((79,210,521,451), GOLD, 21)
        rr((93,153,304,243), CREAM, 16)
        rr((101,226,493,460), PINK, 16)
        d.line([(165,311),(415,311)], fill=CREAM, width=14)
        d.line([(165,361),(355,361)], fill=CREAM, width=14)
    elif kind in ('eye','clue','magnifier','question'):
        oval((147,125,452,430), LIGHT)
        oval((225,204,369,349), BLUE)
        oval((260,244,332,314), INK, INK, 1)
        d.line([(404,392),(502,497)], fill=INK, width=38)
        oval((473,472,525,524), GOLD)
    else:
        poly([(100,297),(212,185),(320,309),(428,193),(512,292),(328,493)], GOLD)
    return im


def choose(scene, ep):
    boards = ep.get('visual_storyboard') or []
    n = scene['scene']
    if n < len(boards):
        v = boards[n]
        if isinstance(v, dict):
            v = v.get('icons') or []
        if isinstance(v, (tuple,list)) and v:
            return [str(x) for x in v[:3]]
    text = scene.get('text','').lower()
    tests = [('celular','phone'),('ligação','call'),('carro','car'),('motorista','car'),
             ('rodoviária','station'),('presente','gift'),('caixa','gift'),
             ('casa','home'),('portão','home'),('bilhete','letter'),('carta','letter'),
             ('mãe','family'),('pai','family'),('filha','family'),('abraç','hug'),
             ('sogra','people'),('funcionária','people'),('mentiu','clue'),
             ('pista','magnifier'),('chave','door'),('relógio','clock'),
             ('recibo','receipt'),('microfone','microphone')]
    found=[]
    for word,shape in tests:
        if word in text and shape not in found: found.append(shape)
    return (found or ['heart'])[:2]


def render(scene, ep):
    """Produce one illustrated transparent PNG. Fully offline; no faces or lettering."""
    size=(1440, 900)
    im=Image.new('RGBA',size,(0,0,0,0))
    # Soft editorial paper blobs, central to story frame, no captions
    wash=Image.new('RGBA',size,(0,0,0,0))
    w=ImageDraw.Draw(wash)
    palette=[(255,237,204,226),(216,237,242,225),(255,223,218,220)]
    color=palette[scene['scene']%len(palette)]
    w.ellipse((125,60,1305,820),fill=color)
    w.ellipse((1130,90,1340,300),fill=(255,201,94,165))
    w.ellipse((115,630,350,835),fill=(111,188,168,120))
    im.alpha_composite(wash)
    shapes=choose(scene,ep)
    if len(shapes)==1: placements=[(415,170,660)]
    elif len(shapes)==2: placements=[(126,220,550),(753,191,550)]
    else: placements=[(70,265,450),(510,180,450),(950,270,380)]
    for kind,(x,y,sz) in zip(shapes,placements):
        art=icon(kind).resize((sz,sz), Image.Resampling.LANCZOS)
        # soft paper shadow
        alpha=art.getchannel('A')
        shadow=Image.new('RGBA', art.size,(40,25,45,0))
        shadow.putalpha(alpha.filter(ImageFilter.GaussianBlur(14)).point(lambda p:int(p*.20)))
        im.alpha_composite(shadow,(x+12,y+21))
        im.alpha_composite(art,(x,y))
    out=io.BytesIO()
    im.save(out,format='PNG',optimize=True)
    return out.getvalue()
