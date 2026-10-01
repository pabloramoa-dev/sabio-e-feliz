"""Adaptador de produção do visual aprovado em 30/09/2026.

Consome exclusivamente o item editorial e os tempos da voz do canal.
Não publica, não altera a fila e não reaproveita falas do episódio piloto.
"""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

VERSAO = 'hyperframes-v2'


def montar_timeline(item, dados):
    frases = dados['frases']
    dur = float(dados['duracao_s'])
    if not frases or not math.isfinite(dur) or dur <= 0:
        raise ValueError('Narração vazia ou duração inválida')
    bats, segs = [], []
    leitura = item.get('formato') == 'D'
    anterior = 0.0
    for i, f in enumerate(frases):
        ini, fim = float(f['inicio']), float(f['fim'])
        if not all(math.isfinite(t) for t in (ini, fim)) or ini < anterior or fim <= ini or fim > dur:
            raise ValueError('Tempos de frase inválidos')
        anterior = fim
        papel = f['papel']
        texto = f['texto'].strip()
        if not texto:
            raise ValueError('Frase vazia')
        # Títulos e notas derivam do conteúdo de cada episódio; nenhuma
        # interpretação ou chamada de outro episódio entra na composição.
        if papel == 'gancho':
            titulo, arte, nota = item['titulo'], 'livro' if leitura else 'conversa', item['gancho']
        elif papel == 'cta':
            titulo, arte, nota = ('LEIA O CAPÍTULO INTEIRO' if leitura else 'LEVE ESTA REFLEXÃO COM VOCÊ'), ('livro' if leitura else 'coracao'), item['cta']
        elif papel == 'passagem' or leitura:
            titulo, arte, nota = texto, 'livro', item['referencia_exibida']
        else:
            titulo, arte, nota = texto, 'conversa', item.get(papel, texto)
        bats.append({'fala': texto, 'arte': [arte, nota],
                     'hf': {'titulo': titulo.upper(), 'selo': item['referencia_exibida'].upper()},
                     'zoom': papel in ('gancho', 'reflexao')})
        z = float(frases[i+1]['inicio']) if i+1 < len(frases) else dur
        segs.append({'i': i, 'ini': 0.0 if i == 0 else ini, 'fim': z, 'fim_fala': fim})
    return {'titulo': item['titulo'], 'batidas': bats, 'fim': item['cta']}, segs


def renderizar_v1(item, wav: Path, dados_voz: dict, saida: Path) -> Path:
    from estudio import hf_compositor as H, voz
    from src.validar_video import validar
    raiz = Path(__file__).resolve().parent.parent
    wav, saida = Path(wav).resolve(), Path(saida).resolve()
    ep, segs = montar_timeline(item, dados_voz)
    dur = H.validar_timeline(ep, segs)
    from src import config
    if not config.DURACAO_MIN_S <= dur <= config.DURACAO_MAX_S:
        raise ValueError(f'Duração HyperFrames fora do limite: {dur:.2f}s')
    if abs(voz.duracao(wav) - float(dados_voz['duracao_s'])) > .15:
        raise ValueError('Áudio e timeline divergentes')
    video = raiz/'video'
    cli = video/'node_modules/hyperframes/bin/hyperframes.mjs'
    if not cli.is_file():
        raise FileNotFoundError('Instale HyperFrames com npm ci --prefix video')
    trabalho = wav.parent/'hyperframes'
    assets = trabalho/'assets'
    assets.mkdir(parents=True, exist_ok=True)
    saida.parent.mkdir(parents=True, exist_ok=True)
    job = trabalho/'job.json'
    job.write_text(json.dumps({'duration': dur, 'envelope': voz.amplitude_por_quadro(wav,30)}))
    (trabalho/'timeline.json').write_text(json.dumps({'ep':ep,'segs':segs},ensure_ascii=False,indent=2))
    env = dict(os.environ, SABIO_JOB=str(job), PYTHONPATH=str(raiz)+os.pathsep+os.environ.get('PYTHONPATH',''),
               HYPERFRAMES_NO_TELEMETRY='1', DO_NOT_TRACK='1',
               HYPERFRAMES_FFMPEG_PATH=shutil.which('ffmpeg') or 'ffmpeg',
               HYPERFRAMES_FFPROBE_PATH=shutil.which('ffprobe') or 'ffprobe')
    media = trabalho/'media'
    H.sh([sys.executable,'-m','manim','--disable_caching','--media_dir',media,'-o','sabio-base',
          raiz/'estudio/cena_hyperframes.py','SabioBase'],cwd=raiz,env=env)
    bases = [p for p in (media/'videos').glob('**/sabio-base.mp4') if 'partial_movie_files' not in str(p)]
    if len(bases) != 1:
        raise ValueError('Camada do Sábio ausente ou ambígua')
    H.sh(['ffmpeg','-y','-v','error','-i',bases[0],'-c:v','libx264','-preset','fast','-crf','18',
          '-g','30','-pix_fmt','yuv420p','-an',assets/'base.mp4'])
    shutil.copy(H.FONT,assets/'bold.ttf')
    shutil.copy(video/'assets/composition.css',trabalho/'composition.css')
    shutil.copy(video/'node_modules/gsap/dist/gsap.min.js',assets/'gsap.min.js')
    H.mixar(wav,segs,dur,assets/'mix.wav')
    H.compor(ep,segs,trabalho)
    H.sh(['node',cli,'lint',trabalho],env=env)
    temporario = saida.with_name(saida.stem+'.rendering.mp4')
    try:
        H.sh(['node',cli,'render',trabalho,'--output',temporario,'--workers',
              os.getenv('SABIO_HF_WORKERS','2'),'--no-browser-gpu'],env=env)
        H.conferir(temporario,dur)
        tecnico = validar(temporario)
        temporario.replace(saida)
    finally:
        temporario.unlink(missing_ok=True)
    (wav.parent/'render.json').write_text(json.dumps({'motor':VERSAO,'voz':dados_voz['voz'],**tecnico},indent=2))
    return saida


