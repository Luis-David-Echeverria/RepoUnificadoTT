import argparse
import json
import os
from multiprocessing import Pool

from motor import Catalogo, Evaluador, Nsga2, cargarEscenario


def correr(argumentos):
    escenario, semilla, poblacion, generaciones = argumentos
    recinto, clases = cargarEscenario(f'escenarios/{escenario}.json')
    catalogo = Catalogo(recinto, clases)
    evaluador = Evaluador(recinto, catalogo)
    algoritmo = Nsga2(evaluador, poblacion, generaciones, semilla)
    resultado = algoritmo.ejecutar()
    salida = {
        'escenario': escenario,
        'semilla': semilla,
        'poblacion': poblacion,
        'generaciones': generaciones,
        'evaluaciones': resultado['evaluaciones'],
        'segundos': resultado['segundos'],
        'rodilla': resultado['rodilla'],
        'frente': [{'F1': e['F1'], 'F2': e['F2'], 'distancias': e['distancias'], 'cromosoma': L.tolist()}
                   for L, e in resultado['frente']],
        'historia': resultado['historia'],
    }
    os.makedirs(f'resultados/{escenario}', exist_ok=True)
    with open(f'resultados/{escenario}/semilla{semilla:02d}.json', 'w', encoding='utf-8') as archivo:
        json.dump(salida, archivo, ensure_ascii=False)
    return escenario, semilla, len(salida['frente']), round(resultado['segundos'], 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Corridas independientes de NSGA-II')
    parser.add_argument('--escenarios', nargs='+', default=['explanada', 'plaza', 'salon'])
    parser.add_argument('--semillas', type=int, default=10)
    parser.add_argument('--poblacion', type=int, default=40)
    parser.add_argument('--generaciones', type=int, default=50)
    parser.add_argument('--procesos', type=int, default=2)
    args = parser.parse_args()
    tareas = [(e, s, args.poblacion, args.generaciones) for e in args.escenarios for s in range(1, args.semillas + 1)]
    with Pool(args.procesos) as pool:
        for escenario, semilla, puntos, segundos in pool.imap_unordered(correr, tareas):
            print(f'{escenario} semilla {semilla}: {puntos} distribuciones en el frente, {segundos} s', flush=True)
