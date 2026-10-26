import numpy as np

#Diagrama fundamental de Weidmann
velocidadLibre = 1.34
gammaWeidmann = 1.913
densidadMaxima = 5.4

#Salidas segun el modelo hidraulico del SFPE
flujoEspecifico = 1.32
capaLimite = 0.15

#Simulacion
pasoTiempo = 0.3
pasosRecalculo = 6
velocidadMinima = 0.05
tiempoMaximo = 1800.0

#Normativa
factorOcupacion = 0.55
profundidadSalida = 2
anchoPaso = 2

#NSGA-II
probabilidadCruza = 0.9
desplazamientoMaximo = 3


def velocidadWeidmann(densidad):
    densidad = np.asarray(densidad, dtype=float)
    velocidad = np.full(densidad.shape, velocidadLibre)
    hayGente = densidad > 1e-9
    velocidad[hayGente] = velocidadLibre * (1 - np.exp(-gammaWeidmann * (1 / densidad[hayGente] - 1 / densidadMaxima)))
    return np.clip(velocidad, 0.0, velocidadLibre)


#Densidad de flujo maximo
_densidades = np.linspace(0.01, densidadMaxima, 20000)
_flujos = _densidades * velocidadWeidmann(_densidades)
densidadCritica = float(_densidades[np.argmax(_flujos)])
flujoMaximo = float(_flujos.max())
