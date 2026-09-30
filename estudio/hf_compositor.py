"""Composição de produção: visual aprovado, dados e artes do próprio roteiro."""
from __future__ import annotations
import base64,html,json,math,os,re,shutil,subprocess,sys
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import ImageFont
from estudio.hf_assets import ICONS


FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
TAIL=2.2
TEXT_TYPES={'titulo','seguir','manchete','manchete_v','carimbo','direct','conversa','notificacao'}

def sh(cmd,**kw):
    subprocess.run([str(x) for x in cmd],check=True,**kw)

def validar_timeline(ep,segs):
    if not ep.get('batidas') or len(ep['batidas'])!=len(segs):
        raise ValueError('Batidas e segmentos não correspondem')
    prev=0
    for i,(b,s) in enumerate(zip(ep['batidas'],segs)):
        a,z=float(s['ini']),float(s['fim'])
        if not all(math.isfinite(v) for v in (a,z)) or a<prev-.001 or z<=a:
            raise ValueError(f'Segmento inválido: {i}')
        end_voice=float(s.get('fim_fala',z-.25))
        if not math.isfinite(end_voice) or not a < end_voice <= z:
            raise ValueError(f'Fim de fala inválido: {i}')
        if s.get('i',i)!=i or not b.get('fala','').strip():
            raise ValueError(f'Fala inválida: {i}')
        prev=z
    return round(prev+TAIL,6)

def linhas(txt,size,width,max_lines=3):
    f=ImageFont.truetype(FONT,size);out=[];line=''
    for word in str(txt).split():
        if f.getlength(word)>width:return None
        candidate=(line+' '+word).strip()
        if f.getlength(candidate)>width and line:out.append(line);line=word
        else:line=candidate
    if line:out.append(line)
    return out if len(out)<=max_lines else None

def bloco(txt,width=850,max_height=128,max_size=58,min_size=26):
    txt=' '.join(str(txt).split())
    for size in range(max_size,min_size-1,-1):
        ls=linhas(txt,size,width)
        if ls and len(ls)*size*1.06<=max_height:
            return '<br>'.join(html.escape(x) for x in ls),size
    # Texto excepcionalmente longo: resumo visual, fala e legenda ficam completos.
    words=txt.split()
    while words:
        words.pop()
        ls=linhas(' '.join(words)+'…',min_size,width)
        if ls and len(ls)*min_size*1.06<=max_height:
            return '<br>'.join(html.escape(x) for x in ls),min_size
    return '…',min_size

def titulo(b,ep,i):
    custom=b.get('hf',{}).get('titulo')
    if custom:return str(custom)
    if i==0:return ep['titulo']
    txt=b.get('tela') or b['fala']
    return re.split(r'(?<=[.!?])\s+',txt,maxsplit=1)[0]

def chunks(text,width=840):
    f=ImageFont.truetype(FONT,45);out=[];g=[]
    for w in text.split():
        if g and (f.getlength(' '.join(g+[w]))>width or len(' '.join(g+[w]))>37):
            out.append(g);g=[]
        g.append(w)
    if g:out.append(g)
    return out

