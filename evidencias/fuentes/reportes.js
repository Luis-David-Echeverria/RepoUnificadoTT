const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  BorderStyle, ShadingType, HeadingLevel, Footer, PageNumber, VerticalAlign, LevelFormat, TableLayoutType
} = require('docx');

const raiz = path.resolve(process.argv[2] || path.join(__dirname, '..', '..'));
const figuras = path.join(raiz, 'resultados', 'figuras');
const resumen = JSON.parse(fs.readFileSync(path.join(raiz, 'resultados', 'resumen.json'), 'utf8'));
const verificacion = JSON.parse(fs.readFileSync(path.join(raiz, 'resultados', 'verificacion.json'), 'utf8'));
const repositorio = 'https://github.com/Luis-David-Echeverria/RepoUnificadoTT';
const nombres = { explanada: 'Explanada abierta', plaza: 'Plaza con escenario', salon: 'Salón con muro divisorio' };
const cortos = { explanada: 'Explanada', plaza: 'Plaza', salon: 'Salón' };
const claves = Object.keys(nombres);
const anchoTexto = 9071;
const fuente = 'Times New Roman';

function numero(valor, decimales = 2) {
  return valor.toLocaleString('en-US', { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
}

//Convertir texto con `codigo`, _cursiva_ y ~subindice~ en fragmentos
function fragmentos(texto, base = {}) {
  const partes = [];
  const patron = /(`[^`]+`|_[^_]+_|~[^~]+~)/g;
  let ultimo = 0;
  for (const m of texto.matchAll(patron)) {
    if (m.index > ultimo) partes.push(new TextRun({ text: texto.slice(ultimo, m.index), ...base }));
    const t = m[0];
    if (t.startsWith('`')) partes.push(new TextRun({ text: t.slice(1, -1), font: 'Consolas', size: 20, ...base }));
    else if (t.startsWith('_')) partes.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    else partes.push(new TextRun({ text: t.slice(1, -1), subScript: true, ...base }));
    ultimo = m.index + t.length;
  }
  if (ultimo < texto.length) partes.push(new TextRun({ text: texto.slice(ultimo), ...base }));
  return partes;
}

function parrafo(texto, opciones = {}) {
  return new Paragraph({
    alignment: opciones.alineacion || AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 300 },
    keepNext: opciones.keepNext,
    children: fragmentos(texto, opciones.formato || {})
  });
}

function titulo(texto) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(texto)] });
}

function tituloTabla(texto) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 80 },
    children: [new TextRun({ text: texto, bold: true, size: 20 })]
  });
}

const borde = { style: BorderStyle.SINGLE, size: 4, color: '555555' };
const bordes = { top: borde, bottom: borde, left: borde, right: borde };

function celda(texto, ancho, opciones = {}) {
  return new TableCell({
    width: { size: ancho, type: WidthType.DXA },
    borders: bordes,
    verticalAlign: VerticalAlign.CENTER,
    shading: opciones.encabezado ? { type: ShadingType.CLEAR, color: 'auto', fill: 'D9D9D9' } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({
      alignment: opciones.derecha ? AlignmentType.RIGHT : AlignmentType.LEFT,
      keepNext: opciones.keepNext,
      children: fragmentos(String(texto), { size: opciones.tamano || 19, bold: !!opciones.encabezado })
    })]
  });
}

//Tabla con encabezado gris y columnas numericas a la derecha
function tabla(encabezados, filas, proporciones, numericas = [], tamano = 19) {
  const suma = proporciones.reduce((a, b) => a + b, 0);
  const anchos = proporciones.map(p => Math.floor(anchoTexto * p / suma));
  anchos[anchos.length - 1] += anchoTexto - anchos.reduce((a, b) => a + b, 0);
  const renglones = [new TableRow({
    tableHeader: true, cantSplit: true,
    children: encabezados.map((t, i) => celda(t, anchos[i], { encabezado: true, derecha: numericas.includes(i), tamano, keepNext: true }))
  })];
  filas.forEach((fila, r) => renglones.push(new TableRow({
    cantSplit: true,
    children: fila.map((t, i) => celda(t, anchos[i], { derecha: numericas.includes(i), tamano, keepNext: r < filas.length - 1 && filas.length < 12 }))
  })));
  return [new Table({ width: { size: anchoTexto, type: WidthType.DXA }, columnWidths: anchos, layout: TableLayoutType.FIXED, rows: renglones }),
    new Paragraph({ spacing: { after: 120 }, children: [] })];
}

function tamanoPng(ruta) {
  const datos = fs.readFileSync(ruta);
  return { ancho: datos.readUInt32BE(16), alto: datos.readUInt32BE(20), datos };
}

