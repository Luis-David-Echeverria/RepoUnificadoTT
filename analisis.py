import glob
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.size'] = 12
import numpy as np
from matplotlib.patches import Rectangle

from motor import Catalogo, Evaluador, Nsga2, cargarEscenario, puntoRodilla
from motor.nsga2 import ordenarNoDominados

escenarios = ['explanada', 'plaza', 'salon']
nombres = {'explanada': 'Explanada abierta', 'plaza': 'Plaza con escenario', 'salon': 'Salón con muro divisorio'}
coloresTipo = {'sanitarios': '#4C78A8', 'atención médica': '#E45756', 'puestos de comida': '#F2A541'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})


def cargarResultados(escenario):
    resultados = []
    for ruta in sorted(glob.glob(f'resultados/{escenario}/semilla*.json')):
        with open(ruta, encoding='utf-8') as archivo:
            resultados.append(json.load(archivo))
    return resultados


def dibujarRecinto(ax, recinto, catalogo=None, L=None):
    a, b = recinto.ancho, recinto.largo
    fondo = np.where(recinto.omega0, 1.0, 0.0)
    ax.imshow(fondo, origin='lower', extent=(0, a, 0, b), cmap='Greys', vmin=-0.2, vmax=4, interpolation='nearest')
    for y, x in zip(*np.nonzero(recinto.inaccesible)):
        ax.add_patch(Rectangle((x, y), 1, 1, facecolor='#555555', edgecolor='none'))
    for y in range(b):
        for x in range(a + 1):
            if recinto.muroV[y, x]:
                ax.plot([x, x], [y, y + 1], color='black', lw=2, solid_capstyle='butt')
    for y in range(b + 1):
        for x in range(a):
            if recinto.muroH[y, x]:
                ax.plot([x, x + 1], [y, y], color='black', lw=2, solid_capstyle='butt')
    for salida in recinto.salidas:
        d = salida['datos']
        if d['orientacion'] == 'V':
            ax.plot([d['x'], d['x']], [d['y'], d['y'] + d['largo']], color='#2CA02C', lw=5, solid_capstyle='butt')
        else:
            ax.plot([d['x'], d['x'] + d['largo']], [d['y'], d['y']], color='#2CA02C', lw=5, solid_capstyle='butt')
    if L is not None:
        for j, (x, y, o) in enumerate(L):
            m = catalogo.modulos[j]
            orient = m.orientaciones[o]
            ax.add_patch(Rectangle((x, y), orient['ancho'], orient['largo'], facecolor=coloresTipo[m.tipo],
                                   edgecolor='black', lw=0.8))
            for cy, cx, lado, ay, ax2 in orient['puertas']:
                px, py = x + cx, y + cy
                segmento = {'S': ([px, px + 1], [py, py]), 'N': ([px, px + 1], [py + 1, py + 1]),
                            'O': ([px, px], [py, py + 1]), 'E': ([px + 1, px + 1], [py, py + 1])}[lado]
                ax.plot(*segmento, color='#1B1B1B', lw=3.5, solid_capstyle='butt')
    ax.set_xlim(-0.5, a + 0.5)
    ax.set_ylim(-0.5, b + 0.5)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])


#Juntar los frentes de todas las semillas y quedarse con los no dominados
def frenteConjunto(resultados):
    puntos = [p for r in resultados for p in r['frente']]
    evaluaciones = [{'G': 0, 'F1': p['F1'], 'F2': p['F2']} for p in puntos]
    frente = [puntos[i] for i in ordenarNoDominados(evaluaciones)[0]]
    unicos = {(round(p['F1'], 6), round(p['F2'], 6)): p for p in frente}
    return sorted(unicos.values(), key=lambda p: p['F1'])


#Mejor valor esperado al hacer n corridas en lugar de 10
def brechaPorRepeticiones(valores, rng, permutaciones=2000):
    valores = np.array(valores)
    mejor = valores.min()
    brechas = []
    for n in range(1, len(valores) + 1):
        muestras = [valores[rng.permutation(len(valores))[:n]].min() for _ in range(permutaciones)]
        brechas.append(100 * (np.mean(muestras) - mejor) / mejor)
    return brechas