def renderizar(item, wav: Path, dados_voz: dict, saida: Path) -> Path:
    """Padrão desde 01/10/2026: Sábio vivo + composição v2.

    SABIO_HF_VISUAL=v1 volta ao visual HyperFrames de 30/09 para diagnóstico.
    """
    if os.getenv('SABIO_HF_VISUAL', 'v2').strip().lower() == 'v1':
        return renderizar_v1(item, wav, dados_voz, saida)
    from estudio import hf_compositor as H, hf_sabio as S, voz
    from src.validar_video import validar
    from src import config
    raiz = Path(__file__).resolve().parent.parent
    wav, saida = Path(wav).resolve(), Path(saida).resolve()
    dur = S.validar(item, dados_voz)
    if not config.DURACAO_MIN_S <= dur <= config.DURACAO_MAX_S:
        raise ValueError(f'Duração HyperFrames fora do limite: {dur:.2f}s')
    if abs(voz.duracao(wav) - float(dados_voz['duracao_s'])) > .15:
        raise ValueError('Áudio e timeline divergentes')
    video = raiz/'video'
    cli = video/'node_modules/hyperframes/bin/hyperframes.mjs'
    if not cli.is_file():
        raise FileNotFoundError('Instale HyperFrames com npm ci --prefix video')
    trabalho = wav.parent/'hyperframes'
    if trabalho.exists():
        shutil.rmtree(trabalho)
    assets = trabalho/'assets'
    assets.mkdir(parents=True, exist_ok=True)
    saida.parent.mkdir(parents=True, exist_ok=True)
    job = trabalho/'job.json'
    job.write_text(json.dumps({'duration': dur, 'formato': item.get('formato'),
                               'segmentos': dados_voz['segmentos'],
                               'envelope': voz.amplitude_por_quadro(wav, 30)}))
    env = dict(os.environ, SABIO_JOB=str(job), PYTHONPATH=str(raiz)+os.pathsep+os.environ.get('PYTHONPATH',''),
               HYPERFRAMES_NO_TELEMETRY='1', DO_NOT_TRACK='1',
               HYPERFRAMES_FFMPEG_PATH=shutil.which('ffmpeg') or 'ffmpeg',
               HYPERFRAMES_FFPROBE_PATH=shutil.which('ffprobe') or 'ffprobe')
    media = trabalho/'media'
    H.sh([sys.executable,'-m','manim','--disable_caching','--progress_bar','none','-v','WARNING',
          '--media_dir',media,'-o','sabio-vivo',raiz/'estudio/sabio_vivo.py','SabioVivo'],cwd=raiz,env=env)
    bases = [p for p in (media/'videos').glob('**/sabio-vivo.mp4') if 'partial_movie_files' not in str(p)]
    if len(bases) != 1:
        raise ValueError('Camada do Sábio ausente ou ambígua')
    # gradação quente de manhã + brilho suave (bloom) já na camada do Sábio:
    # feito no ffmpeg porque o shader de cor do navegador deixa a captura lenta
    luz = ('split[a][b];[b]gblur=sigma=14,eq=brightness=0.06[g];'
           '[a][g]blend=all_mode=screen:all_opacity=0.12,'
           'colorbalance=gs=0.01:bs=-0.03:bh=-0.02,eq=saturation=1.06:contrast=1.04')
    H.sh(['ffmpeg','-y','-v','error','-i',bases[0],'-vf',luz,'-c:v','libx264','-preset','fast','-crf','16',
          '-g','30','-pix_fmt','yuv420p','-an',assets/'base.mp4'])
    shutil.copy(S.achar('Poppins-Bold.ttf','assets/fonts'),assets/'Poppins-Bold.ttf')
    shutil.copy(S.achar('Poppins-Medium.ttf','assets/fonts'),assets/'Poppins-Medium.ttf')
    shutil.copy(S.achar('Lora-Italic-Variable.ttf','assets/fonts'),assets/'Lora-Italic.ttf')
    shutil.copy(S.achar('sabio-v2.css','video/assets'),trabalho/'composition.css')
    shutil.copy(video/'node_modules/gsap/dist/gsap.min.js',assets/'gsap.min.js')
    dur, sons = S.compor(item, dados_voz, trabalho)
    S.mixar(wav, dur, sons, assets/'mix.wav')
    H.sh(['node',cli,'lint',trabalho],env=env)
    temporario = saida.with_name(saida.stem+'.rendering.mp4')
    try:
        H.sh(['node',cli,'render',trabalho,'--output',temporario,'--workers',
              os.getenv('SABIO_HF_WORKERS','2'),'--no-browser-gpu'],env=env)
        H.conferir(temporario,dur)
        tecnico = validar(temporario)
        temporario.replace(saida)
    finally:
        temporario.unlink(missing_ok=True)
    (wav.parent/'render.json').write_text(json.dumps({'motor':VERSAO,'voz':dados_voz['voz'],**tecnico},indent=2))
    return saida
