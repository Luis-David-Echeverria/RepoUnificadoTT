import numpy as np
from numba import njit

from .eikonal import resolverEikonal


@njit(cache=True)
def velocidadCelda(densidad, vLibre, gamma, densidadMax):
    if densidad <= 1e-9:
        return vLibre
    v = vLibre * (1.0 - np.exp(-gamma * (1.0 / densidad - 1.0 / densidadMax)))
    return max(0.0, min(vLibre, v))


#Simular evacuacion con Hughes, Weidmann y transmision de celdas
@njit(cache=True)
def simularEvacuacion(libre, abiertoE, abiertoO, abiertoN, abiertoS, salidaY, salidaX, salidaId, capacidades,
                      aforo, vLibre, gamma, densidadMax, densidadCrit, flujoMax, dt, pasosRecalculo, vMinima,
                      tMaximo, guardarCada):
    b, a = libre.shape
    numSalidas = capacidades.shape[0]
    numLibres = 0
    for y in range(b):
        for x in range(a):
            if libre[y, x]:
                numLibres += 1
    densidad = np.zeros((b, a))
    for y in range(b):
        for x in range(a):
            if libre[y, x]:
                densidad[y, x] = aforo / numLibres
    maxCuadros = 1
    if guardarCada > 0:
        maxCuadros = int(tMaximo / dt / guardarCada) + 2
    cuadros = np.zeros((maxCuadros, b, a))
    numCuadros = 0
    if guardarCada > 0:
        cuadros[0] = densidad
        numCuadros = 1
    velocidad = np.ones((b, a))
    potencial = np.full((b, a), np.inf)
    salidaFlujo = np.zeros((4, b, a))
    entrante = np.zeros((b, a))
    factor = np.ones((b, a))
    totalSalida = np.zeros(numSalidas)
    paso = 0
    t = 0.0
    while True:
        #Recalcular rutas con la densidad actual
        if paso % pasosRecalculo == 0:
            for y in range(b):
                for x in range(a):
                    if libre[y, x]:
                        velocidad[y, x] = max(velocidadCelda(densidad[y, x], vLibre, gamma, densidadMax), vMinima)
            potencial = resolverEikonal(libre, abiertoE, abiertoO, abiertoN, abiertoS, velocidad, salidaY, salidaX)
        salidaFlujo[:] = 0.0
        entrante[:] = 0.0
        #Demanda de cada celda repartida hacia vecinas con menor potencial
        for y in range(b):
            for x in range(a):
                if not libre[y, x] or densidad[y, x] <= 1e-12 or potencial[y, x] == np.inf:
                    continue
                rho = densidad[y, x]
                if rho <= densidadCrit:
                    demanda = rho * velocidadCelda(rho, vLibre, gamma, densidadMax)
                else:
                    demanda = flujoMax
                diferencias = np.zeros(4)
                suma = 0.0
                for d in range(4):
                    ny, nx = y, x
                    if d == 0:
                        if not abiertoE[y, x]:
                            continue
                        nx = x + 1
                    elif d == 1:
                        if not abiertoO[y, x]:
                            continue
                        nx = x - 1
                    elif d == 2:
                        if not abiertoN[y, x]:
                            continue
                        ny = y + 1
                    else:
                        if not abiertoS[y, x]:
                            continue
                        ny = y - 1
                    if libre[ny, nx] and potencial[ny, nx] < potencial[y, x]:
                        diferencias[d] = potencial[y, x] - potencial[ny, nx]
                        suma += diferencias[d]
                if suma <= 0.0:
                    continue
                for d in range(4):
                    if diferencias[d] > 0.0:
                        q = diferencias[d] / suma * demanda * dt
                        salidaFlujo[d, y, x] = q
                        ny, nx = y, x
                        if d == 0:
                            nx = x + 1
                        elif d == 1:
                            nx = x - 1
                        elif d == 2:
                            ny = y + 1
                        else:
                            ny = y - 1
                        entrante[ny, nx] += q
        #Oferta: lo que cada celda puede recibir
        for y in range(b):
            for x in range(a):
                factor[y, x] = 1.0
                if entrante[y, x] > 0.0:
                    rho = densidad[y, x]
                    if rho <= densidadCrit:
                        oferta = flujoMax
                    else:
                        oferta = rho * velocidadCelda(rho, vLibre, gamma, densidadMax)
                    factor[y, x] = min(1.0, oferta * dt / entrante[y, x])
        nueva = densidad.copy()
        for y in range(b):
            for x in range(a):
                for d in range(4):
                    q = salidaFlujo[d, y, x]
                    if q <= 0.0:
                        continue
                    ny, nx = y, x
                    if d == 0:
                        nx = x + 1
                    elif d == 1:
                        nx = x - 1
                    elif d == 2:
                        ny = y + 1
                    else:
                        ny = y - 1
                    q = q * factor[ny, nx]
                    nueva[y, x] -= q
                    nueva[ny, nx] += q
        densidad = nueva
        #Desalojo por las salidas
        totalSalida[:] = 0.0
        for k in range(salidaY.shape[0]):
            totalSalida[salidaId[k]] += densidad[salidaY[k], salidaX[k]]
        for k in range(salidaY.shape[0]):
            e = salidaId[k]
            if totalSalida[e] > 0.0:
                sale = min(totalSalida[e], capacidades[e])
                densidad[salidaY[k], salidaX[k]] -= densidad[salidaY[k], salidaX[k]] * sale / totalSalida[e]
        dentro = 0.0
        for y in range(b):
            for x in range(a):
                dentro += densidad[y, x]
        t += dt
        paso += 1
        if guardarCada > 0 and paso % guardarCada == 0 and numCuadros < maxCuadros:
            cuadros[numCuadros] = densidad
            numCuadros += 1
        if dentro < 1.0:
            break
        if t >= tMaximo:
            t = tMaximo
            break
    return t, cuadros[:numCuadros]
