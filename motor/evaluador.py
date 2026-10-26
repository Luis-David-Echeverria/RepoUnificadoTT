from collections import deque

import numpy as np

from . import parametros as P
from .eikonal import resolverEikonal
from .evacuacion import simularEvacuacion
from .modulos import paredEnPuerta


class Evaluador:
    def __init__(self, recinto, catalogo):
        self.recinto = recinto
        self.catalogo = catalogo
        r = recinto
        self.abiertos = tuple(np.ascontiguousarray(m) for m in (r.abiertoE, r.abiertoO, r.abiertoN, r.abiertoS))
        ys, xs, ids, caps = [], [], [], []
        for e, salida in enumerate(r.salidas):
            for (y, x) in salida['celdas']:
                ys.append(y)
                xs.append(x)
                ids.append(e)
            caps.append(salida['capacidadPaso'])
        self.salidaY = np.array(ys, dtype=np.int64)
        self.salidaX = np.array(xs, dtype=np.int64)
        self.salidaId = np.array(ids, dtype=np.int64)
        self.capacidades = np.array(caps, dtype=np.float64)
        self.celdasSalida = list(zip(ys, xs))
        self.plazaVacia = self.alcancePlaza(r.omega0)
        self.evaluaciones = 0

    #Celdas de cada modulo, puertas y conteo de ocupacion
    def desplegar(self, L):
        r = self.recinto
        a, b = r.ancho, r.largo
        conteo = np.zeros((b, a), dtype=np.int32)
        g1 = g3 = 0
        puertas = []
        for j, (x, y, o) in enumerate(L):
            m = self.catalogo.modulos[j]
            orient = m.orientaciones[o]
            w, l = orient['ancho'], orient['largo']
            y0, y1, x0, x1 = max(y, 0), min(y + l, b), max(x, 0), min(x + w, a)
            dentro = max(y1 - y0, 0) * max(x1 - x0, 0)
            g1 += w * l - dentro
            if dentro > 0:
                g1 += int((~r.omega0[y0:y1, x0:x1]).sum())
                g1 += int(r.muroV[y0:y1, max(x + 1, 0):max(min(x + w, a), 0)].sum())
                g1 += int(r.muroH[max(y + 1, 0):max(min(y + l, b), 0), x0:x1].sum())
                conteo[y0:y1, x0:x1] += 1
                g3 += int(r.franjaSalidas[y0:y1, x0:x1].sum())
            for cy, cx, lado, ay, ax in orient['puertas']:
                puertas.append((j, y + cy, x + cx, lado, y + ay, x + ax))
        return conteo, puertas, g1, g3

    #Posiciones de un cuadro de 2 x 2 m que pueden llegar a una salida
    def alcancePlaza(self, libre):
        r = self.recinto
        valida = (libre[:-1, :-1] & libre[1:, :-1] & libre[:-1, 1:] & libre[1:, 1:]
                  & ~r.muroV[:-1, 1:-1] & ~r.muroV[1:, 1:-1] & ~r.muroH[1:-1, :-1] & ~r.muroH[1:-1, 1:])
        alcance = np.zeros_like(valida)
        cola = deque()
        for (cy, cx) in self.celdasSalida:
            for py in (cy - 1, cy):
                for px in (cx - 1, cx):
                    if 0 <= py < valida.shape[0] and 0 <= px < valida.shape[1] and valida[py, px] and not alcance[py, px]:
                        alcance[py, px] = True
                        cola.append((py, px))
        while cola:
            y, x = cola.popleft()
            for ny, nx in ((y, x + 1), (y, x - 1), (y + 1, x), (y - 1, x)):
                if 0 <= ny < valida.shape[0] and 0 <= nx < valida.shape[1] and valida[ny, nx] and not alcance[ny, nx]:
                    alcance[ny, nx] = True
                    cola.append((ny, nx))
        return alcance

    def puertaConectada(self, alcance, ay, ax):
        for py in (ay - 1, ay):
            for px in (ax - 1, ax):
                if 0 <= py < alcance.shape[0] and 0 <= px < alcance.shape[1] and alcance[py, px]:
                    return True
        return False

    #Contar violaciones de las seis restricciones
    def violaciones(self, L):
        r = self.recinto
        a, b = r.ancho, r.largo
        conteo, puertas, g1, g3 = self.desplegar(L)
        g2 = int((conteo >= 2).sum())
        ocupado = conteo > 0
        libre = r.omega0 & ~ocupado
        g4 = 0
        accesosValidos = []
        for j, py, px, lado, ay, ax in puertas:
            puertaDentro = 0 <= py < b and 0 <= px < a
            accesoDentro = 0 <= ay < b and 0 <= ax < a
            if not (puertaDentro and accesoDentro) or not libre[ay, ax] or paredEnPuerta(r, py, px, lado):
                g4 += 1
            else:
                accesosValidos.append((j, ay, ax))
        g5 = 0
        if r.abierto:
            alcance = self.alcancePlaza(libre)
            for j, ay, ax in accesosValidos:
                if not self.puertaConectada(alcance, ay, ax) and self.puertaConectada(self.plazaVacia, ay, ax):
                    g5 += 1
        alcanzadas = r.alcanzables(self.celdasSalida, libre)
        g6 = int((libre & ~alcanzadas).sum())
        return [int(g) for g in (g1, g2, g3, g4, g5, g6)], libre, accesosValidos

    #Distancia promedio al modulo mas cercano de cada tipo
    def accesibilidad(self, libre, accesosValidos):
        unos = np.ones(libre.shape)
        distancias = {}
        for tipo in self.catalogo.tipos:
            semillas = [(ay, ax) for j, ay, ax in accesosValidos if self.catalogo.modulos[j].tipo == tipo]
            semillasY = np.array([s[0] for s in semillas], dtype=np.int64)
            semillasX = np.array([s[1] for s in semillas], dtype=np.int64)
            campo = resolverEikonal(libre, *self.abiertos, unos, semillasY, semillasX)
            distancias[tipo] = float(campo[libre].mean())
        return float(np.mean(list(distancias.values()))), distancias

    def tiempoEvacuacion(self, libre, guardarCada=0):
        return simularEvacuacion(libre, *self.abiertos, self.salidaY, self.salidaX, self.salidaId, self.capacidades,
                                 float(self.recinto.aforo), P.velocidadLibre, P.gammaWeidmann, P.densidadMaxima,
                                 P.densidadCritica, P.flujoMaximo, P.pasoTiempo, P.pasosRecalculo,
                                 P.velocidadMinima, P.tiempoMaximo, guardarCada)

    #Evaluar distribucion
    def evaluar(self, L):
        self.evaluaciones += 1
        g, libre, accesos = self.violaciones(L)
        resultado = {'G': int(sum(g)), 'violaciones': g, 'F1': np.inf, 'F2': np.inf, 'distancias': {}}
        if resultado['G'] == 0:
            resultado['F1'], resultado['distancias'] = self.accesibilidad(libre, accesos)
            resultado['F2'] = float(self.tiempoEvacuacion(libre)[0])
        return resultado
