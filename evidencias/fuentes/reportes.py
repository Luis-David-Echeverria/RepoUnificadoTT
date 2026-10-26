import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

raiz = Path(__file__).resolve().parents[2]
figuras = raiz / 'resultados' / 'figuras'
repositorio = 'https://github.com/Luis-David-Echeverria/RepoUnificadoTT'

estilo = """
@page { size: A4; margin: 2.2cm 2.2cm 2.4cm 2.6cm; }
body { font-family: 'Times New Roman', 'Liberation Serif', serif; font-size: 11.5pt; line-height: 1.45; color: #111; text-align: justify; }
.encabezado { text-align: center; border-bottom: 1.5px solid #222; padding-bottom: 10px; margin-bottom: 14px; }
.encabezado .inst { font-weight: bold; font-size: 12.5pt; }
.encabezado .tt { font-size: 11pt; margin-top: 2px; }
h1 { font-size: 16pt; text-align: center; margin: 10px 0 4px; }
.subtitulo { text-align: center; font-style: italic; margin-bottom: 6px; }
.datos { font-size: 10.5pt; margin: 8px 0 4px; }
.datos td { border: none; padding: 1px 8px 1px 0; vertical-align: top; }
h2 { font-size: 13pt; margin: 18px 0 6px; break-after: avoid; }
p { margin: 0 0 8px; }
table { border-collapse: collapse; width: 100%; font-size: 9.8pt; margin: 4px 0 12px; text-align: left; }
th, td { border: 1px solid #555; padding: 3px 6px; vertical-align: top; }
th { background: #e4e4e4; }
td.num, th.num { text-align: right; }
.titulo { text-align: center; font-weight: bold; font-size: 10pt; margin-top: 10px; break-after: avoid; }
figure { margin: 10px 0 12px; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; }
figcaption { font-size: 10pt; font-weight: bold; margin-top: 4px; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 9.3pt; }
pre { font-family: 'DejaVu Sans Mono', monospace; font-size: 9pt; background: #f3f3f3; padding: 6px 8px; border: 1px solid #ccc; }
ul, ol { margin: 0 0 8px 0; padding-left: 22px; }
.refs p { padding-left: 2.2em; text-indent: -2.2em; font-size: 10.5pt; }
"""


def encabezado(titulo, subtitulo, responsable, commit):
    return f"""
<div class="encabezado">
  <div class="inst">Instituto Politécnico Nacional · Escuela Superior de Cómputo</div>
  <div class="tt">Trabajo Terminal 2027-A126 · «Prototipo de sistema para la distribución óptima de áreas de servicio en eventos masivos mediante algoritmos bioinspirados»</div>
</div>
<h1>{titulo}</h1>
<div class="subtitulo">{subtitulo}</div>
<table class="datos">
<tr><td><b>Periodo</b></td><td>13 al 26 de octubre de 2026</td></tr>
<tr><td><b>Responsable</b></td><td>{responsable}</td></tr>
<tr><td><b>Integrantes</b></td><td>Echeverría Pérez Luis David · Martínez Meneses Monserrat Alejandra</td></tr>
<tr><td><b>Directores</b></td><td>Dr. Daniel Molina Pérez · Dr. Jacobo Torres Figueroa</td></tr>
<tr><td><b>Código</b></td><td>{repositorio} (commit <code>{commit}</code>)</td></tr>
</table>"""


def figura(numero, archivo, texto, ancho=100):
    return f'<figure><img src="{(figuras / archivo).as_uri()}" style="width:{ancho}%"><figcaption>Figura {numero}. {texto}</figcaption></figure>'


def numero(valor, decimales=2):
    return f'{valor:,.{decimales}f}'


