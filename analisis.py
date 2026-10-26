import glob
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from scipy import stats

from motor import Catalogo, Evaluador, cargarEscenario

escenarios = ['explanada', 'plaza', 'salon']
nombres = {'explanada': 'Explanada abierta', 'plaza': 'Plaza con escenario', 'salon': 'Salón con muro divisorio'}
coloresTipo = {'sanitarios': '#4C78A8', 'atención médica': '#E45756', 'puestos de comida': '#F2A541'}
referencia = 1.1
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})


def cargarResultados(escenario):
    resultados = []
    for ruta in sorted(glob.glob(f'resultados/{escenario}/semilla*.json')):
        with open(ruta, encoding='utf-8') as archivo:
            resultados.append(json.load(archivo))
    return resultados


#Hipervolumen en dos objetivos normalizados
def hipervolumen(puntos, ideal, nadir):
    if len(puntos) == 0:
        return 0.0
    p = (np.array(puntos) - ideal) / np.where(nadir - ideal > 0, nadir - ideal, 1.0)
    p = p[(p[:, 0] < referencia) & (p[:, 1] < referencia)]
    p = p[np.argsort(p[:, 0])]
    volumen, mejorF2 = 0.0, referencia
    for f1, f2 in p:
        if f2 < mejorF2:
            volumen += (referencia - f1) * (mejorF2 - f2)
            mejorF2 = f2
    return volumen


def repeticionesNecesarias(valores, error):
    media, desviacion = np.mean(valores), np.std(valores, ddof=1)
    for n in range(2, 1000):
        if stats.t.ppf(0.975, n - 1) * desviacion / np.sqrt(n) <= error * media:
            return n
    return None


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
    ax.set_xticks(range(0, a + 1, 5))
    ax.set_yticks(range(0, b + 1, 5))