def distribucionAlAzar(evaluador, semilla=0):
    algoritmo = Nsga2(evaluador, semilla=semilla)
    for _ in range(1000):
        L = algoritmo.construirIndividuo()
        resultado = evaluador.evaluar(L)
        if resultado['G'] == 0:
            return L, resultado
    raise RuntimeError('No se encontró una distribución al azar válida')


def analizar():
    os.makedirs('resultados/figuras', exist_ok=True)
    rng = np.random.default_rng(0)
    resumen = {}
    figFrentes, ejesFrentes = plt.subplots(1, 3, figsize=(13, 4.4))
    figRep, ejesRep = plt.subplots(1, 3, figsize=(13, 3.4), sharey=True)
    colores = plt.cm.tab10(np.linspace(0, 1, 10))
    for k, escenario in enumerate(escenarios):
        resultados = cargarResultados(escenario)
        filas = []
        for r in resultados:
            puntos = [[p['F1'], p['F2']] for p in r['frente']]
            rodilla = r['frente'][r['rodilla']]
            todasValidas = next((h['generacion'] for h in r['historia'] if h['factibles'] == r['poblacion']), None)
            filas.append({'semilla': r['semilla'], 'puntos': len(puntos), 'mejorF1': min(p[0] for p in puntos),
                          'mejorF2': min(p[1] for p in puntos), 'rodillaF1': rodilla['F1'], 'rodillaF2': rodilla['F2'],
                          'evaluaciones': r['evaluaciones'], 'segundos': r['segundos'], 'generacionTodasValidas': todasValidas})
            frente = np.array(sorted(puntos))
            c = colores[(r['semilla'] - 1) % 10]
            ejesFrentes[k].plot(frente[:, 0], frente[:, 1], '-o', color=c, ms=3, lw=0.8, label=f'Semilla {r["semilla"]}')
            ejesFrentes[k].plot(rodilla['F1'], rodilla['F2'], '*', color=c, ms=11, mec='black', mew=0.5)
        ejesFrentes[k].set_title(nombres[escenario])
        ejesFrentes[k].set_xlabel('F1: distancia promedio (m)')
        ejesFrentes[k].set_ylabel('F2: tiempo de evacuación (s)')
        variacion = {}
        for clave in ('mejorF1', 'mejorF2', 'rodillaF1', 'rodillaF2'):
            valores = [f[clave] for f in filas]
            variacion[clave] = {'minimo': min(valores), 'maximo': max(valores),
                                'diferencia': 100 * (max(valores) - min(valores)) / min(valores)}
        brechaF1 = brechaPorRepeticiones([f['mejorF1'] for f in filas], rng)
        brechaF2 = brechaPorRepeticiones([f['mejorF2'] for f in filas], rng)
        n = np.arange(1, len(filas) + 1)
        ejesRep[k].plot(n, brechaF1, '-o', ms=3, color='#4C78A8', label='Distancia promedio (F1)')
        ejesRep[k].plot(n, brechaF2, '-s', ms=3, color='#E45756', label='Tiempo de evacuación (F2)')
        ejesRep[k].axhline(0.5, color='gray', lw=0.8, ls='--')
        ejesRep[k].set_title(nombres[escenario])
        ejesRep[k].set_xlabel('Número de repeticiones')
        ejesRep[k].set_xticks(n)
        necesarias = int(next(i + 1 for i in range(len(n)) if brechaF1[i] <= 0.5 and brechaF2[i] <= 0.5))
        #Distribuciones para comparar
        recinto, clases = cargarEscenario(f'escenarios/{escenario}.json')
        catalogo = Catalogo(recinto, clases)
        evaluador = Evaluador(recinto, catalogo)
        conjunto = frenteConjunto(resultados)
        mejorEvacuacion = min(conjunto, key=lambda p: (p['F2'], p['F1']))
        mejorAccesibilidad = min(conjunto, key=lambda p: (p['F1'], p['F2']))
        rodillaConjunta = conjunto[puntoRodilla(conjunto)]
        Lazar, azar = distribucionAlAzar(evaluador)
        casos = [('Al azar', Lazar, azar), ('Mejor para evacuación', np.array(mejorEvacuacion['cromosoma']), mejorEvacuacion),
                 ('Mejor para accesibilidad', np.array(mejorAccesibilidad['cromosoma']), mejorAccesibilidad),
                 ('Punto de rodilla', np.array(rodillaConjunta['cromosoma']), rodillaConjunta)]
        figDist, ejesDist = plt.subplots(2, 2, figsize=(10, 7))
        for eje, (titulo, L, valores) in zip(ejesDist.flat, casos):
            dibujarRecinto(eje, recinto, catalogo, L)
            eje.set_title(f'{titulo}: F1 = {valores["F1"]:.2f} m, F2 = {valores["F2"]:.1f} s', fontsize=11)
        figDist.tight_layout()
        figDist.savefig(f'resultados/figuras/distribuciones_{escenario}.png', dpi=200, bbox_inches='tight')
        plt.close(figDist)
        if escenario == 'plaza':
            figEv, ejesEv = plt.subplots(2, 4, figsize=(13, 5.6))
            for fila, (titulo, L, _) in enumerate((casos[0], casos[3])):
                conteo, _, _, _ = evaluador.desplegar(L)
                libre = recinto.omega0 & (conteo == 0)
                tiempo, cuadros = evaluador.tiempoEvacuacion(libre, guardarCada=50)
                for i, segundos in enumerate((0, 30, 60, 75)):
                    c = min(int(segundos / (50 * 0.3)), len(cuadros) - 1)
                    dibujarRecinto(ejesEv[fila, i], recinto, catalogo, L)
                    densidad = np.ma.masked_where(~libre, cuadros[c])
                    imagen = ejesEv[fila, i].imshow(densidad, origin='lower', extent=(0, recinto.ancho, 0, recinto.largo),
                                                    cmap='YlOrRd', vmin=0, vmax=5.4, interpolation='nearest', zorder=3)
                    ejesEv[fila, i].set_title(f'{titulo}: t = {c * 50 * 0.3:.0f} s, dentro: {cuadros[c].sum():.0f}', fontsize=8.5)
            figEv.colorbar(imagen, ax=ejesEv, fraction=0.015, label='personas/m²')
            figEv.savefig('resultados/figuras/evacuacion_plaza.png', dpi=200, bbox_inches='tight')
            plt.close(figEv)
        resumen[escenario] = {
            'nombre': nombres[escenario], 'semillas': filas, 'variacion': variacion,
            'brechaF1': brechaF1, 'brechaF2': brechaF2, 'repeticionesNecesarias': necesarias,
            'comparacion': {titulo: {'F1': float(v['F1']), 'F2': float(v['F2']), 'distancias': v['distancias']} for titulo, _, v in casos},
            'puntosFrenteConjunto': len(conjunto),
            'evaluacionesPromedio': float(np.mean([f['evaluaciones'] for f in filas])),
            'segundosPromedio': float(np.mean([f['segundos'] for f in filas])),
        }
    figFrentes.legend(*ejesFrentes[0].get_legend_handles_labels(), loc='lower center', ncol=10, frameon=False, fontsize=10, bbox_to_anchor=(0.5, -0.08))
    ejesRep[0].set_ylabel('Diferencia con el mejor de 10 (%)')
    ejesRep[2].legend(fontsize=10, frameon=False, loc='upper right')
    for figura, nombre in ((figFrentes, 'frentes'), (figRep, 'repeticiones')):
        figura.tight_layout()
        figura.savefig(f'resultados/figuras/{nombre}.png', dpi=200, bbox_inches='tight')
        plt.close(figura)
    figRec, ejesRec = plt.subplots(1, 3, figsize=(13, 3.6))
    for k, escenario in enumerate(escenarios):
        recinto, _ = cargarEscenario(f'escenarios/{escenario}.json')
        dibujarRecinto(ejesRec[k], recinto)
        ejesRec[k].set_title(nombres[escenario])
    figRec.tight_layout()
    figRec.savefig('resultados/figuras/recintos.png', dpi=200, bbox_inches='tight')
    plt.close(figRec)
    with open('resultados/resumen.json', 'w', encoding='utf-8') as archivo:
        json.dump(resumen, archivo, ensure_ascii=False, indent=2, default=float)
    return resumen


if __name__ == '__main__':
    resumen = analizar()
    for escenario, datos in resumen.items():
        print(datos['nombre'], 'repeticiones:', datos['repeticionesNecesarias'],
              {t: (round(v['F1'], 2), round(v['F2'], 1)) for t, v in datos['comparacion'].items()})
