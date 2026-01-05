import os
import numpy as np
import healpy as hp
from utils_JB import make_seeds

base_outdir = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/camb_outputs/fiducial"

dir = os.path.join(base_outdir, "Noise_SO")
os.makedirs(dir, exist_ok=True)

lmax = 128
Nside = 128
nsim = 20
base_seed = 972581

seeds = make_seeds(nsim, base_seed=base_seed)

freq = np.array([27, 39, 93, 145, 225, 280])

# ------------------
# Añadir Ruido Blanco de SO
# ------------------

# Añadimos Ruido de LAT en muK-arcmin
# Ruido para la Temperatura
vect_noise_T = np.array([71,36,8.0,10,22,54])*(np.pi/(60*180))*1e-6 #Tiene unidades de muK

# Ruido para la Polarizacion mapas Q y U --> es sqrt(2) mas grande que el de T
vect_noise_P = vect_noise_T*np.sqrt(2)

for i, noise in enumerate(vect_noise_T):
    print(f"Frecuencia: {freq[i]}")
    for j in range(nsim):
        
        seed = seeds[j]

        N_T_ells = np.ones(lmax + 1)*(noise**2)

        N_P_ells = np.ones(lmax + 1)*(vect_noise_P[i]**2)

        np.random.seed(seed["noise_T"])
        alm_T_noise = hp.synalm(N_T_ells, lmax=lmax, new=True)

        np.savez_compressed(
            os.path.join(dir, f"alm_{freq[i]}_LAT_T{j+1}.npz"),
            alm_noise_T=alm_T_noise,    
            )
        
        np.random.seed(seed["noise_Q"])
        alm_Q_noise = hp.synalm(N_P_ells, lmax=lmax, new=True)

        np.savez_compressed(
            os.path.join(dir, f"alm_{freq[i]}_LAT_Q{j+1}.npz"),
            alm_noise_Q=alm_Q_noise,    
            )

        np.random.seed(seed["noise_U"])
        alm_U_noise = hp.synalm(N_P_ells, lmax=lmax, new=True)

        np.savez_compressed(
            os.path.join(dir, f"alm_{freq[i]}_LAT_U{j+1}.npz"),
            alm_noise_U=alm_U_noise,    
            )
    
# ------------------
# Añadir Ruido 1/f no entiendo como añadirlo
# ------------------

# ADEMAS HACE FALTA HACER EL RUIDO PARA LAT Y SAT POR SEPARADO ...
