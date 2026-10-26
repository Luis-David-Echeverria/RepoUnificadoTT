import json
from collections import deque

import numpy as np

from . import parametros as P


class Recinto:
    def __init__(self, datos):
        self.nombre = datos['nombre']
        self.ancho = int(datos['ancho'])
        self.largo = int(datos['largo'])
        self.abierto = bool(datos['abierto'])
        self.aforo = int(datos['aforo'])
        a, b = self.ancho, self.largo
        #Muros en las aristas: verticales (b, a+1) y horizontales (b+1, a)
        self.muroV = np.zeros((b, a + 1), dtype=bool)
        self.muroH = np.zeros((b + 1, a), dtype=bool)
        self.muroV[:, 0] = self.muroV[:, a] = True
        self.muroH[0, :] = self.muroH[b, :] = True
        for muro in datos.get('muros', []):
            self.colocarMuro(muro)
        self.salidas = []
        for salida in datos['salidas']:
            self.colocarMuro(salida)
            self.salidas.append(self.prepararSalida(salida))
        self.calcularAbiertos()
        self.clasificarCeldas()
        self.franjaSalidas = self.calcularFranjas()

    #Colocar muro
    def colocarMuro(self, muro):
        x, y, n = muro['x'], muro['y'], muro['largo']
        if muro['orientacion'] == 'V':
            self.muroV[y:y + n, x] = True
        else:
            self.muroH[y, x:x + n] = True

    def prepararSalida(self, salida):
        x, y, n = salida['x'], salida['y'], salida['largo']
        interior = salida['interior']
        if salida['orientacion'] == 'V':
            cx = x if interior == '+' else x - 1
            ox = x - 1 if interior == '+' else x
            celdas = [(yy, cx) for yy in range(y, y + n)]
            exteriores = [(yy, ox) for yy in range(y, y + n)]
        else:
            cy = y if interior == '+' else y - 1
            oy = y - 1 if interior == '+' else y
            celdas = [(cy, xx) for xx in range(x, x + n)]
            exteriores = [(oy, xx) for xx in range(x, x + n)]
        capacidad = P.flujoEspecifico * max(n - 2 * P.capaLimite, 0.0) * P.pasoTiempo
        return {'datos': salida, 'celdas': celdas, 'exteriores': exteriores, 'capacidadPaso': capacidad}

    def calcularAbiertos(self):
        a, b = self.ancho, self.largo
        self.abiertoE = ~self.muroV[:, 1:]
        self.abiertoO = ~self.muroV[:, :-1]
        self.abiertoN = ~self.muroH[1:, :]
        self.abiertoS = ~self.muroH[:-1, :]
        self.abiertoE[:, a - 1] = False
        self.abiertoO[:, 0] = False
        self.abiertoN[b - 1, :] = False
        self.abiertoS[0, :] = False

    def vecinos(self, y, x, libre):
        if self.abiertoE[y, x] and libre[y, x + 1]:
            yield y, x + 1
        if self.abiertoO[y, x] and libre[y, x - 1]:
            yield y, x - 1
        if self.abiertoN[y, x] and libre[y + 1, x]:
            yield y + 1, x
        if self.abiertoS[y, x] and libre[y - 1, x]:
            yield y - 1, x

    def alcanzables(self, origenes, libre):
        visto = np.zeros_like(libre)
        cola = deque()
        for y, x in origenes:
            if 0 <= y < self.largo and 0 <= x < self.ancho and libre[y, x] and not visto[y, x]:
                visto[y, x] = True
                cola.append((y, x))
        while cola:
            y, x = cola.popleft()
            for ny, nx in self.vecinos(y, x, libre):
                if not visto[ny, nx]:
                    visto[ny, nx] = True
                    cola.append((ny, nx))
        return visto

    #Clasificar celdas en recinto, exterior e inaccesible
    def clasificarCeldas(self):
        todo = np.ones((self.largo, self.ancho), dtype=bool)
        celdasInteriores = [c for s in self.salidas for c in s['celdas']]
        self.omega0 = self.alcanzables(celdasInteriores, todo)
        celdasExteriores = [c for s in self.salidas for c in s['exteriores']]
        self.exterior = self.alcanzables(celdasExteriores, todo) & ~self.omega0
        self.inaccesible = ~self.omega0 & ~self.exterior

    def calcularFranjas(self):
        franja = np.zeros((self.largo, self.ancho), dtype=bool)
        for s in self.salidas:
            d = s['datos']
            signo = 1 if d['interior'] == '+' else -1
            for k in range(P.profundidadSalida):
                for (cy, cx) in s['celdas']:
                    y, x = (cy, cx + signo * k) if d['orientacion'] == 'V' else (cy + signo * k, cx)
                    if 0 <= y < self.largo and 0 <= x < self.ancho:
                        franja[y, x] = True
        return franja & self.omega0

    def aforoMaximo(self, areaModulos):
        return int((self.omega0.sum() - areaModulos) / P.factorOcupacion)


def cargarEscenario(ruta):
    with open(ruta, encoding='utf-8') as archivo:
        datos = json.load(archivo)
    return Recinto(datos), datos['modulos']
