"""Versão visual usada pelo estúdio e pela fila; não carrega o renderizador."""
import os
HYPERFRAMES_VERSION = 'nina-hyperframes-1'
def versao():
    motor = os.environ.get('NINA_MOTOR', 'hyperframes')
    if motor not in ('hyperframes', 'manim'):
        raise ValueError('NINA_MOTOR deve ser hyperframes ou manim')
    return HYPERFRAMES_VERSION if motor == 'hyperframes' else 'nina-manim-legacy'