def analizar():
    os.makedirs('resultados/figuras', exist_ok=True)
    resumen = {}
    figFrentes, ejesFrentes = plt.subplots(1, 3, figsize=(13, 4))
    figConv, ejesConv = plt.subplots(1, 3, figsize=(13, 3.6))
    figDist, ejesDist = plt.subplots(1, 3, figsize=(13, 3.8))
    colores = plt.cm.tab10(np.linspace(0, 1, 10))
    for k, escenario in enumerate(escenarios):
        resultados = cargarResultados(escenario)
        finales = np.array([[p['F1'], p['F2']] for r in resultados for p in r['frente']])
        ideal, nadir = finales.min(axis=0), finales.max(axis=0)
        filas = []
        for r in resultados:
            puntos = [[p['F1'], p['F2']] for p in r['frente']]
            rodilla = r['frente'][r['rodilla']]
            filas.append({'semilla': r['semilla'], 'hipervolumen': hipervolumen(puntos, ideal, nadir),
                          'puntos': len(puntos), 'mejorF1': min(p[0] for p in puntos), 'mejorF2': min(p[1] for p in puntos),
                          'rodillaF1': rodilla['F1'], 'rodillaF2': rodilla['F2'],
                          'evaluaciones': r['evaluaciones'], 'segundos': r['segundos']})
            curva = [hipervolumen(h['frente'], ideal, nadir) for h in r['historia']]
            ejesConv[k].plot(range(1, len(curva) + 1), curva, color=colores[(r['semilla'] - 1) % 10], lw=0.9, alpha=0.8)
            frente = np.array(sorted(puntos))
            c = colores[(r['semilla'] - 1) % 10]
            ejesFrentes[k].plot(frente[:, 0], frente[:, 1], '-o', color=c, ms=3, lw=0.8, label=f'Semilla {r["semilla"]}')
            ejesFrentes[k].plot(rodilla['F1'], rodilla['F2'], '*', color=c, ms=11, mec='black', mew=0.5)
        curvas = np.array([[hipervolumen(h['frente'], ideal, nadir) for h in r['historia']] for r in resultados])
        ejesConv[k].plot(range(1, curvas.shape[1] + 1), curvas.mean(axis=0), color='black', lw=2.2, label='Promedio')
        ejesConv[k].set_title(nombres[escenario])
        ejesConv[k].set_xlabel('Generación')
        ejesConv[k].set_ylabel('Hipervolumen normalizado')
        ejesFrentes[k].set_title(nombres[escenario])
        ejesFrentes[k].set_xlabel('F1: distancia promedio (m)')
        ejesFrentes[k].set_ylabel('F2: tiempo de evacuación (s)')
        hv = np.array([f['hipervolumen'] for f in filas])
        media, desviacion = hv.mean(), hv.std(ddof=1)
        mitad = stats.t.ppf(0.975, len(hv) - 1) * desviacion / np.sqrt(len(hv))
        mediana = filas[int(np.argsort(hv)[len(hv) // 2])]['semilla']
        resumen[escenario] = {'nombre': nombres[escenario], 'semillas': filas, 'ideal': ideal.tolist(), 'nadir': nadir.tolist(),
                              'media': media, 'desviacion': desviacion, 'cv': desviacion / media, 'minimo': hv.min(),
                              'maximo': hv.max(), 'intervalo95': [media - mitad, media + mitad],
                              'repeticiones2': repeticionesNecesarias(hv, 0.02), 'repeticiones5': repeticionesNecesarias(hv, 0.05),
                              'semillaMediana': mediana,
                              'objetivos': {clave: {'media': float(np.mean([f[clave] for f in filas])),
                                                    'desviacion': float(np.std([f[clave] for f in filas], ddof=1)),
                                                    'repeticiones1': repeticionesNecesarias([f[clave] for f in filas], 0.01)}
                                            for clave in ('mejorF1', 'mejorF2', 'rodillaF1', 'rodillaF2')},
                              'evaluacionesPromedio': float(np.mean([f['evaluaciones'] for f in filas])),
                              'segundosPromedio': float(np.mean([f['segundos'] for f in filas]))}
        recinto, clases = cargarEscenario(f'escenarios/{escenario}.json')
        catalogo = Catalogo(recinto, clases)
        elegido = next(r for r in resultados if r['semilla'] == mediana)
        L = np.array(elegido['frente'][elegido['rodilla']]['cromosoma'])
        dibujarRecinto(ejesDist[k], recinto, catalogo, L)
        p = elegido['frente'][elegido['rodilla']]
        ejesDist[k].set_title(f'{nombres[escenario]}\nF1 = {p["F1"]:.2f} m, F2 = {p["F2"]:.1f} s')
        #Mapas de densidad de la distribucion elegida
        evaluador = Evaluador(recinto, catalogo)
        _, _, accesos = evaluador.violaciones(L)
        libre = recinto.omega0.copy()
        conteo, _, _, _ = evaluador.desplegar(L)
        libre &= conteo == 0
        tiempo, cuadros = evaluador.tiempoEvacuacion(libre, guardarCada=50)
        instantes = np.linspace(0, len(cuadros) - 1, 4).astype(int)
        figEv, ejesEv = plt.subplots(1, 4, figsize=(13, 2.9))
        for i, c in enumerate(instantes):
            dibujarRecinto(ejesEv[i], recinto, catalogo, L)
            densidad = np.ma.masked_where(~libre, cuadros[c])
            imagen = ejesEv[i].imshow(densidad, origin='lower', extent=(0, recinto.ancho, 0, recinto.largo), cmap='YlOrRd',
                                      vmin=0, vmax=5.4, interpolation='nearest', zorder=3)
            ejesEv[i].set_title(f't = {c * 50 * 0.3:.0f} s, dentro: {cuadros[c].sum():.0f}')
            ejesEv[i].set_xticks([])
            ejesEv[i].set_yticks([])
        figEv.colorbar(imagen, ax=ejesEv, fraction=0.015, label='personas/m²')
        figEv.savefig(f'resultados/figuras/evacuacion_{escenario}.png', dpi=200, bbox_inches='tight')
        plt.close(figEv)
    ejesFrentes[2].legend(fontsize=7, ncol=2, frameon=False, loc='upper right')
    ejesConv[2].legend(fontsize=8, frameon=False, loc='lower right')
    for figura, nombre in ((figFrentes, 'frentes'), (figConv, 'convergencia'), (figDist, 'distribuciones')):
        figura.tight_layout()
        figura.savefig(f'resultados/figuras/{nombre}.png', dpi=200, bbox_inches='tight')
        plt.close(figura)
    #Hipervolumen por semilla
    figHv, ejeHv = plt.subplots(figsize=(6.5, 3.4))
    for k, escenario in enumerate(escenarios):
        hv = [f['hipervolumen'] for f in resumen[escenario]['semillas']]
        ejeHv.scatter(np.full(len(hv), k) + np.linspace(-0.12, 0.12, len(hv)), hv, color='#4C78A8', s=18, zorder=3)
        bajo, alto = resumen[escenario]['intervalo95']
        ejeHv.errorbar(k + 0.3, resumen[escenario]['media'], yerr=[[resumen[escenario]['media'] - bajo], [alto - resumen[escenario]['media']]],
                       fmt='D', color='black', capsize=4, ms=5)
    ejeHv.set_xticks(range(3))
    ejeHv.set_xticklabels([nombres[e] for e in escenarios])
    ejeHv.set_ylabel('Hipervolumen normalizado')
    figHv.tight_layout()
    figHv.savefig('resultados/figuras/hipervolumen.png', dpi=200, bbox_inches='tight')
    plt.close(figHv)
    #Recintos de prueba
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
        print(f"{datos['nombre']}: HV medio {datos['media']:.4f}, CV {100 * datos['cv']:.2f} %, "
              f"repeticiones para 2 %: {datos['repeticiones2']}, para 5 %: {datos['repeticiones5']}")
