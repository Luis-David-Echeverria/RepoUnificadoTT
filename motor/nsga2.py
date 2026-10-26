import time

import numpy as np

from . import parametros as P


def domina(a, b):
    if a['G'] == 0 and b['G'] > 0:
        return True
    if a['G'] > 0:
        return b['G'] > 0 and a['G'] < b['G']
    return a['F1'] <= b['F1'] and a['F2'] <= b['F2'] and (a['F1'] < b['F1'] or a['F2'] < b['F2'])


#Ordenamiento por no dominancia con dominancia restringida
def ordenarNoDominados(evaluaciones):
    n = len(evaluaciones)
    dominados = [[] for _ in range(n)]
    contador = np.zeros(n, dtype=int)
    frentes = [[]]
    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if domina(evaluaciones[p], evaluaciones[q]):
                dominados[p].append(q)
            elif domina(evaluaciones[q], evaluaciones[p]):
                contador[p] += 1
        if contador[p] == 0:
            frentes[0].append(p)
    k = 0
    while frentes[k]:
        siguiente = []
        for p in frentes[k]:
            for q in dominados[p]:
                contador[q] -= 1
                if contador[q] == 0:
                    siguiente.append(q)
        k += 1
        frentes.append(siguiente)
    return frentes[:-1]


def distanciaAglomeracion(frente, evaluaciones):
    distancia = {i: 0.0 for i in frente}
    if not frente or evaluaciones[frente[0]]['G'] > 0:
        return distancia
    for objetivo in ('F1', 'F2'):
        orden = sorted(frente, key=lambda i: evaluaciones[i][objetivo])
        minimo, maximo = evaluaciones[orden[0]][objetivo], evaluaciones[orden[-1]][objetivo]
        distancia[orden[0]] = distancia[orden[-1]] = np.inf
        if maximo - minimo <= 0:
            continue
        for k in range(1, len(orden) - 1):
            distancia[orden[k]] += (evaluaciones[orden[k + 1]][objetivo] - evaluaciones[orden[k - 1]][objetivo]) / (maximo - minimo)
    return distancia


def puntoRodilla(frente):
    f1 = np.array([e['F1'] for e in frente])
    f2 = np.array([e['F2'] for e in frente])
    rango1 = f1.max() - f1.min() or 1.0
    rango2 = f2.max() - f2.min() or 1.0
    suma = (f1 - f1.min()) / rango1 + (f2 - f2.min()) / rango2
    return int(np.argmin(suma))