//Figura con su pie debajo
function figura(archivo, pie, proporcion = 1) {
  const { ancho, alto, datos } = tamanoPng(path.join(figuras, archivo));
  const anchoPx = Math.round(605 * proporcion);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: 'png', data: datos, transformation: { width: anchoPx, height: Math.round(anchoPx * alto / ancho) } })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: fragmentos(pie, { bold: true, size: 20 })
    })
  ];
}

function referencias(lista) {
  return lista.map((r, i) => new Paragraph({
    alignment: AlignmentType.LEFT, spacing: { after: 80 }, indent: { left: 500, hanging: 500 },
    children: fragmentos(`[${i + 1}] ${r}`, { size: 21 })
  }));
}

function encabezado(tituloReporte, actividad, responsable) {
  const sinBorde = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
  const sinBordes = { top: sinBorde, bottom: sinBorde, left: sinBorde, right: sinBorde };
  const datos = [['Periodo', '13 al 26 de octubre de 2026'], ['Responsable', responsable],
    ['Integrantes', 'Echeverría Pérez Luis David y Martínez Meneses Monserrat Alejandra'],
    ['Directores', 'Dr. Daniel Molina Pérez y Dr. Jacobo Torres Figueroa'], ['Código', repositorio]];
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'Instituto Politécnico Nacional', bold: true, size: 26 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'Escuela Superior de Cómputo', bold: true, size: 24 })] }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 120 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: '222222', space: 6 } },
      children: [new TextRun({ text: 'Trabajo Terminal 2027-A126. «Prototipo de sistema para la distribución óptima de áreas de servicio en eventos masivos mediante algoritmos bioinspirados»', size: 21 })]
    }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 80 }, children: [new TextRun({ text: tituloReporte, bold: true, size: 32 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: actividad, italics: true, size: 22 })] }),
    new Table({
      width: { size: anchoTexto, type: WidthType.DXA }, columnWidths: [1700, anchoTexto - 1700], layout: TableLayoutType.FIXED,
      rows: datos.map(([etiqueta, valor]) => new TableRow({
        children: [
          new TableCell({ width: { size: 1700, type: WidthType.DXA }, borders: sinBordes, children: [new Paragraph({ children: [new TextRun({ text: etiqueta, bold: true, size: 21 })] })] }),
          new TableCell({ width: { size: anchoTexto - 1700, type: WidthType.DXA }, borders: sinBordes, children: [new Paragraph({ children: [new TextRun({ text: valor, size: 21 })] })] })
        ]
      }))
    }),
    new Paragraph({ spacing: { after: 120 }, children: [] })
  ];
}

function codigo(lineas) {
  return lineas.map((l, i) => new Paragraph({
    shading: { type: ShadingType.CLEAR, color: 'auto', fill: 'F2F2F2' },
    spacing: { after: i === lineas.length - 1 ? 160 : 0 },
    keepNext: i < lineas.length - 1,
    keepLines: true,
    children: [new TextRun({ text: l, font: 'Consolas', size: 19 })]
  }));
}

function documento(secciones) {
  return new Document({
    styles: {
      default: { document: { run: { font: fuente, size: 24 } } },
      paragraphStyles: [{
        id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: fuente, size: 26, bold: true }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 0 }
      }]
    },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1247, bottom: 1361, left: 1474, right: 1361 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
      children: secciones.flat()
    }]
  });
}

const refDeb = 'K. Deb, A. Pratap, S. Agarwal y T. Meyarivan, «A fast and elitist multiobjective genetic algorithm: NSGA-II», _IEEE Transactions on Evolutionary Computation_, vol. 6, no. 2, pp. 182–197, 2002.';
const refNom = 'Secretaría de Seguridad y Protección Ciudadana, «Proyecto de Norma Oficial Mexicana PROY-NOM-011-SSPC-2025», _Diario Oficial de la Federación_, México, 17 de septiembre de 2025.';
const refDas = 'I. Das, «On characterizing the "knee" of the Pareto curve based on normal-boundary intersection», _Structural Optimization_, vol. 18, no. 2, pp. 107–115, 1999.';
const refSfpe = 'S. M. V. Gwynne y E. R. Rosenbaum, «Employing the hydraulic model in assessing emergency movement», en _SFPE Handbook of Fire Protection Engineering_, 5.ª ed., M. J. Hurley, Ed. Nueva York: Springer, 2016, pp. 2115–2151.';
const refBranke = 'J. Branke, K. Deb, H. Dierolf y M. Osswald, «Finding knees in multi-objective optimization», en _Parallel Problem Solving from Nature, PPSN VIII_, LNCS 3242. Berlín: Springer, 2004, pp. 722–731.';

