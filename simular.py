import argparse
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from analisis import dibujarRecinto
from motor import Catalogo, Evaluador, cargarEscenario
from motor import parametros as P

#Animar la evacuacion de la distribucion de rodilla de una corrida
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulación paso a paso con mapa de densidad')
    parser.add_argument('escenario')
    parser.add_argument('--semilla', type=int, default=1)
    parser.add_argument('--cada', type=int, default=5)
    args = parser.parse_args()
    recinto, clases = cargarEscenario(f'escenarios/{args.escenario}.json')
    catalogo = Catalogo(recinto, clases)
    evaluador = Evaluador(recinto, catalogo)
    with open(f'resultados/{args.escenario}/semilla{args.semilla:02d}.json', encoding='utf-8') as archivo:
        corrida = json.load(archivo)
    L = np.array(corrida['frente'][corrida['rodilla']]['cromosoma'])
    conteo, _, _, _ = evaluador.desplegar(L)
    libre = recinto.omega0 & (conteo == 0)
    tiempo, cuadros = evaluador.tiempoEvacuacion(libre, guardarCada=args.cada)
    figura, eje = plt.subplots(figsize=(7, 5))
    dibujarRecinto(eje, recinto, catalogo, L)
    imagen = eje.imshow(np.ma.masked_where(~libre, cuadros[0]), origin='lower', extent=(0, recinto.ancho, 0, recinto.largo),
                        cmap='YlOrRd', vmin=0, vmax=P.densidadMaxima, interpolation='nearest', zorder=3)
    figura.colorbar(imagen, ax=eje, fraction=0.03, label='personas/m²')

    def actualizar(k):
        imagen.set_data(np.ma.masked_where(~libre, cuadros[k]))
        eje.set_title(f'{recinto.nombre}: t = {k * args.cada * P.pasoTiempo:.0f} s, dentro: {cuadros[k].sum():.0f} personas')
        return [imagen]

    animacion = FuncAnimation(figura, actualizar, frames=len(cuadros), blit=False)
    animacion.save(f'resultados/figuras/simulacion_{args.escenario}.gif', writer=PillowWriter(fps=8))
    print(f'Tiempo de evacuación: {tiempo:.1f} s, {len(cuadros)} cuadros')
