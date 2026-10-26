# TT 2027-A126

Prototipo de sistema para la distribución óptima de áreas de servicio en eventos masivos mediante algoritmos bioinspirados.

Escuela Superior de Cómputo, IPN. Echeverría Pérez Luis David y Martínez Meneses Monserrat Alejandra. Directores: Dr. Daniel Molina Pérez y Dr. Jacobo Torres Figueroa.

Este repositorio contiene el motor de optimización que se usa en TT1 para validar el modelo del capítulo 5 del reporte técnico y dimensionar las corridas. No incluye la interfaz web ni la API, que se desarrollan en TT2.

## Contenido

| Ruta | Qué contiene |
|---|---|
| `motor/parametros.py` | Parámetros del modelo (Weidmann, SFPE, NOM-011) y del algoritmo |
| `motor/recinto.py` | Malla de 1 m, muros y salidas en las aristas, clasificación de celdas |
| `motor/modulos.py` | Módulos, giros, puertas y posiciones válidas |
| `motor/eikonal.py` | Fast Marching Method con muros en las aristas |
| `motor/evacuacion.py` | Simulación de la evacuación (Hughes, Weidmann y transmisión de celdas) |
| `motor/evaluador.py` | Violación total G, accesibilidad F1 y tiempo de evacuación F2 |
| `motor/nsga2.py` | NSGA-II con dominancia restringida, reparación y punto de rodilla |
| `escenarios/` | Recintos de prueba de 30 x 20 m |
| `editor/index.html` | Editor de recinto: muros, salidas y exportación al formato del motor |
| `verificacion.py` | Validez de la población inicial y costo por evaluación |
| `corridas.py` | Corridas independientes con distintas semillas |
| `analisis.py` | Hipervolumen, variabilidad entre semillas y figuras |
| `simular.py` | Animación de la evacuación con el mapa de densidad |
| `resultados/` | Frentes de cada corrida, resumen y figuras |
| `evidencias/` | Reportes en PDF de cada periodo del cronograma |

## Uso

```
pip install -r requirements.txt
python verificacion.py
python corridas.py --semillas 10 --poblacion 40 --generaciones 50
python analisis.py
python simular.py plaza --semilla 1
```

El editor se abre directamente en el navegador (`editor/index.html`) y descarga recintos en el mismo formato que `escenarios/`.