//Reporte de implementacion del algoritmo
function reporteImplementacion() {
  const filas = claves.map(c => {
    const v = verificacion[c];
    const generaciones = resumen[c].semillas.map(f => f.generacionTodasValidas);
    return [nombres[c], `${(100 * v.validasAleatorias / v.muestras).toFixed(1)} %`, `${(100 * v.validasConstruidas / v.muestras).toFixed(1)} %`,
      numero(resumen[c].evaluacionesPromedio, 0), Math.max(...generaciones), numero(resumen[c].segundosPromedio, 0)];
  });
  const totalMuestras = claves.reduce((s, c) => s + verificacion[c].muestras, 0);
  const totalAzar = claves.reduce((s, c) => s + verificacion[c].validasAleatorias, 0);
  const frasesAzar = totalAzar === 0 ? `Ninguna de las ${totalMuestras} distribuciones con los módulos completamente al azar fue válida.`
    : `De las ${totalMuestras} distribuciones con los módulos completamente al azar solo ${totalAzar} fueron válidas.`;
  const construidas = c => `${(100 * verificacion[c].validasConstruidas / verificacion[c].muestras).toFixed(1)} %`;
  const evaluacionesPromedio = claves.reduce((s, c) => s + resumen[c].evaluacionesPromedio, 0) / claves.length;
  const peorGeneracion = Math.max(...claves.flatMap(c => resumen[c].semillas.map(f => f.generacionTodasValidas)));
  const segundos = claves.map(c => resumen[c].segundosPromedio);
  return documento([
    encabezado('Reporte de implementación del algoritmo',
      'Implementación del algoritmo bioinspirado: algoritmo genético multiobjetivo con ordenamiento por no dominancia sobre las dos funciones objetivo',
      'Martínez Meneses Monserrat Alejandra'),
    titulo('1. Objetivo'),
    parrafo('Programar el algoritmo genético multiobjetivo NSGA-II [1] para acomodar módulos de servicio en un recinto. El algoritmo busca minimizar al mismo tiempo la distancia promedio que caminan los asistentes hasta cada tipo de servicio (F1) y el tiempo de evacuación (F2), y solo acepta distribuciones que cumplen las seis restricciones del modelo.'),
    titulo('2. Organización del código'),
    parrafo('El motor está escrito en Python y se ejecuta desde la línea de comandos. Cada recinto se describe en un archivo JSON con sus medidas, muros, salidas, aforo y módulos.'),
    tituloTabla('Tabla 1. Archivos del motor de optimización'),
    tabla(['Archivo', 'Qué hace', 'Funciones principales'], [
      ['`parametros.py`', 'Guarda los parámetros de Weidmann, del SFPE, de la norma y del algoritmo', '`velocidadWeidmann`'],
      ['`recinto.py`', 'Arma la malla de 1 m con muros y salidas en las aristas, y encuentra las celdas del recinto y las franjas frente a las salidas', '`colocarMuro`, `clasificarCeldas`, `calcularFranjas`'],
      ['`modulos.py`', 'Gira los módulos con sus puertas y calcula dónde puede ir cada uno', '`rotar`, `mascaraEstatica`, `posicionesValidas`'],
      ['`eikonal.py`', 'Resuelve la ecuación eikonal con el Fast Marching Method', '`resolverEikonal`'],
      ['`evacuacion.py`', 'Simula la evacuación', '`simularEvacuacion`'],
      ['`evaluador.py`', 'Calcula la violación total G, la accesibilidad F1 y el tiempo de evacuación F2', '`violaciones`, `accesibilidad`, `evaluar`'],
      ['`nsga2.py`', 'Contiene el algoritmo NSGA-II', '`construirIndividuo`, `reparar`, `ordenarNoDominados`, `ejecutar`, `puntoRodilla`']
    ], [2, 5, 4]),
    titulo('3. Representación de una distribución'),
    parrafo('Cada módulo se codifica con un gen g = (x, y, o), donde (x, y) es la celda de la esquina inferior izquierda del módulo ya girado y o es el número de giros de 90° en sentido antihorario. Una distribución es un arreglo de K × 3 enteros en el que la fila j corresponde siempre al módulo j. El tipo, las medidas y las puertas de cada módulo no van en el gen. Se guardan aparte, en la clase `Catalogo`.'),
    parrafo('Las puertas giran con el módulo. La función `rotar` calcula, para cada una de las cuatro orientaciones, las medidas del módulo, la arista de cada puerta y la celda de acceso que queda afuera de ella.'),
    titulo('4. Evaluación de una distribución'),
    parrafo('La clase `Evaluador` cuenta primero las violaciones de las seis restricciones y las suma en G. Solo cuando G = 0 calcula los dos objetivos, para no gastar tiempo en distribuciones que no se pueden entregar.'),
    parrafo('F1 es el promedio, sobre los tres tipos de servicio, de la distancia de cada celda libre al módulo más cercano de ese tipo, como en el problema de la p-mediana [2]. La distancia se mide desde la celda de acceso de cada puerta con el Fast Marching Method [3], así que rodea muros y módulos. F2 es el tiempo que pasa hasta que queda menos de una persona en el recinto. Sale de una simulación en la que la multitud se mueve hacia las salidas por la ruta más rápida, como en el modelo de Hughes [4], con la velocidad que da el diagrama de Weidmann [5] según la densidad de cada celda. El paso de personas entre celdas sigue el modelo de transmisión de celdas [6] y cada salida deja pasar 1.32 personas por metro por segundo, descontando 15 cm a cada lado [7].'),
    tituloTabla('Tabla 2. Cómo se cuenta cada restricción'),
    tabla(['Restricción', 'Suma 1 por cada'], [
      ['1. El módulo queda dentro del recinto y ningún muro lo atraviesa', 'Celda del módulo fuera del recinto y arista interior del módulo con muro'],
      ['2. Los módulos no se enciman', 'Celda ocupada por más de un módulo'],
      ['3. Franja libre de 2 m frente a cada salida [8]', 'Celda de un módulo dentro de la franja'],
      ['4. Las puertas se pueden usar', 'Puerta con muro encima o con su celda de acceso fuera del recinto u ocupada'],
      ['5. En espacios abiertos, paso de 2 m hasta una salida [8]', 'Puerta desde la que un cuadro de 2 × 2 m no llega a una salida, si en el recinto vacío sí llegaba'],
      ['6. Los módulos no encierran zonas [8]', 'Celda libre sin camino a una salida']
    ], [1, 1]),
    titulo('5. Operadores del algoritmo'),
    tituloTabla('Tabla 3. Etapas de NSGA-II y cómo se programaron'),
    tabla(['Etapa', 'Función', 'Qué hace'], [
      ['Población inicial', '`construirIndividuo`', 'Coloca los módulos del más grande al más pequeño, cada uno en una posición y orientación válidas elegidas al azar, como en la fase de construcción de GRASP [9]. Si un módulo no cabe, vuelve a empezar, hasta 50 veces.'],
      ['Reparación', '`reparar`', 'Recorre los módulos en el orden del cromosoma. Deja cada uno donde quedó si su posición es válida y, si no, lo mueve a la posición válida más cercana [10].'],
      ['Ordenamiento', '`ordenarNoDominados`, `domina`', 'Separa la población en frentes con dominancia restringida [1]. Una distribución válida gana a una inválida, entre dos inválidas gana la de menor G y entre dos válidas se aplica la dominancia de Pareto.'],
      ['Diversidad', '`distanciaAglomeracion`', 'Calcula la distancia de aglomeración dentro de cada frente [1].'],
      ['Selección', '`torneoBinario`', 'Toma dos distribuciones al azar y gana la de mejor frente. Si empatan, gana la de mayor distancia de aglomeración.'],
      ['Cruza', '`cruzaUniforme`', 'Con probabilidad 0.9, cada hijo toma cada módulo completo de uno de los dos padres, al azar [11].'],
      ['Mutación', '`mutar`', 'Cada módulo, con probabilidad 1/K, se mueve hasta 3 celdas, se gira o se cambia a un lugar al azar.'],
      ['Reemplazo elitista', '`ejecutar`', 'Junta padres e hijos y se queda con los mejores según su frente y su distancia de aglomeración [1].'],
      ['Distribución final', '`puntoRodilla`', 'Normaliza los dos objetivos con los valores del frente y elige la de menor suma [12], [13].']
    ], [2, 3.6, 6]),
    parrafo('Las posiciones que cumplen las restricciones de cada módulo por sí solo se calculan una vez por recinto en `mascaraEstatica`. Durante la construcción y la reparación solo falta revisar los módulos ya colocados, y `posicionesValidas` lo hace con una imagen integral para no revisar celda por celda. Además, cada distribución evaluada se guarda en memoria para no calcularla dos veces.'),
    titulo('6. Parámetros'),
    tituloTabla('Tabla 4. Parámetros de NSGA-II'),
    tabla(['Parámetro', 'Valor', 'Origen'], [
      ['Tamaño de la población (P)', '40', 'Elegido para que una corrida dure alrededor de un minuto'],
      ['Generaciones (G~max~)', '60', 'Igual que el anterior'],
      ['Probabilidad de cruza (p~c~)', '0.9', 'Valor usado en [1]'],
      ['Probabilidad de mutación por módulo (p~m~)', '1/K = 1/15', 'Valor usado en [1]'],
      ['Desplazamiento máximo en la mutación', '3 celdas', 'Elegido para mover un módulo sin sacarlo de su zona']
    ], [5, 2, 5], [1]),
    titulo('7. Verificación'),
    parrafo('Se probó el algoritmo en tres recintos de 30 × 20 m con 15 módulos cada uno: cinco baterías sanitarias, dos carpas médicas y ocho puestos de comida. En cada recinto se generaron 200 distribuciones de dos formas, con los módulos puestos completamente al azar y con la construcción de la población inicial. Después se hicieron 10 corridas por recinto.'),
    tituloTabla('Tabla 5. Distribuciones válidas, costo y avance de las corridas'),
    tabla(['Recinto', 'Válidas al azar', 'Válidas construidas', 'Evaluaciones por corrida', 'Generación con toda la población válida (peor corrida)', 'Segundos por corrida'],
      filas, [3, 2, 2, 2.2, 3, 2], [1, 2, 3, 4, 5]),
    parrafo(`${frasesAzar} Con la construcción de la población inicial fueron válidas el ${construidas('explanada')} en la Explanada, el ${construidas('plaza')} en la Plaza y el ${construidas('salon')} en el Salón. En los recintos abiertos casi todas las que fallan lo hacen en la restricción 5, el paso de 2 m hasta las salidas, que la construcción no revisa porque depende de todos los módulos a la vez. El ordenamiento por violación las va corrigiendo, y en ninguna corrida pasaron más de ${peorGeneracion} generaciones antes de que toda la población fuera válida. Cada corrida hizo en promedio unas ${numero(evaluacionesPromedio, 0)} evaluaciones y tardó entre ${Math.min(...segundos).toFixed(0)} y ${Math.max(...segundos).toFixed(0)} segundos en promedio, según el recinto.`),
    figura('distribuciones_plaza.png', 'Figura 1. Distribuciones en la Plaza con escenario: una válida al azar, la mejor para evacuación, la mejor para accesibilidad y la del punto de rodilla. Azul: sanitarios. Rojo: atención médica. Naranja: comida. Negro grueso: puertas. Verde: salidas. Gris oscuro: escenario.', 0.9),
    titulo('8. Ejecución'),
    parrafo('Para repetir la verificación, las corridas y las figuras se usan estos comandos desde la raíz del repositorio:', { keepNext: true }),
    codigo(['pip install -r requirements.txt', 'python verificacion.py', 'python corridas.py --semillas 10 --poblacion 40 --generaciones 60', 'python analisis.py']),
    titulo('Referencias'),
    referencias([
      refDeb,
      'S. L. Hakimi, «Optimum distribution of switching centers in a communication network and some related graph theoretic problems», _Operations Research_, vol. 13, no. 3, pp. 462–475, 1965.',
      'J. A. Sethian, «A fast marching level set method for monotonically advancing fronts», _Proceedings of the National Academy of Sciences_, vol. 93, no. 4, pp. 1591–1595, 1996.',
      'R. L. Hughes, «A continuum theory for the flow of pedestrians», _Transportation Research Part B: Methodological_, vol. 36, no. 6, pp. 507–535, 2002.',
      'U. Weidmann, _Transporttechnik der Fussgänger_, 2.ª ed., Schriftenreihe des IVT, no. 90. Zúrich: IVT, ETH Zürich, 1993.',
      'C. F. Daganzo, «The cell transmission model: A dynamic representation of highway traffic consistent with the hydrodynamic theory», _Transportation Research Part B: Methodological_, vol. 28, no. 4, pp. 269–287, 1994.',
      refSfpe,
      refNom,
      'T. A. Feo y M. G. C. Resende, «Greedy randomized adaptive search procedures», _Journal of Global Optimization_, vol. 6, no. 2, pp. 109–133, 1995.',
      'S. Salcedo-Sanz, «A survey of repair methods used as constraint handling techniques in evolutionary algorithms», _Computer Science Review_, vol. 3, no. 3, pp. 175–192, 2009.',
      'G. Syswerda, «Uniform crossover in genetic algorithms», en _Proc. 3rd International Conference on Genetic Algorithms_, San Mateo, CA: Morgan Kaufmann, 1989, pp. 2–9.',
      refDas,
      refBranke
    ])
  ]);
}

