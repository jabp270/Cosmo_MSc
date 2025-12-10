import numpy as np
import os
import healpy as hp

### HACER DIVERSOS MODELOS Y CADA UNO GUARDALOS EN UNA CARPETA ###
# De esta manera luego solo sumo con el CMB aplico beam y window function mas ruido
# aplicamos wiener filter, luego separacion de componentes HILC
# A esos mapas aplicamos Delensing interno y comparamos con los originales
# Luego añadir otros tracers --> combinacion de ellos