def compor(ep,segs,pasta):
    dur=validar_timeline(ep,segs);parts=[];anim=[]
    for i,(b,s) in enumerate(zip(ep['batidas'],segs)):
        a=float(s['ini']);z=float(s['fim']);d=z-a
        spec=b.get('arte') or [None];tipo=spec[0];arg=spec[1] if len(spec)>1 else None
        tag=b.get('hf',{}).get('selo') or f'EP {ep.get("ep",0):02d} · PARTE {ep.get("parte",1)} · SÁBIO E FELIZ'
        title,size=bloco(titulo(b,ep,i))
        body,body_size=bloco(arg if arg is not None else (b.get('tela') or b['fala']),max_height=225,max_size=34,min_size=24,width=505 if tipo in ICONS else 790)
        if tipo in ICONS:
            art=ICONS[tipo]+f'<div class="note" style="font-size:{body_size}px">{body}</div>'
        elif tipo=='imagem':
            art=f'<img class="native-art" src="assets/arte{i}.png" alt="Imagem do roteiro">'
        elif tipo and tipo not in TEXT_TYPES:
            art=f'<img class="native-art" src="assets/arte{i}.png" alt="Arte do roteiro">'
        else:
            wave='<div class="wave">'+''.join(f'<i style="height:{17+k*19%44}px"></i>' for k in range(25))+'</div>' if tipo in ('direct','notificacao') else ''
            label='PARA REFLETIR' if tipo=='seguir' and ep.get('parte')==1 else 'SÁBIO E FELIZ'
            art=f'<div class="bubble" style="font-size:{body_size}px"><small>{label}</small>{body}{wave}<div class="underline"></div></div>'
        end=dur if i==len(segs)-1 else z
        parts.append(f'<section id="p{i}" class="clip panel" data-start="{a}" data-duration="{end-a}" data-track-index="2"><div id="c{i}" class="card"><div class="tape"></div><div class="eyebrow">{html.escape(str(tag))}</div><h1 style="font-size:{size}px">{title}</h1><div class="art">{art}</div></div></section>')
        if i:
            anim.append(f'tl.fromTo("#c{i}",{{y:55,rotation:{-3 if i%2 else 3},scale:.94,opacity:0}},{{y:0,rotation:0,scale:1,opacity:1,duration:.42,immediateRender:false,ease:"back.out(1.15)"}},{a});')
        anim.append(f'tl.to("#c{i} .art",{{y:-8,duration:{max(.1,d-.5)},ease:"none"}},{a+.5});')
        anim.append(f'tl.to("#base",{{scale:{1.10 if b.get("zoom") or b.get("expr")=="chocada" else 1.02},x:{-12 if i%2 else 12},duration:.55,ease:"power2.inOut"}},{a});')
        if i and (b.get('zoom') or i%4==0):
            anim.append(f'tl.fromTo("#wipe",{{x:"-110%"}},{{x:"110%",duration:.48,immediateRender:false,ease:"power2.inOut"}},{a});')
        active=max(.1,min(d-.1,2.5))
        if tipo=='porta':anim.append(f'tl.to("#p{i} .door",{{y:-140,duration:{active},ease:"power2.inOut"}},{a+.1});')
        if tipo=='carro':anim.append(f'tl.fromTo("#p{i} .car",{{x:-45}},{{x:0,duration:.8,immediateRender:false,ease:"power2.out"}},{a});')
        if tipo=='relogio':anim.append(f'tl.to("#p{i} .hands",{{rotation:360,svgOrigin:"140 130",duration:{d},ease:"none"}},{a});')
        if tipo in ('cafe','caneca'):anim.append(f'tl.fromTo("#p{i} .steam",{{y:7,opacity:.35}},{{y:-5,opacity:1,duration:{active/2},yoyo:true,repeat:1,immediateRender:false}},{a});')
        if tipo=='coracao':anim.append(f'tl.fromTo("#p{i} .heartpath",{{scale:.92,svgOrigin:"140 130"}},{{scale:1,duration:{active/4},yoyo:true,repeat:3,immediateRender:false}},{a});')
        if tipo in ('direct','notificacao'):anim.append(f'tl.fromTo("#p{i} .wave i",{{scaleY:.45}},{{scaleY:1,duration:{min(.24,max(.05,d/8))},stagger:.015,yoyo:true,repeat:4,immediateRender:false}},{a});')
        anim.append(f'tl.fromTo("#p{i} .underline",{{scaleX:0}},{{scaleX:1,duration:.8,immediateRender:false,ease:"power2.out"}},{a});')
        ws=b['fala'].split();total=sum(max(2,len(w)) for w in ws);t=a;j=0
        fim_fala=float(s.get('fim_fala',z-.25));fim_fala=max(a+.01,min(z,fim_fala))
        groups=chunks(b['fala'])
        for k,g in enumerate(groups):
            start=t;spans=[]
            for w in g:
                endw=t+(fim_fala-a)*max(2,len(w))/total
                spans.append(f'<span id="w{i}_{j}">{html.escape(w)}</span>')
                anim.append(f'tl.set("#w{i}_{j}",{{color:"#f4cd72"}},{t});tl.set("#w{i}_{j}",{{color:"#ffffff"}},{endw});')
                t=endw;j+=1
            stop=z if k==len(groups)-1 else t
            parts.append(f'<div id="cap{i}_{k}" class="clip caps" data-start="{start}" data-duration="{stop-start}" data-track-index="3"><div class="speaker">SÁBIO E FELIZ</div><div class="words">{" ".join(spans)}</div></div>')
    final,final_size=bloco(ep.get('fim') or ('CONTINUA NA PARTE 2' if ep.get('parte')==1 else 'PALAVRAS QUE ACOLHEM'),max_height=120,max_size=45)
    parts.append(f'<div id="outro" class="clip caps" data-start="{segs[-1]["fim"]}" data-duration="{TAIL}" data-track-index="3"><div class="speaker">PALAVRAS QUE ACOLHEM</div><div class="words" style="font-size:{final_size}px">{final}</div></div>')
    confetti=''
    for k in range(22):
        x=80+k*139%920;color=['#ffd24a','#467769','#fff9ea'][k%3]
        confetti+=f'<div id="f{k}" class="confetti" style="left:{x}px;background:{color}"></div>'
        anim.append(f'tl.fromTo("#f{k}",{{y:0,opacity:1,rotation:0}},{{y:{500+k*11},x:{(k%5-2)*35},rotation:{k*63},opacity:0,duration:1.3,immediateRender:false,ease:"power1.out"}},{segs[-1]["fim"]+k*.03});')
    anim.append(f'tl.fromTo("#progress",{{scaleX:0}},{{scaleX:1,duration:{dur},ease:"none"}},0);')
    out=f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="composition.css"></head><body><div id="root" data-composition-id="sabio-hf" data-width="1080" data-height="1920" data-duration="{dur}" data-fps="30"><video id="base" class="clip" src="assets/base.mp4" data-start="0" data-duration="{dur}" data-track-index="0" muted playsinline></video><div class="wash"></div><header><div class="brand">SÁBIO E FELIZ</div><div class="tag">PROVÉRBIOS</div></header>{''.join(parts)}{confetti}<footer><span>Um provérbio. Uma decisão melhor.</span><small>@sabioefeliz</small></footer><div id="progress"></div><div class="demo">SABEDORIA PARA O DIA A DIA</div><div id="grain"></div><div id="wipe"></div><audio id="voice" src="assets/mix.wav" data-start="0" data-duration="{dur}" data-track-index="4"></audio><script src="assets/gsap.min.js"></script><script>const tl=gsap.timeline({{paused:true}});{''.join(anim)}window.__timelines=window.__timelines||{{}};window.__timelines['sabio-hf']=tl;</script></div></body></html>'''
    (pasta/'index.html').write_text(out,encoding='utf-8')
    return dur

def mixar(voz,segs,dur,destino):
    sr=48000;out=np.zeros(math.ceil(sr*dur));rng=np.random.default_rng(91)
    def add(t,s):
        i=int(t*sr);n=min(len(s),len(out)-i)
        if n>0:out[i:i+n]+=s[:n]
    for k,t0 in enumerate(np.arange(0,dur,.6)):
        t=np.arange(int(.22*sr))/sr
        add(t0,.008*np.sin(2*np.pi*65*t)*np.exp(-t*25))
        if k%2:add(t0,.002*rng.normal(size=len(t))*np.exp(-t*38))
    for k,t0 in enumerate(np.arange(0,dur,2.4)):
        t=np.arange(int(1.8*sr))/sr;notes=[220,261.63,329.63] if k%2 else [196,246.94,293.66]
        add(t0,sum(.003*np.sin(2*np.pi*f*t)*np.exp(-t*2.8) for f in notes))
    for s in segs[1:]:
        t=np.arange(int(.18*sr))/sr
        add(s['ini'],.006*rng.normal(size=len(t))*np.sin(np.pi*t/.18)**2)
    for i,s in enumerate(segs):
        if i==0 or i%4==0:
            for k,f in enumerate([880,1174]):
                t=np.arange(int(.14*sr))/sr
                add(s['ini']+.15+k*.14,.018*np.sin(2*np.pi*f*t)*np.exp(-t*25))
    bed=destino.with_name('bed.wav');sf.write(bed,out,sr)
    sh(['ffmpeg','-y','-v','error','-i',voz,'-i',bed,'-filter_complex',f'[0:a]apad,atrim=duration={dur}[v];[v][1:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=disabled[a]','-map','[a]','-ar','48000',destino])

def conferir(mp4,dur):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(mp4)]))
    videos=[s for s in data['streams'] if s['codec_type']=='video'];audios=[s for s in data['streams'] if s['codec_type']=='audio']
    if len(videos)!=1 or not audios:raise ValueError('MP4 incompleto: vídeo ou áudio ausente')
    v=videos[0]
    if (v['width'],v['height'],v['avg_frame_rate'])!=(1080,1920,'30/1') or abs(float(data['format']['duration'])-dur)>.15:
        raise ValueError('Resolução, fps ou duração divergente')
    return data