//Reporte de las primeras corridas
function reporteCorridas() {
  const descripciones = {
    explanada: ['Abierto', 'Sin muros interiores', '2 (de 4 m y 2 m)'],
    plaza: ['Abierto', 'Escenario de 8 × 3 m cerrado con muros', '3 (de 3 m, 3 m y 2 m)'],
    salon: ['Cerrado', 'Muro divisorio de 13 m con un paso de 7 m', '3 (de 2 m, 2 m y 3 m)']
  };
  const filasRecintos = claves.map(c => [nombres[c], ...descripciones[c], `${verificacion[c].areaRecinto} m²`, verificacion[c].aforoMaximo]);
  const filasSemillas = claves.flatMap(c => resumen[c].semillas.map(f => [cortos[c], f.semilla, f.puntos, numero(f.mejorF1), numero(f.mejorF2, 1),
    `${numero(f.rodillaF1)} m, ${numero(f.rodillaF2, 1)} s`]));
  const filasVariacion = claves.map(c => {
    const v = resumen[c].variacion;
    return [nombres[c], ...[['mejorF1', 2, 'm'], ['mejorF2', 1, 's'], ['rodillaF1', 2, 'm'], ['rodillaF2', 1, 's']].map(([k, d, u]) =>
      `${numero(v[k].minimo, d)} a ${numero(v[k].maximo, d)} ${u} (${v[k].diferencia.toFixed(1)} %)`)];
  });
  const filasRep = claves.map(c => [nombres[c], `${Math.max(0, resumen[c].brechaF1[4]).toFixed(2)} %`, `${Math.max(0, resumen[c].brechaF2[4]).toFixed(2)} %`, resumen[c].repeticionesNecesarias]);
  const titulos = ['Al azar', 'Mejor para evacuación', 'Mejor para accesibilidad', 'Punto de rodilla'];
  const filasComp = claves.map(c => [nombres[c], ...titulos.map(t => `${numero(resumen[c].comparacion[t].F1)} m, ${numero(resumen[c].comparacion[t].F2, 1)} s`)]);
  const totalEval = claves.reduce((s, c) => s + resumen[c].semillas.reduce((a, f) => a + f.evaluaciones, 0), 0);
  const totalSeg = claves.reduce((s, c) => s + resumen[c].semillas.reduce((a, f) => a + f.segundos, 0), 0);
  const comp = c => resumen[c].comparacion;
  const mejoraF1 = c => (100 * (comp(c)['Al azar'].F1 - comp(c)['Punto de rodilla'].F1) / comp(c)['Al azar'].F1).toFixed(0);
  const mejoraF2 = c => (100 * (comp(c)['Al azar'].F2 - comp(c)['Punto de rodilla'].F2) / comp(c)['Al azar'].F2).toFixed(0);
  const rangoF1 = c => (100 * (comp(c)['Mejor para evacuación'].F1 - comp(c)['Mejor para accesibilidad'].F1) / comp(c)['Mejor para accesibilidad'].F1).toFixed(1);
  const rangoF2 = c => (100 * (comp(c)['Mejor para accesibilidad'].F2 - comp(c)['Mejor para evacuación'].F2) / comp(c)['Mejor para evacuación'].F2).toFixed(1);
  const maxDifF1 = Math.max(...claves.map(c => resumen[c].variacion.mejorF1.diferencia));
  const maxDifF2 = Math.max(...claves.map(c => resumen[c].variacion.mejorF2.diferencia));
  const maxRodillaF2 = Math.max(...claves.map(c => resumen[c].variacion.rodillaF2.diferencia));
  const maxRangoF1 = Math.max(...claves.map(c => Number(rangoF1(c))));
  //Tiempo que tardan todos en cruzar las salidas a su capacidad
  const limiteSalidas = c => {
    const esc = JSON.parse(fs.readFileSync(path.join(raiz, 'escenarios', `${c}.json`), 'utf8'));
    return esc.aforo / esc.salidas.reduce((s, x) => s + 1.32 * (x.largo - 0.3), 0);
  };
  const mejoresF2 = claves.map(c => `${numero(resumen[c].variacion.mejorF2.minimo, 1)} s`);
  const ordenRep = [...claves].sort((a, b) => resumen[a].repeticionesNecesarias - resumen[b].repeticionesNecesarias)
    .map(c => `${resumen[c].repeticionesNecesarias} en la ${cortos[c]}`.replace('la Salón', 'el Salón'));
  const repeticiones = Math.max(...claves.map(c => resumen[c].repeticionesNecesarias));
  return documento([
    encabezado('Reporte de las primeras corridas',
      'Implementación del motor de optimización: primeras corridas con repeticiones independientes y análisis de la variabilidad entre semillas',
      'Echeverría Pérez Luis David'),
    titulo('1. Objetivo'),
    parrafo('Correr el motor de optimización varias veces sobre los mismos recintos, cambiando solo la semilla del generador de números aleatorios, para ver cuánto cambia el resultado de una corrida a otra y cuántas repeticiones hacen falta para confiar en él.'),
    titulo('2. Recintos de prueba'),
    parrafo('Se usaron tres recintos de 30 × 20 m con los mismos 15 módulos: cinco baterías sanitarias de 3 × 2 m con dos puertas, dos carpas médicas de 3 × 3 m con una puerta y ocho puestos de comida de 2 × 2 m con dos puertas. En total ocupan 80 m². El aforo es de 800 personas en los tres casos, por debajo del máximo que permite el factor de 0.55 m² por persona de pie [1].'),
    tituloTabla('Tabla 1. Recintos de prueba'),
    tabla(['Recinto', 'Tipo', 'Interior', 'Salidas', 'Área', 'Aforo máximo'], filasRecintos, [3, 2, 4, 3, 2, 2], [4, 5]),
    figura('recintos.png', 'Figura 1. Recintos de prueba. Negro: muros. Verde: salidas. Gris oscuro: zona inaccesible.'),
    titulo('3. Cómo se hicieron las corridas'),
    parrafo(`En cada recinto se hicieron 10 corridas de NSGA-II [2] con las semillas 1 a 10, una población de 40 y 60 generaciones. Fueron 30 corridas, ${numero(totalEval, 0)} evaluaciones y ${numero(totalSeg / 60, 1)} minutos de cómputo, repartidas en dos procesos en paralelo.`),
    parrafo('Cada distribución se califica con dos números que se quieren lo más bajos posible. F1 es la distancia promedio que camina una persona hasta el módulo más cercano de cada tipo de servicio. F2 es el tiempo, en segundos, en que el recinto queda vacío según la simulación de la evacuación. De cada corrida se guardó su frente, es decir, las distribuciones en las que ya no se puede mejorar un objetivo sin empeorar el otro, y la de su punto de rodilla, que es la que tiene el mejor equilibrio entre los dos [3], [4].'),
    titulo('4. Frentes de cada repetición'),
    figura('frentes.png', 'Figura 2. Frente de cada semilla. La estrella marca el punto de rodilla.'),
    tituloTabla('Tabla 2. Resultados de cada semilla'),
    tabla(['Recinto', 'Semilla', 'Distribuciones en el frente', 'Mejor F1 (m)', 'Mejor F2 (s)', 'Punto de rodilla'], filasSemillas, [2, 1.3, 2.2, 1.8, 1.8, 2.6], [1, 2, 3, 4, 5], 18),
    titulo('5. Variabilidad entre semillas'),
    parrafo(`La Tabla 3 compara la mejor y la peor semilla en cada valor. La distancia promedio más baja cambió como mucho ${maxDifF1.toFixed(1)} % entre la mejor y la peor corrida.`),
    parrafo(maxDifF2 === 0
      ? `El tiempo de evacuación más bajo fue el mismo en las 10 semillas de cada recinto: ${mejoresF2[0]} en la Explanada, ${mejoresF2[1]} en la Plaza y ${mejoresF2[2]} en el Salón. Esos valores son prácticamente lo que tardan 800 personas en cruzar las salidas a 1.32 personas por segundo por cada metro de ancho efectivo [5], que da ${numero(limiteSalidas('explanada'), 1)} s, ${numero(limiteSalidas('plaza'), 1)} s y ${numero(limiteSalidas('salon'), 1)} s. Es decir, las salidas ponen un límite y todas las corridas lo alcanzan. El tiempo de evacuación del punto de rodilla sí cambia un poco entre semillas, hasta ${maxRodillaF2.toFixed(1)} %, porque depende de qué distribuciones quedaron en el frente de cada corrida.`
      : `El tiempo de evacuación más bajo cambió como mucho ${maxDifF2.toFixed(1)} %.`),
    tituloTabla('Tabla 3. Rango de valores entre las 10 semillas (diferencia entre la peor y la mejor)'),
    tabla(['Recinto', 'Mejor F1', 'Mejor F2', 'F1 de la rodilla', 'F2 de la rodilla'], filasVariacion, [2.4, 2.4, 2.4, 2.4, 2.4], [1, 2, 3, 4], 18),
    titulo('6. Cuántas repeticiones hacen falta'),
    parrafo('Para saber cuántas corridas bastan, se tomó el mejor F1 y el mejor F2 de las 10 semillas como referencia y se calculó qué tan lejos queda, en promedio, lo mejor que se obtiene con menos corridas. Por ejemplo, con 3 corridas se toman 3 semillas al azar, se guarda el mejor valor de esas tres y se repite el sorteo 2,000 veces. La Figura 3 muestra el resultado.'),
    figura('repeticiones.png', 'Figura 3. Diferencia promedio entre lo mejor de n corridas y lo mejor de las 10. La línea punteada marca 0.5 %.'),
    tituloTabla('Tabla 4. Diferencia con 5 corridas y repeticiones necesarias'),
    tabla(['Recinto', 'F1 con 5 corridas', 'F2 con 5 corridas', 'Corridas para quedar a menos de 0.5 %'], filasRep, [3, 2, 2, 3], [1, 2, 3]),
    parrafo(`En F2 la diferencia es cero desde la primera corrida, porque todas las semillas llegan al mismo tiempo mínimo. En F1 sí hace falta repetir. Para quedar a menos de 0.5 % bastan ${ordenRep[0]}, ${ordenRep[1]} y ${ordenRep[2]}. Por eso se fijan 10 repeticiones por recinto. Como la referencia es lo mejor de estas mismas 10 corridas, este número sirve como guía y no como garantía.`),
    titulo('7. Distribución al azar contra distribuciones optimizadas'),
    parrafo('Para ver qué gana el algoritmo, en cada recinto se compararon cuatro distribuciones: una válida generada al azar, como las de la población inicial, la mejor para evacuación, la mejor para accesibilidad y la del punto de rodilla. Las tres últimas salen de juntar los frentes de las 10 semillas.'),
    tituloTabla('Tabla 5. F1 y F2 de cada distribución'),
    tabla(['Recinto', 'Al azar', 'Mejor para evacuación', 'Mejor para accesibilidad', 'Punto de rodilla'], filasComp, [2.4, 2.4, 2.4, 2.4, 2.4], [1, 2, 3, 4], 18),
    parrafo(`Frente a la distribución al azar, la del punto de rodilla redujo la distancia promedio ${mejoraF1('explanada')} %, ${mejoraF1('plaza')} % y ${mejoraF1('salon')} %, y el tiempo de evacuación ${mejoraF2('explanada')} %, ${mejoraF2('plaza')} % y ${mejoraF2('salon')} %, en la Explanada, la Plaza y el Salón. Entre la mejor para evacuación y la mejor para accesibilidad, la distancia promedio cambia ${rangoF1('explanada')} %, ${rangoF1('plaza')} % y ${rangoF1('salon')} %, y el tiempo de evacuación ${rangoF2('explanada')} %, ${rangoF2('plaza')} % y ${rangoF2('salon')} %. En distancia, lo que se gana frente al azar es mucho mayor que la diferencia entre los extremos del frente, que no pasa de ${maxRangoF1.toFixed(1)} %. En tiempo de evacuación las cifras se parecen más. En la Plaza, la mejor distribución para accesibilidad tarda ${numero(comp('plaza')['Mejor para accesibilidad'].F2, 1)} s en evacuarse, la mejor para evacuación ${numero(comp('plaza')['Mejor para evacuación'].F2, 1)} s y la distribución al azar ${numero(comp('plaza')['Al azar'].F2, 1)} s. Ahí se ve que los dos objetivos compiten: acercar los servicios a la gente puede costar buena parte de lo que se ganó en evacuación.`),
    figura('distribuciones_explanada.png', 'Figura 4. Explanada abierta. Azul: sanitarios. Rojo: atención médica. Naranja: comida. Negro grueso: puertas. Verde: salidas.', 0.9),
    figura('distribuciones_plaza.png', 'Figura 5. Plaza con escenario. Gris oscuro: escenario.', 0.9),
    figura('distribuciones_salon.png', 'Figura 6. Salón con muro divisorio.', 0.9),
    parrafo('La Figura 7 compara la evacuación de la distribución al azar y la del punto de rodilla en la Plaza con escenario.'),
    figura('evacuacion_plaza.png', 'Figura 7. Densidad de personas durante la evacuación de la Plaza con escenario. Arriba: distribución al azar. Abajo: punto de rodilla.'),
    titulo('8. Conclusiones'),
    parrafo(`El motor terminó las 30 corridas y en todas entregó distribuciones válidas. El tiempo de evacuación más bajo fue el mismo en todas las semillas y coincide con el límite que ponen las salidas. La distancia promedio sí cambia de una semilla a otra, hasta ${maxDifF1.toFixed(1)} %, y con ${repeticiones} corridas lo mejor que se obtiene queda a menos de 0.5 % de lo mejor de las 10. Comparado con una distribución al azar, el algoritmo mejora los dos objetivos a la vez, y el frente muestra cuánto hay que ceder en uno para mejorar el otro.`),
    titulo('Referencias'),
    referencias([refNom, refDeb, refDas, refBranke, refSfpe])
  ]);
}

(async () => {
  const salida = path.join(raiz, 'evidencias');
  fs.writeFileSync(path.join(salida, 'Periodo3-1-Implementacion-del-algoritmo.docx'), await Packer.toBuffer(reporteImplementacion()));
  fs.writeFileSync(path.join(salida, 'Periodo3-2-Primeras-corridas.docx'), await Packer.toBuffer(reporteCorridas()));
  console.log('listo');
})();