class Nsga2:
    def __init__(self, evaluador, poblacion=40, generaciones=40, semilla=0):
        self.evaluador = evaluador
        self.catalogo = evaluador.catalogo
        self.recinto = evaluador.recinto
        self.poblacion = poblacion
        self.generaciones = generaciones
        self.rng = np.random.default_rng(semilla)
        self.K = self.catalogo.cantidad
        self.probabilidadMutacion = 1.0 / self.K
        self.memoria = {}

    def evaluar(self, L):
        clave = L.tobytes()
        if clave not in self.memoria:
            self.memoria[clave] = self.evaluador.evaluar(L)
        return self.memoria[clave]

    def candidatos(self, j, ocupacion, reservadas):
        xs, ys, os = [], [], []
        for o in range(4):
            py, px = self.catalogo.posicionesValidas(j, o, ocupacion, reservadas)
            xs.append(px)
            ys.append(py)
            os.append(np.full(len(px), o))
        return np.concatenate(xs), np.concatenate(ys), np.concatenate(os)

    #Construir una distribucion valida modulo por modulo
    def construirIndividuo(self):
        areas = np.array([m.area for m in self.catalogo.modulos])
        orden = sorted(range(self.K), key=lambda j: (-areas[j], self.rng.random()))
        b, a = self.recinto.largo, self.recinto.ancho
        for _ in range(50):
            ocupacion = np.zeros((b, a), dtype=bool)
            reservadas = np.zeros((b, a), dtype=bool)
            L = np.zeros((self.K, 3), dtype=np.int64)
            completo = True
            for j in orden:
                xs, ys, os = self.candidatos(j, ocupacion, reservadas)
                if len(xs) == 0:
                    completo = False
                    break
                k = self.rng.integers(len(xs))
                L[j] = (xs[k], ys[k], os[k])
                self.catalogo.colocar(j, L[j], ocupacion, reservadas)
            if completo:
                return L
        raise RuntimeError('Los modulos no caben en el recinto')

    #Reparar en el orden del cromosoma buscando la posicion valida mas cercana
    def reparar(self, L):
        b, a = self.recinto.largo, self.recinto.ancho
        ocupacion = np.zeros((b, a), dtype=bool)
        reservadas = np.zeros((b, a), dtype=bool)
        for j in range(self.K):
            x, y, o = L[j]
            xs, ys, os = self.candidatos(j, ocupacion, reservadas)
            if len(xs) > 0:
                heredada = (xs == x) & (ys == y) & (os == o)
                if not heredada.any():
                    distancia = (xs - x) ** 2 + (ys - y) ** 2 + 0.5 * (os != o) + 1e-3 * self.rng.random(len(xs))
                    k = int(np.argmin(distancia))
                    L[j] = (xs[k], ys[k], os[k])
            self.catalogo.colocar(j, L[j], ocupacion, reservadas)
        return L

    def torneoBinario(self, rango, aglomeracion):
        i, k = self.rng.integers(len(rango), size=2)
        if rango[i] != rango[k]:
            return i if rango[i] < rango[k] else k
        return i if aglomeracion[i] >= aglomeracion[k] else k

    def cruzaUniforme(self, padre, madre):
        hijo1, hijo2 = padre.copy(), madre.copy()
        if self.rng.random() < P.probabilidadCruza:
            intercambio = self.rng.random(self.K) < 0.5
            hijo1[intercambio], hijo2[intercambio] = madre[intercambio], padre[intercambio]
        return hijo1, hijo2

    #Mover, girar o reubicar modulos
    def mutar(self, L):
        a, b = self.recinto.ancho, self.recinto.largo
        r = P.desplazamientoMaximo
        for j in range(self.K):
            if self.rng.random() >= self.probabilidadMutacion:
                continue
            x, y, o = L[j]
            tipo = self.rng.integers(3)
            if tipo == 0:
                dx, dy = 0, 0
                while dx == 0 and dy == 0:
                    dx, dy = self.rng.integers(-r, r + 1, size=2)
                x, y = x + dx, y + dy
            elif tipo == 1:
                o = (o + self.rng.integers(1, 4)) % 4
            else:
                o = self.rng.integers(4)
                x, y = self.rng.integers(a), self.rng.integers(b)
            orient = self.catalogo.modulos[j].orientaciones[o]
            L[j] = (np.clip(x, 0, a - orient['ancho']), np.clip(y, 0, b - orient['largo']), o)
        return L

    def ordenar(self, evaluaciones):
        frentes = ordenarNoDominados(evaluaciones)
        rango = np.zeros(len(evaluaciones), dtype=int)
        aglomeracion = np.zeros(len(evaluaciones))
        for k, frente in enumerate(frentes):
            distancia = distanciaAglomeracion(frente, evaluaciones)
            for i in frente:
                rango[i] = k
                aglomeracion[i] = distancia[i]
        return frentes, rango, aglomeracion

    def frenteFactible(self, individuos, evaluaciones):
        factibles = [i for i in range(len(individuos)) if evaluaciones[i]['G'] == 0]
        if not factibles:
            return []
        frente = ordenarNoDominados([evaluaciones[i] for i in factibles])[0]
        vistos, resultado = set(), []
        for k in frente:
            i = factibles[k]
            clave = (round(evaluaciones[i]['F1'], 6), round(evaluaciones[i]['F2'], 6))
            if clave not in vistos:
                vistos.add(clave)
                resultado.append((individuos[i], evaluaciones[i]))
        return sorted(resultado, key=lambda par: par[1]['F1'])

    def ejecutar(self):
        inicio = time.time()
        individuos = [self.construirIndividuo() for _ in range(self.poblacion)]
        evaluaciones = [self.evaluar(L) for L in individuos]
        historia = []
        for generacion in range(self.generaciones):
            frentes, rango, aglomeracion = self.ordenar(evaluaciones)
            hijos = []
            while len(hijos) < self.poblacion:
                padre = individuos[self.torneoBinario(rango, aglomeracion)]
                madre = individuos[self.torneoBinario(rango, aglomeracion)]
                for hijo in self.cruzaUniforme(padre, madre):
                    hijos.append(self.reparar(self.mutar(hijo)))
            hijos = hijos[:self.poblacion]
            evaluacionesHijos = [self.evaluar(L) for L in hijos]
            #Reemplazo elitista
            todos = individuos + hijos
            todasEvaluaciones = evaluaciones + evaluacionesHijos
            frentes, rango, aglomeracion = self.ordenar(todasEvaluaciones)
            elegidos = []
            for frente in frentes:
                if len(elegidos) + len(frente) <= self.poblacion:
                    elegidos += frente
                else:
                    resto = sorted(frente, key=lambda i: -aglomeracion[i])
                    elegidos += resto[:self.poblacion - len(elegidos)]
                    break
            individuos = [todos[i] for i in elegidos]
            evaluaciones = [todasEvaluaciones[i] for i in elegidos]
            frente = self.frenteFactible(individuos, evaluaciones)
            historia.append({'generacion': generacion + 1,
                             'factibles': int(sum(e['G'] == 0 for e in evaluaciones)),
                             'frente': [[e['F1'], e['F2']] for _, e in frente]})
        frente = self.frenteFactible(individuos, evaluaciones)
        rodilla = puntoRodilla([e for _, e in frente]) if frente else None
        return {'frente': frente, 'rodilla': rodilla, 'historia': historia,
                'evaluaciones': self.evaluador.evaluaciones, 'segundos': time.time() - inicio}
