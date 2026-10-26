import heapq

import numpy as np
from numba import njit


#Fast Marching Method con muros en las aristas
@njit(cache=True)
def resolverEikonal(libre, abiertoE, abiertoO, abiertoN, abiertoS, velocidad, semillasY, semillasX):
    b, a = libre.shape
    infinito = np.inf
    tiempo = np.full((b, a), infinito)
    aceptado = np.zeros((b, a), dtype=np.bool_)
    monticulo = [(0.0, 0, 0)]
    monticulo.pop()
    for k in range(semillasY.shape[0]):
        y = semillasY[k]
        x = semillasX[k]
        if libre[y, x] and tiempo[y, x] > 0.0:
            tiempo[y, x] = 0.0
            heapq.heappush(monticulo, (0.0, y, x))
    while len(monticulo) > 0:
        t, y, x = heapq.heappop(monticulo)
        if aceptado[y, x]:
            continue
        aceptado[y, x] = True
        for d in range(4):
            if d == 0:
                if not abiertoE[y, x]:
                    continue
                ny, nx = y, x + 1
            elif d == 1:
                if not abiertoO[y, x]:
                    continue
                ny, nx = y, x - 1
            elif d == 2:
                if not abiertoN[y, x]:
                    continue
                ny, nx = y + 1, x
            else:
                if not abiertoS[y, x]:
                    continue
                ny, nx = y - 1, x
            if not libre[ny, nx] or aceptado[ny, nx]:
                continue
            h = 1.0 / velocidad[ny, nx]
            tHorizontal = infinito
            if abiertoE[ny, nx] and aceptado[ny, nx + 1]:
                tHorizontal = tiempo[ny, nx + 1]
            if abiertoO[ny, nx] and aceptado[ny, nx - 1]:
                tHorizontal = min(tHorizontal, tiempo[ny, nx - 1])
            tVertical = infinito
            if abiertoN[ny, nx] and aceptado[ny + 1, nx]:
                tVertical = tiempo[ny + 1, nx]
            if abiertoS[ny, nx] and aceptado[ny - 1, nx]:
                tVertical = min(tVertical, tiempo[ny - 1, nx])
            if tHorizontal == infinito or tVertical == infinito or abs(tHorizontal - tVertical) >= h:
                candidato = min(tHorizontal, tVertical) + h
            else:
                candidato = (tHorizontal + tVertical + np.sqrt(2.0 * h * h - (tHorizontal - tVertical) ** 2)) / 2.0
            if candidato < tiempo[ny, nx]:
                tiempo[ny, nx] = candidato
                heapq.heappush(monticulo, (candidato, ny, nx))
    return tiempo
