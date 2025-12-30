import os
import numpy as np
import healpy as hp

base_outdir = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/camb_outputs/fiducial"

dir = os.path.join(base_outdir, "Noise_SO")
os.makedirs(dir, exist_ok=True)

lmax = 1000
Nside = 512
freq = np.array([27, 39, 93, 145, 225, 280])

# ------------------
# Añadir Ruido Blanco de SO
# ------------------

# Añadimos Ruido de LAT en muK-arcmin
vect_noise = np.array([71,36,8.0,10,22,54])*(np.pi/(60*180))*1e-6 #Tiene unidades de muK

np.random.seed(1234)
for i, noise in enumerate(vect_noise):
    N_ells = np.ones(lmax + 1)*(noise**2)

    alm_noise = hp.synalm(N_ells, lmax=lmax, new=True)

    noise_map = hp.alm2map(alm_noise, nside=Nside, lmax=lmax)

    hp.write_map(os.path.join(dir, f"map_{freq[i]}_LAT.fits"), noise_map, overwrite=True)
    
# ------------------
# Añadir Ruido 1/f no entiendo como añadirlo
# ------------------

# ADEMAS HACE FALTA HACER EL RUIDO PARA LAT Y SAT POR SEPARADO ...
