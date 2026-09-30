"""Ensaio HyperFrames. Lê EP-001; jamais altera a fila nem publica."""
import json, os, sys, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from estudio import voz, roteiro
import compositor as H

def run(args,**kw):subprocess.run([str(x) for x in args],check=True,**kw)

item=json.loads((ROOT/'conteudo/fila.json').read_text())[0]
wav=HERE/'assets/voz.wav'
if not wav.exists():voz.gerar(roteiro.montar(item),wav)
data=json.loads(wav.with_suffix('.tempos.json').read_text())
segs=[];bats=[]
direcao={
 'gancho':('ANTES DE ENVIAR','celular','Vai responder com raiva?'),
 'passagem':('A FORÇA DA RESPOSTA BRANDA','livro','Provérbios 15:1'),
 'reflexao':('RESOLVE OU AUMENTA A BRIGA?','conversa','Uma pausa muda a conversa.'),
 'aplicacao':('DISCORDE SEM FERIR','celular','Releia antes de enviar.'),
 'cta':('ESPALHE PALAVRAS DE PAZ','coracao','Envie para quem acalma uma conversa.')}
for i,f in enumerate(data['frases']):
    title,art,note=direcao[f['papel']]
    if f['papel']=='passagem' and 'resposta' in f['texto'].lower():title='A RESPOSTA BRANDA DESVIA O FUROR'
    if f['papel']=='passagem' and 'palavra dura' in f['texto'].lower():title='PALAVRAS TÊM CONSEQUÊNCIAS'
    z=data['frases'][i+1]['inicio'] if i+1<len(data['frases']) else data['duracao_s']
    segs.append({'i':i,'ini':0 if i==0 else f['inicio'],'fim':z,'fim_fala':f['fim']})
    bats.append({'fala':f['texto'],'arte':[art,note],'hf':{'titulo':title,'selo':item['referencia_exibida'].upper()},'zoom':f['papel'] in ['gancho','reflexao']})
ep={'titulo':item['titulo'],'batidas':bats,'fim':item['cta'],'ep':1,'parte':1}
duration=H.validar_timeline(ep,segs)
job={'duration':duration,'envelope':voz.amplitude_por_quadro(wav,30)}
(HERE/'job.json').write_text(json.dumps(job))
(HERE/'timeline.json').write_text(json.dumps({'ep':ep,'segs':segs},ensure_ascii=False,indent=2))
base=HERE/'assets/base.mp4'
if not base.exists():
    run([sys.executable,'-m','manim','--disable_caching','--media_dir',HERE/'media','-o','sabio-base',HERE/'cena_base.py','SabioBase'],cwd=ROOT,env=dict(os.environ,SABIO_JOB=str(HERE/'job.json'),PYTHONPATH=str(ROOT)))
    src=next(p for p in (HERE/'media/videos').glob('**/sabio-base.mp4') if 'partial_movie_files' not in str(p))
    run(['ffmpeg','-y','-v','error','-i',src,'-c:v','libx264','-preset','fast','-crf','18','-g','30','-pix_fmt','yuv420p','-an',base])
shutil.copy(H.FONT,HERE/'assets/bold.ttf')
shutil.copy(HERE/'node_modules/gsap/dist/gsap.min.js',HERE/'assets/gsap.min.js')
H.mixar(wav,segs,duration,HERE/'assets/mix.wav')
H.compor(ep,segs,HERE)
print(json.dumps({'duracao':duration,'frases':len(segs)},ensure_ascii=False))
if '--prepare-only' not in sys.argv:
    cli=HERE/'node_modules/hyperframes/bin/hyperframes.mjs'
    env=dict(os.environ,HYPERFRAMES_NO_TELEMETRY='1',DO_NOT_TRACK='1',HYPERFRAMES_FFMPEG_PATH=shutil.which('ffmpeg'),HYPERFRAMES_FFPROBE_PATH=shutil.which('ffprobe'))
    run(['node',cli,'lint',HERE],env=env)
    out=ROOT.parent/'Proverbios_HyperFrames_Teste.mp4'
    run(['node',cli,'render',HERE,'--output',out,'--workers','2','--no-browser-gpu'],env=env)
    report=H.conferir(out,duration)
    (HERE/'validation.json').write_text(json.dumps(report,indent=2))
