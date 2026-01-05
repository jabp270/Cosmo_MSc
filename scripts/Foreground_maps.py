import numpy as np
import os
import healpy as hp
import pysm3 as pysm
import pysm3.units as u

base_outdir = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/camb_outputs/fiducial"

nside = 128

dir = os.path.join(base_outdir, "Foreground")
os.makedirs(dir, exist_ok=True)

### HACER DIVERSOS MODELOS Y CADA UNO GUARDALOS EN UNA CARPETA ###
# De esta manera luego solo sumo con el CMB aplico beam y window function mas ruido
# aplicamos wiener filter, luego separacion de componentes HILC
# A esos mapas aplicamos Delensing interno y comparamos con los originales
# Luego añadir otros tracers --> combinacion de ellos

# -----------------------------
# Modelo 1: SIMPLE s1 + d1
# -----------------------------

print('Formando mapas del modelo simple')

dir_0 = os.path.join(dir, "Simple")
os.makedirs(dir_0, exist_ok=True)

# Crear un cielo fisico con modelos d1 polvo y s1 sincrotron
sky = pysm.Sky(nside=nside, preset_strings=["d1", "s1"],output_unit="K_CMB") 

# vector de frecuencias que queremos los mapas de foregrounds USAMOS LOS DE SO
freq = np.array([27, 39, 93, 145, 225, 280])

map_27 = sky.get_emission(freq[0]*u.GHz) #tiene I, Q y U
map_39 = sky.get_emission(freq[1]*u.GHz)
map_93 = sky.get_emission(freq[2]*u.GHz)
map_145 = sky.get_emission(freq[3]*u.GHz)
map_225 = sky.get_emission(freq[4]*u.GHz)
map_280 = sky.get_emission(freq[5]*u.GHz)

print('Guardando mapas')

hp.write_map(os.path.join(dir_0, "map_27_T.fits"), map_27[0], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_39_T.fits"), map_39[0], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_93_T.fits"), map_93[0], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_145_T.fits"), map_145[0], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_225_T.fits"), map_225[0], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_280_T.fits"), map_280[0], overwrite=True)

hp.write_map(os.path.join(dir_0, "map_27_Q.fits"), map_27[1], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_39_Q.fits"), map_39[1], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_93_Q.fits"), map_93[1], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_145_Q.fits"), map_145[1], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_225_Q.fits"), map_225[1], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_280_Q.fits"), map_280[1], overwrite=True)

hp.write_map(os.path.join(dir_0, "map_27_U.fits"), map_27[2], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_39_U.fits"), map_39[2], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_93_U.fits"), map_93[2], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_145_U.fits"), map_145[2], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_225_U.fits"), map_225[2], overwrite=True)
hp.write_map(os.path.join(dir_0, "map_280_U.fits"), map_280[2], overwrite=True)

# -----------------------------
# Modelo 2: 
# -----------------------------