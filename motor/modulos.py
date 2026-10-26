import numpy as np

#Desplazamiento (dy, dx) hacia afuera de cada lado
direcciones = {'E': (0, 1), 'N': (1, 0), 'O': (0, -1), 'S': (-1, 0)}
#Giro de 90 grados en sentido antihorario
giroLado = {'E': 'N', 'N': 'O', 'O': 'S', 'S': 'E'}


def paredEnPuerta(recinto, y, x, lado):
    if lado == 'E':
        return recinto.muroV[y, x + 1]
    if lado == 'O':
        return recinto.muroV[y, x]
    if lado == 'N':
        return recinto.muroH[y + 1, x]
    return recinto.muroH[y, x]


class Modulo:
    def __init__(self, indice, clase):
        self.indice = indice
        self.tipo = clase['tipo']
        self.nombre = clase['nombre']
        self.ancho = int(clase['ancho'])
        self.largo = int(clase['largo'])
        self.puertas = [(int(u), int(v), lado) for u, v, lado in clase['puertas']]
        self.orientaciones = [self.rotar(o) for o in range(4)]
        self.area = self.ancho * self.largo

    #Girar el modulo y sus puertas
    def rotar(self, o):
        w, l = self.ancho, self.largo
        puertas = list(self.puertas)
        for _ in range(o):
            puertas = [(l - 1 - v, u, giroLado[lado]) for (u, v, lado) in puertas]
            w, l = l, w
        lista = []
        for u, v, lado in puertas:
            dy, dx = direcciones[lado]
            lista.append((v, u, lado, v + dy, u + dx))
        return {'ancho': w, 'largo': l, 'puertas': lista}


class Catalogo:
    def __init__(self, recinto, clases):
        self.recinto = recinto
        self.modulos = []
        for clase in clases:
            for _ in range(int(clase['cantidad'])):
                self.modulos.append(Modulo(len(self.modulos), clase))
        self.tipos = sorted({m.tipo for m in self.modulos})
        cache = {}
        self.estaticas = []
        for m in self.modulos:
            clave = (m.ancho, m.largo, tuple(m.puertas))
            if clave not in cache:
                cache[clave] = [self.mascaraEstatica(m.orientaciones[o]) for o in range(4)]
            self.estaticas.append(cache[clave])

    @property
    def cantidad(self):
        return len(self.modulos)

    @property
    def areaTotal(self):
        return sum(m.area for m in self.modulos)

    #Posiciones validas sin considerar otros modulos
    def mascaraEstatica(self, orient):
        r = self.recinto
        a, b = r.ancho, r.largo
        w, l = orient['ancho'], orient['largo']
        mascara = np.zeros((b, a), dtype=bool)
        prohibidas = ~r.omega0 | r.franjaSalidas
        for y in range(0, b - l + 1):
            for x in range(0, a - w + 1):
                if prohibidas[y:y + l, x:x + w].any():
                    continue
                if r.muroV[y:y + l, x + 1:x + w].any() or r.muroH[y + 1:y + l, x:x + w].any():
                    continue
                valida = True
                for cy, cx, lado, ay, ax in orient['puertas']:
                    yy, xx = y + ay, x + ax
                    if not (0 <= yy < b and 0 <= xx < a) or not r.omega0[yy, xx] or paredEnPuerta(r, y + cy, x + cx, lado):
                        valida = False
                        break
                mascara[y, x] = valida
        return mascara

    #Posiciones validas dado lo que ya esta colocado
    def posicionesValidas(self, j, o, ocupacion, reservadas):
        orient = self.modulos[j].orientaciones[o]
        w, l = orient['ancho'], orient['largo']
        ys, xs = np.nonzero(self.estaticas[j][o])
        if len(ys) == 0:
            return ys, xs
        bloqueo = (ocupacion | reservadas).astype(np.int32)
        integral = np.zeros((bloqueo.shape[0] + 1, bloqueo.shape[1] + 1), dtype=np.int32)
        integral[1:, 1:] = bloqueo.cumsum(0).cumsum(1)
        suma = integral[ys + l, xs + w] - integral[ys, xs + w] - integral[ys + l, xs] + integral[ys, xs]
        validas = suma == 0
        for cy, cx, lado, ay, ax in orient['puertas']:
            validas &= ~ocupacion[ys + ay, xs + ax]
        return ys[validas], xs[validas]

    def colocar(self, j, gen, ocupacion, reservadas):
        x, y, o = gen
        orient = self.modulos[j].orientaciones[o]
        a, b = self.recinto.ancho, self.recinto.largo
        ocupacion[max(y, 0):min(y + orient['largo'], b), max(x, 0):min(x + orient['ancho'], a)] = True
        for cy, cx, lado, ay, ax in orient['puertas']:
            if 0 <= y + ay < b and 0 <= x + ax < a:
                reservadas[y + ay, x + ax] = True