def reporteImplementacion(resumen, verificacion, commit):
    filasVerif = ''
    for clave, nombre in (('explanada', 'Explanada abierta'), ('plaza', 'Plaza con escenario'), ('salon', 'Salón con muro divisorio')):
        v = verificacion[clave]
        filasVerif += (f"<tr><td>{nombre}</td><td class='num'>{100 * v['validasAleatorias'] / v['muestras']:.1f} %</td>"
                       f"<td class='num'>{100 * v['validasConstruidas'] / v['muestras']:.1f} %</td>"
                       f"<td class='num'>{numero(v['msPorEvaluacion'], 1)}</td>"
                       f"<td class='num'>{numero(resumen[clave]['evaluacionesPromedio'], 0)}</td>"
                       f"<td class='num'>{numero(resumen[clave]['segundosPromedio'], 1)}</td></tr>")
    azar = [100 * verificacion[c]['validasAleatorias'] / verificacion[c]['muestras'] for c in verificacion]
    azarMin, azarMax = min(azar), max(azar)
    abiertoMin = min(100 * verificacion[c]['validasConstruidas'] / verificacion[c]['muestras'] for c in ('explanada', 'plaza'))
    cerrado = 100 * verificacion['salon']['validasConstruidas'] / verificacion['salon']['muestras']
    return f"""<html><head><meta charset="utf-8"><style>{estilo}</style></head><body>
{encabezado('Reporte de implementación del algoritmo',
            'Actividad 1: implementación del algoritmo bioinspirado, un algoritmo genético multiobjetivo con ordenamiento por no dominancia sobre las dos funciones objetivo',
            'Martínez Meneses Monserrat Alejandra', commit)}

<h2>1. Objetivo</h2>
<p>Implementar el algoritmo NSGA-II diseñado en el periodo anterior para buscar distribuciones de módulos que minimicen al mismo tiempo la distancia promedio a las áreas de servicio (F1) y el tiempo de evacuación (F2), respetando las seis restricciones del modelo. La implementación sigue las secciones 5.3 y 5.4 del reporte técnico [1].</p>

<h2>2. Alcance</h2>
<p>Lo que se entrega es el motor de optimización en Python, que se ejecuta desde la línea de comandos sobre recintos de prueba descritos en archivos JSON. Su propósito en TT1 es validar el modelo y medir cuánto cuesta cada corrida. La interfaz web, la API en FastAPI y la carga de recintos desde el editor forman parte del desarrollo de TT2.</p>

<h2>3. Organización del código</h2>
<div class="titulo">Tabla 1. Módulos del motor de optimización</div>
<table>
<tr><th>Archivo</th><th>Responsabilidad</th><th>Funciones principales</th></tr>
<tr><td><code>parametros.py</code></td><td>Parámetros de Weidmann, del SFPE, de la NOM-011 y del algoritmo</td><td><code>velocidadWeidmann</code></td></tr>
<tr><td><code>recinto.py</code></td><td>Malla de 1 m, muros y salidas en las aristas, celdas del recinto y franjas frente a las salidas</td><td><code>colocarMuro</code>, <code>clasificarCeldas</code>, <code>calcularFranjas</code></td></tr>
<tr><td><code>modulos.py</code></td><td>Módulos, giros, puertas y posiciones válidas</td><td><code>rotar</code>, <code>mascaraEstatica</code>, <code>posicionesValidas</code></td></tr>
<tr><td><code>eikonal.py</code></td><td>Fast Marching Method con muros en las aristas</td><td><code>resolverEikonal</code></td></tr>
<tr><td><code>evacuacion.py</code></td><td>Simulación de la evacuación</td><td><code>simularEvacuacion</code></td></tr>
<tr><td><code>evaluador.py</code></td><td>Violación total G, accesibilidad F1 y tiempo de evacuación F2</td><td><code>violaciones</code>, <code>accesibilidad</code>, <code>evaluar</code></td></tr>
<tr><td><code>nsga2.py</code></td><td>Algoritmo NSGA-II</td><td><code>construirIndividuo</code>, <code>reparar</code>, <code>ordenarNoDominados</code>, <code>ejecutar</code>, <code>puntoRodilla</code></td></tr>
</table>

<h2>4. Representación de una distribución</h2>
<p>Cada módulo se codifica con un gen g = (x, y, o): la celda de la esquina inferior izquierda del módulo ya girado y el número de giros de 90° en sentido antihorario. Una distribución es un arreglo de K × 3 enteros en el que la fila j corresponde siempre al módulo j. El tipo, las medidas y las puertas de cada módulo no forman parte del gen y se guardan en el catálogo (clase <code>Catalogo</code>).</p>
<p>Al girar un módulo también giran sus puertas. La función <code>rotar</code> calcula, para cada una de las cuatro orientaciones, las medidas del módulo, la arista de cada puerta y su celda de acceso.</p>

<h2>5. Evaluación de una distribución</h2>
<p>La clase <code>Evaluador</code> cuenta primero las violaciones de las seis restricciones de la sección 5.3.5 y las suma en G. Solo si G = 0 calcula F1 con el FMM desde las celdas de acceso de los módulos de cada tipo, y F2 con la simulación de la evacuación. Así no se gasta tiempo de cómputo en distribuciones que no se pueden entregar.</p>
<div class="titulo">Tabla 2. Implementación de las restricciones</div>
<table>
<tr><th>Restricción</th><th>Cómo se cuenta</th></tr>
<tr><td>1. Dentro del recinto y sin muros que atraviesen el módulo</td><td>Celdas del módulo fuera del recinto más aristas interiores del módulo con muro</td></tr>
<tr><td>2. Sin traslape</td><td>Celdas ocupadas por más de un módulo</td></tr>
<tr><td>3. Franja libre frente a las salidas</td><td>Celdas de módulos dentro de la franja de 2 m frente a cada salida</td></tr>
<tr><td>4. Puertas utilizables</td><td>Puertas con muro encima o con la celda de acceso fuera del recinto u ocupada</td></tr>
<tr><td>5. Paso de 2 m en espacios abiertos</td><td>Puertas desde las que un cuadro de 2 × 2 m no llega a una salida, solo si en el recinto vacío sí llegaba</td></tr>
<tr><td>6. Sin celdas encerradas</td><td>Celdas libres sin camino a una salida</td></tr>
</table>

<h2>6. Operadores del algoritmo</h2>
<div class="titulo">Tabla 3. Etapas de NSGA-II y su implementación</div>
<table>
<tr><th>Etapa</th><th>Función</th><th>Implementación</th></tr>
<tr><td>Población inicial</td><td><code>construirIndividuo</code></td><td>Coloca los módulos del más grande al más pequeño, cada uno en una posición y orientación válidas elegidas al azar. Si un módulo no cabe, reinicia hasta 50 veces.</td></tr>
<tr><td>Reparación</td><td><code>reparar</code></td><td>Recorre el cromosoma en orden. Conserva la posición heredada si es válida, y si no, busca la posición válida más cercana.</td></tr>
<tr><td>Ordenamiento</td><td><code>ordenarNoDominados</code>, <code>domina</code></td><td>Frentes por dominancia restringida: una distribución válida domina a una inválida, entre inválidas gana la de menor G y entre válidas se usa la dominancia de Pareto.</td></tr>
<tr><td>Diversidad</td><td><code>distanciaAglomeracion</code></td><td>Distancia de aglomeración dentro de cada frente.</td></tr>
<tr><td>Selección</td><td><code>torneoBinario</code></td><td>Gana el de mejor frente y, si empatan, el de mayor distancia de aglomeración.</td></tr>
<tr><td>Cruza</td><td><code>cruzaUniforme</code></td><td>Con probabilidad 0.9, cada módulo completo se toma al azar de uno de los dos padres.</td></tr>
<tr><td>Mutación</td><td><code>mutar</code></td><td>Cada módulo, con probabilidad 1/K, se desplaza hasta 3 celdas, se gira o se reubica al azar.</td></tr>
<tr><td>Reemplazo elitista</td><td><code>ejecutar</code></td><td>Se juntan padres e hijos y se conservan los mejores por frente y distancia de aglomeración.</td></tr>
<tr><td>Distribución final</td><td><code>puntoRodilla</code></td><td>Con los dos objetivos normalizados en el frente, la de menor suma.</td></tr>
</table>
<p>Las posiciones válidas de cada módulo se calculan una sola vez por recinto (<code>mascaraEstatica</code>), considerando que quede dentro del recinto, sin muros que lo atraviesen, fuera de la franja frente a las salidas y con sus puertas utilizables. Durante la construcción y la reparación solo falta revisar los módulos ya colocados, lo que se hace con una imagen integral en <code>posicionesValidas</code>. Las evaluaciones se guardan en memoria para no repetir el cálculo de una distribución que ya se evaluó.</p>

<h2>7. Parámetros</h2>
<div class="titulo">Tabla 4. Parámetros de NSGA-II en las primeras corridas</div>
<table>
<tr><th>Parámetro</th><th class="num">Valor</th><th>Origen</th></tr>
<tr><td>Tamaño de la población (P)</td><td class="num">40</td><td>Elegido para que una corrida tome alrededor de medio minuto</td></tr>
<tr><td>Generaciones (G<sub>max</sub>)</td><td class="num">50</td><td>Igual que el anterior</td></tr>
<tr><td>Probabilidad de cruza (p<sub>c</sub>)</td><td class="num">0.9</td><td>Valor usado por Deb et al. [2]</td></tr>
<tr><td>Probabilidad de mutación por módulo (p<sub>m</sub>)</td><td class="num">1/K = 1/6</td><td>Valor usado por Deb et al. [2]</td></tr>
<tr><td>Desplazamiento máximo en la mutación (r)</td><td class="num">3 celdas</td><td>Diseño</td></tr>
</table>

<h2>8. Verificación</h2>
<p>Se generaron 200 distribuciones por recinto de dos formas: colocando los módulos completamente al azar y con la construcción de la población inicial. La Tabla 5 muestra qué porcentaje cumplió las seis restricciones, el costo medio de una evaluación completa y el costo de las corridas del periodo, descritas en el reporte de las primeras corridas.</p>
<div class="titulo">Tabla 5. Distribuciones válidas y costo de evaluación</div>
<table>
<tr><th>Recinto</th><th class="num">Válidas al azar</th><th class="num">Válidas construidas</th><th class="num">ms por evaluación</th><th class="num">Evaluaciones por corrida</th><th class="num">Segundos por corrida</th></tr>
{filasVerif}
</table>
<p>Colocar los módulos completamente al azar solo produjo entre {azarMin:.1f} % y {azarMax:.1f} % de distribuciones válidas. Con la construcción de la población inicial (sección 5.4.2) el porcentaje sube a {abiertoMin:.1f} % o más en los recintos abiertos y a {cerrado:.1f} % en el cerrado. Las distribuciones construidas que no son válidas fallan únicamente en la restricción 5, el paso de 2 m hacia las salidas, que la construcción no revisa porque depende de todos los módulos a la vez. Esas distribuciones se ordenan por su violación total, y en las 30 corridas del periodo toda la población quedó formada por distribuciones válidas desde la primera generación. La Figura 1 muestra la distribución del punto de rodilla obtenida en una corrida de cada recinto.</p>
{figura(1, 'distribuciones.png', 'Distribución del punto de rodilla en cada recinto. Azul: sanitarios. Rojo: atención médica. Amarillo: puestos de comida. Las líneas gruesas negras sobre los módulos son sus puertas y las verdes, las salidas.')}

<h2>9. Ejecución</h2>
<pre>pip install -r requirements.txt
python verificacion.py
python corridas.py --semillas 10 --poblacion 40 --generaciones 50
python analisis.py</pre>

<h2>10. Siguientes pasos</h2>
<p>En TT2 el motor se conectará con la interfaz web mediante la API, se ajustarán P y G<sub>max</sub> con más corridas y recintos de mayor tamaño, y se evaluará en paralelo cada generación para reducir el tiempo de espera del usuario.</p>

<h2>Referencias</h2>
<div class="refs">
<p>[1] L. D. Echeverría Pérez y M. A. Martínez Meneses, «Prototipo de sistema para la distribución óptima de áreas de servicio en eventos masivos mediante algoritmos bioinspirados», Documento técnico de Trabajo Terminal 2027-A126, ESCOM, IPN, 2026.</p>
<p>[2] K. Deb, A. Pratap, S. Agarwal y T. Meyarivan, «A fast and elitist multiobjective genetic algorithm: NSGA-II», <i>IEEE Transactions on Evolutionary Computation</i>, vol. 6, no. 2, pp. 182–197, 2002.</p>
</div>
</body></html>"""


