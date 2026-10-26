import json
import time

import numpy as np

from motor import Catalogo, Evaluador, Nsga2, cargarEscenario

#Revisar la poblacion inicial y medir el costo por evaluacion
if __name__ == '__main__':
    reporte = {}
    for escenario in ['explanada', 'plaza', 'salon']:
        recinto, clases = cargarEscenario(f'escenarios/{escenario}.json')
        catalogo = Catalogo(recinto, clases)
        evaluador = Evaluador(recinto, catalogo)
        algoritmo = Nsga2(evaluador, semilla=0)
        evaluador.evaluar(algoritmo.construirIndividuo())
        validas, tiempos, violaciones = 0, [], np.zeros(6, dtype=int)
        muestras = 200
        for _ in range(muestras):
            L = algoritmo.construirIndividuo()
            inicio = time.perf_counter()
            resultado = evaluador.evaluar(L)
            tiempos.append(time.perf_counter() - inicio)
            violaciones += np.array(resultado['violaciones']) > 0
            validas += resultado['G'] == 0
        aleatorias = 0
        rng = np.random.default_rng(0)
        for _ in range(muestras):
            L = np.array([[rng.integers(recinto.ancho), rng.integers(recinto.largo), rng.integers(4)] for _ in range(catalogo.cantidad)])
            aleatorias += evaluador.violaciones(L)[0] == [0] * 6
        reporte[escenario] = {'muestras': muestras, 'validasConstruidas': int(validas), 'validasAleatorias': int(aleatorias),
                              'restriccionesIncumplidas': violaciones.tolist(), 'msPorEvaluacion': 1000 * float(np.mean(tiempos)),
                              'areaRecinto': int(recinto.omega0.sum()), 'aforo': recinto.aforo,
                              'aforoMaximo': recinto.aforoMaximo(catalogo.areaTotal), 'modulos': catalogo.cantidad}
        print(escenario, reporte[escenario])
    with open('resultados/verificacion.json', 'w', encoding='utf-8') as archivo:
        json.dump(reporte, archivo, ensure_ascii=False, indent=2)
