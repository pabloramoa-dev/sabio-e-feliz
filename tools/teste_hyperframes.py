"""Render real isolado para CI: não escreve na fila e não publica."""
import argparse
import json
from pathlib import Path
from estudio import render, roteiro, voz
from src import config, validar_video

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--id')
    parser.add_argument('--mudo',action='store_true')
    args=parser.parse_args()
    itens=json.loads(config.FILA_JSON.read_text())
    item=next(i for i in itens if i['id']==args.id) if args.id else next(i for i in itens if i.get('formato')=='D')
    pasta=config.SAIDA/'teste-hyperframes'
    pasta.mkdir(parents=True,exist_ok=True)
    wav=pasta/'voz.wav'
    dados=voz.gerar(roteiro.montar(item),wav,mudo=args.mudo)
    mp4=render.renderizar(item,wav,dados,pasta/'teste.mp4')
    print(json.dumps({'id':item['id'],**validar_video.validar(mp4)},indent=2))

if __name__=='__main__':main()
