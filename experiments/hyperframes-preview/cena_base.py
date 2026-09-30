"""Camada do personagem original; ensaio isolado, sem publicação."""
import json, os
from pathlib import Path
from manim import *
import numpy as np
from estudio.cena import cenario_manha, rosto_sabio, lip_sync, vapor
from estudio import previsao_lib as P

config.frame_width=8
config.frame_height=128/9
config.pixel_width=720
config.pixel_height=1280
config.frame_rate=30

class SabioBase(Scene):
    def construct(self):
        job=json.loads(Path(os.environ['SABIO_JOB']).read_text())
        fundo,frente,piso=cenario_manha()
        self.add(fundo)
        dm=rosto_sabio(P.ranzinza('desconfiado'))
        g=dm['grupo'];g.scale(1.62)
        g.shift(UP*(-.85-dm['cab'].get_center()[1]))
        self.add(g)
        home=g.get_center().copy()
        eye_heights=[dm[k].height for k in ['oe','od']]
        hand=dm['maoE'];hand_home=hand.get_center().copy()
        arm=g[10];arm_start=arm.get_start().copy()
        def motion(m,dt):
            t=self.renderer.time
            delta=np.array([.055*np.sin(t*1.3),.035*np.sin(t*2),0])
            m.move_to(home+delta)
            blink=(t%4.1)
            f=.1 if blink<.13 else 1
            for k,h in zip(['oe','od'],eye_heights):dm[k].stretch_to_fit_height(h*f)
            lift=.22*(.5+.5*np.sin(t*1.55))
            pos=hand_home+delta+UP*lift+LEFT*(lift*.4)
            hand.move_to(pos);arm.put_start_and_end_on(arm_start+delta,pos)
        g.add_updater(motion)
        self.add(frente)
        vapor(self,np.array([2.9,piso+.9,0]))
        lip_sync(self,dm,job['envelope'],30)
        self.wait(job['duration'])