def reporteCorridas(resumen, verificacion, commit):
    nombres = {'explanada': 'Explanada abierta', 'plaza': 'Plaza con escenario', 'salon': 'Salón con muro divisorio'}
    filasSemillas = ''
    for clave, nombre in nombres.items():
        for f in resumen[clave]['semillas']:
            filasSemillas += (f"<tr><td>{nombre}</td><td class='num'>{f['semilla']}</td><td class='num'>{f['puntos']}</td>"
                              f"<td class='num'>{numero(f['mejorF1'])}</td><td class='num'>{numero(f['mejorF2'], 1)}</td>"
                              f"<td class='num'>{numero(f['rodillaF1'])} m, {numero(f['rodillaF2'], 1)} s</td>"
                              f"<td class='num'>{numero(f['hipervolumen'], 3)}</td></tr>")
    filasResumen = ''
    filasRepeticiones = ''
    for clave, nombre in nombres.items():
        d = resumen[clave]
        filasResumen += (f"<tr><td>{nombre}</td><td class='num'>{numero(d['media'], 3)}</td><td class='num'>{numero(d['desviacion'], 3)}</td>"
                         f"<td class='num'>{100 * d['cv']:.1f} %</td><td class='num'>[{numero(d['intervalo95'][0], 3)}, {numero(d['intervalo95'][1], 3)}]</td>"
                         f"<td class='num'>{numero(d['minimo'], 3)}</td><td class='num'>{numero(d['maximo'], 3)}</td></tr>")
    filasRecintos = ''
    descripciones = {'explanada': ('Abierto', 'Sin muros interiores', '2 (4 m y 2 m)'),
                     'plaza': ('Abierto', 'Escenario de 8 × 3 m cerrado con muros', '3 (3 m, 3 m y 2 m)'),
                     'salon': ('Cerrado', 'Muro divisorio de 13 m con un paso de 7 m', '3 (2 m, 2 m y 3 m)')}
    for clave, nombre in nombres.items():
        v = verificacion[clave]
        tipo, interior, salidas = descripciones[clave]
        filasRecintos += (f"<tr><td>{nombre}</td><td>{tipo}</td><td>{interior}</td><td>{salidas}</td>"
                          f"<td class='num'>{v['areaRecinto']} m²</td><td class='num'>{v['aforo']}</td><td class='num'>{v['aforoMaximo']}</td></tr>")
    filasObjetivos = ''
    for clave, nombre in nombres.items():
        o = resumen[clave]['objetivos']
        filasObjetivos += (f"<tr><td>{nombre}</td>" + ''.join(
            f"<td class='num'>{numero(o[k]['media'], 2 if 'F1' in k else 1)} ± {numero(o[k]['desviacion'], 2 if 'F1' in k else 1)}</td>"
            for k in ('mejorF1', 'mejorF2', 'rodillaF1', 'rodillaF2')) + "</tr>")
    filasRepeticiones = ''
    for clave, nombre in nombres.items():
        d = resumen[clave]
        rodilla = max(d['objetivos']['rodillaF1']['repeticiones1'], d['objetivos']['rodillaF2']['repeticiones1'])
        filasRepeticiones += (f"<tr><td>{nombre}</td><td class='num'>{d['repeticiones5']}</td><td class='num'>{d['repeticiones2']}</td>"
                              f"<td class='num'>{rodilla}</td></tr>")
    rangoF1 = resumen['explanada']['nadir'][0] - resumen['explanada']['ideal'][0]
    rangoF2 = resumen['explanada']['nadir'][1] - resumen['explanada']['ideal'][1]
    variacionF1 = max(100 * (max(f['mejorF1'] for f in resumen[c]['semillas']) - min(f['mejorF1'] for f in resumen[c]['semillas']))
                      / resumen[c]['objetivos']['mejorF1']['media'] for c in nombres)
    repExplanada = resumen['explanada']['repeticiones5']
    segMin = min(f['segundos'] for c in nombres for f in resumen[c]['semillas'])
    segMax = max(f['segundos'] for c in nombres for f in resumen[c]['semillas'])
    maximo5 = max(resumen[c]['repeticiones5'] for c in nombres)
    maximo2 = max(resumen[c]['repeticiones2'] for c in nombres)
    cvs = [100 * resumen[c]['cv'] for c in nombres]
    totalEval = sum(f['evaluaciones'] for c in nombres for f in resumen[c]['semillas'])
    totalSeg = sum(f['segundos'] for c in nombres for f in resumen[c]['semillas'])
    return f"""<html><head><meta charset="utf-8"><style>{estilo}</style></head><body>
{encabezado('Reporte de las primeras corridas',
            'Actividad 2: implementación del motor de optimización, primeras corridas con repeticiones independientes y análisis de la variabilidad entre semillas',
            'Echeverría Pérez Luis David', commit)}

<h2>1. Objetivo</h2>
<p>Ejecutar el motor de optimización con varias semillas sobre los mismos recintos para medir cuánto cambia el resultado de una corrida a otra, y con ello determinar cuántas repeticiones hacen falta para que un resultado sea concluyente. El modelo y el algoritmo son los de las secciones 5.3 y 5.4 del reporte técnico [1], implementados como se describe en el reporte de implementación del algoritmo.</p>

<h2>2. Recintos de prueba</h2>
<p>Se usaron tres recintos de 30 × 20 m con la misma lista de módulos: dos baterías sanitarias de 3 × 2 m con dos puertas, una carpa médica de 3 × 3 m con una puerta y tres puestos de comida de 2 × 2 m con dos puertas, es decir, K = 6 módulos y 33 m². El aforo es de 800 personas en los tres casos, por debajo del aforo máximo que resulta del factor de 0.55 m² por persona.</p>
<div class="titulo">Tabla 1. Recintos de prueba</div>
<table>
<tr><th>Recinto</th><th>Tipo</th><th>Interior</th><th>Salidas</th><th class="num">Área</th><th class="num">Aforo</th><th class="num">Aforo máximo</th></tr>
{filasRecintos}
</table>
{figura(1, 'recintos.png', 'Recintos de prueba. Negro: muros. Verde: salidas. Gris oscuro: zona inaccesible.')}

<h2>3. Configuración de las corridas</h2>
<p>Para cada recinto se hicieron 10 corridas independientes, con semillas de 1 a 10, población de 40 y 50 generaciones. En total fueron 30 corridas, {numero(totalEval, 0)} evaluaciones y {numero(totalSeg / 60, 1)} minutos de cómputo en un servidor de dos núcleos.</p>
<p>Para comparar los frentes se usó el hipervolumen [2], el área del espacio de objetivos que domina un frente hasta un punto de referencia. Mientras mayor es, mejor es el frente, porque está más cerca de los mínimos de ambos objetivos y los cubre mejor. En cada recinto los objetivos se normalizaron con el mínimo y el máximo de todos los frentes finales, y el punto de referencia fue (1.1, 1.1).</p>

<h2>4. Frentes obtenidos en cada repetición</h2>
{figura(2, 'frentes.png', 'Frente final de cada semilla. La estrella marca la distribución del punto de rodilla.')}
<div class="titulo">Tabla 2. Resultados por semilla</div>
<table>
<tr><th>Recinto</th><th class="num">Semilla</th><th class="num">Puntos</th><th class="num">Mejor F1 (m)</th><th class="num">Mejor F2 (s)</th><th class="num">Rodilla</th><th class="num">Hipervolumen</th></tr>
{filasSemillas}
</table>

<h2>5. Variabilidad entre semillas</h2>
<div class="titulo">Tabla 3. Hipervolumen final por recinto</div>
<table>
<tr><th>Recinto</th><th class="num">Media</th><th class="num">Desviación</th><th class="num">CV</th><th class="num">IC 95 % de la media</th><th class="num">Mínimo</th><th class="num">Máximo</th></tr>
{filasResumen}
</table>
{figura(3, 'hipervolumen.png', 'Hipervolumen final de cada semilla (puntos) y media con su intervalo de confianza del 95 % (rombo).', 75)}
<p>El coeficiente de variación del hipervolumen fue de {cvs[1]:.1f} % en la Plaza con escenario y de {cvs[2]:.1f} % en el Salón, pero de {cvs[0]:.1f} % en la Explanada abierta. La diferencia no se debe a que las corridas de la Explanada encuentren distribuciones muy distintas, sino a que sus frentes son muy angostos: todos caben en {rangoF1:.2f} m de F1 y {rangoF2:.1f} s de F2. Al normalizar con rangos tan pequeños, diferencias de centímetros pesan mucho en el hipervolumen.</p>
<p>Los valores de los objetivos son mucho más estables (Tabla 4). En los tres recintos las 10 semillas llegaron al mismo tiempo de evacuación mínimo, y la mejor distancia promedio varió menos de {variacionF1:.1f} % entre semillas.</p>
<div class="titulo">Tabla 4. Valores de los objetivos entre semillas (media ± desviación estándar)</div>
<table>
<tr><th>Recinto</th><th class="num">Mejor F1 (m)</th><th class="num">Mejor F2 (s)</th><th class="num">F1 de la rodilla (m)</th><th class="num">F2 de la rodilla (s)</th></tr>
{filasObjetivos}
</table>
{figura(4, 'convergencia.png', 'Hipervolumen del frente de la población en cada generación. Líneas delgadas: semillas. Línea gruesa: promedio.')}
<p>La Figura 4 muestra que el hipervolumen promedio sigue creciendo en la generación 50 en los tres recintos. Es decir, con 2,000 evaluaciones el algoritmo todavía no termina de converger, y parte de la variabilidad entre semillas viene de que cada corrida se detiene en un punto distinto de su avance. En la Explanada el hipervolumen es cero en las primeras generaciones porque esos frentes quedan fuera del punto de referencia, definido con los frentes finales.</p>

<h2>6. Repeticiones necesarias</h2>
<p>Se considera que un resultado es concluyente cuando el intervalo de confianza del 95 % de la media tiene una semiamplitud menor a un porcentaje e de la media. Con la desviación estándar medida, el número de repeticiones n es el menor que cumple t<sub>0.975, n−1</sub> · s / √n ≤ e · media.</p>
<div class="titulo">Tabla 5. Repeticiones necesarias por recinto</div>
<table>
<tr><th>Recinto</th><th class="num">Hipervolumen, e = 5 %</th><th class="num">Hipervolumen, e = 2 %</th><th class="num">Objetivos de la rodilla, e = 1 %</th></tr>
{filasRepeticiones}
</table>
<p>Con 10 repeticiones el hipervolumen medio queda estimado con un error menor al 5 % en la Plaza y en el Salón, y los valores de los objetivos con un error menor al 1 % en los tres recintos. La Explanada necesitaría {repExplanada} repeticiones para el mismo error en el hipervolumen, lo que indica que con frentes tan angostos el hipervolumen normalizado no es una buena medida para comparar corridas. Por ello, para los experimentos de TT2 se usarán al menos 10 repeticiones por configuración, se reportarán junto al hipervolumen los valores de los objetivos y se repetirá este análisis después de aumentar el número de generaciones.</p>

<h2>7. Distribuciones obtenidas</h2>
<p>La Figura 5 muestra la simulación de la evacuación de la distribución del punto de rodilla en la Plaza con escenario, en cuatro instantes. Las Figuras 6 y 7 muestran lo mismo para los otros dos recintos. Las mayores densidades aparecen frente a las salidas, que son el cuello de botella de la evacuación, y los módulos quedan fuera de las franjas de 2 m frente a ellas.</p>
{figura(5, 'evacuacion_plaza.png', 'Evacuación de la distribución de rodilla en la Plaza con escenario.')}
{figura(6, 'evacuacion_explanada.png', 'Evacuación de la distribución de rodilla en la Explanada abierta.')}
{figura(7, 'evacuacion_salon.png', 'Evacuación de la distribución de rodilla en el Salón con muro divisorio.')}

<h2>8. Conclusiones</h2>
<ul>
<li>El motor completó las 30 corridas y en todas entregó distribuciones válidas, con un costo de entre {segMin:.0f} y {segMax:.0f} segundos por corrida.</li>
<li>Las semillas llegan a valores de los objetivos muy parecidos: el mismo tiempo de evacuación mínimo y diferencias menores al {variacionF1:.1f} % en la distancia promedio.</li>
<li>Los frentes son angostos en recintos de 30 × 20 m con seis módulos, por lo que en recintos pequeños el compromiso entre accesibilidad y evacuación es moderado.</li>
<li>Con 50 generaciones el hipervolumen sigue creciendo, así que en TT2 se aumentará el presupuesto de evaluaciones antes de fijar los parámetros.</li>
<li>Se usarán al menos 10 repeticiones por configuración, y el análisis se repetirá con recintos más grandes, más módulos y el nuevo presupuesto.</li>
</ul>

<h2>Referencias</h2>
<div class="refs">
<p>[1] L. D. Echeverría Pérez y M. A. Martínez Meneses, «Prototipo de sistema para la distribución óptima de áreas de servicio en eventos masivos mediante algoritmos bioinspirados», Documento técnico de Trabajo Terminal 2027-A126, ESCOM, IPN, 2026.</p>
<p>[2] E. Zitzler y L. Thiele, «Multiobjective evolutionary algorithms: a comparative case study and the strength Pareto approach», <i>IEEE Transactions on Evolutionary Computation</i>, vol. 3, no. 4, pp. 257–271, 1999.</p>
</div>
</body></html>"""


def imprimir(html, destino):
    origen = destino.parent / 'fuentes' / destino.with_suffix('.html').name
    origen.write_text(html, encoding='utf-8')
    pie = '<div style="width:100%; font-size:9px; text-align:center; font-family:serif;"><span class="pageNumber"></span></div>'
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page()
        pagina.goto(origen.as_uri())
        pagina.pdf(path=str(destino), format='A4', print_background=True, display_header_footer=True,
                   header_template='<div></div>', footer_template=pie,
                   margin={'top': '2.2cm', 'bottom': '2.4cm', 'left': '2.6cm', 'right': '2.2cm'})
        navegador.close()


if __name__ == '__main__':
    commit = sys.argv[1]
    resumen = json.loads((raiz / 'resultados' / 'resumen.json').read_text(encoding='utf-8'))
    verificacion = json.loads((raiz / 'resultados' / 'verificacion.json').read_text(encoding='utf-8'))
    salida = raiz / 'evidencias'
    imprimir(reporteImplementacion(resumen, verificacion, commit), salida / 'Periodo3-1-Implementacion-del-algoritmo.pdf')
    imprimir(reporteCorridas(resumen, verificacion, commit), salida / 'Periodo3-2-Primeras-corridas.pdf')
