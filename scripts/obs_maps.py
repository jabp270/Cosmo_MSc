import os
import numpy as np
import healpy as hp
import matplotlib.pyplot as plt
from config import NSIDE, LMAX, NSIM, BASE_SEED

# -------------------------
# Generar mapas observador 
# -------------------------

def main():
    ruta = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/fiducial/"

    ruta_f = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/fiducial/Foreground/"

    ruta_n = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/fiducial/Noise_SO"

    ruta_obs = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/obs_maps"

    ruta_filt = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/fiducial/fil_window"

    nside = NSIDE
    lmax  = LMAX
    nsim  = NSIM
    base_seed  = BASE_SEED


    # Diversos valores de r para nuestras simulaciones
    vect_r = np.array([0, 0.01, 0.05, 0.1])

    freq = np.array([27, 39, 93, 145, 225, 280])

    names = np.array(["T", "E" , "B"])

    names_f = np.array(["Simple"])

    ruta_f1 = os.path.join(ruta_f, "Simple")

    # Filtro por Beam y Window pixel
    pwT, pwP = hp.pixwin(nside, pol=True, lmax=lmax) # window pixel

    vect_fwhm = np.array([7.4, 5.1, 2.2, 1.4, 1.0, 0.9])*np.pi / (180 * 60) #en radianes

    list_fil = {}
    for j,f in enumerate(freq):
        list_fil[f] = {}
        beam = hp.sphtfunc.gauss_beam(fwhm=vect_fwhm[j], lmax=lmax, pol=True)
        # bT  = beam[:, 0]   # temperatura
        # bE  = beam[:, 1]   # grad/electric (E)
        # bB  = beam[:, 2]   # curl/magnetic (B)

        for i, name in enumerate(names):
            if name == "T":
                fil = beam[:, i] * pwT
            else:
                fil = beam[:, i] * pwP
            
            list_fil[f][name] = fil

    # Cargamos las simulaciones para cada r
    for r in vect_r:

        print(f"> Cargando r = {r}")
        
        ruta_r = os.path.join(ruta, f"r_{r}")

        ruta_obs_r = os.path.join(ruta_obs, f"r_{r}")
        os.makedirs(ruta_obs_r, exist_ok=True)
        
        for i in range(nsim):

            data = np.load(os.path.join(ruta_r, f"cmb_alms_total{i+1}.npz")) # cargar cmb_total

            for f in freq:
                
                data_f = np.load(os.path.join(ruta_f1, f"alms_fg_{f}.npz")) # cargar alm foregrounds

                data_n = np.load(os.path.join(ruta_n, f"alm_{f}_LAT{i+1}.npz")) # cargar alm ruido

                # lista de alms orden T, E y B 

                alm_obs = []
                for name in names:
                    
                    alm = data[f"alm{name}"] 

                    alm1 = data_f[f"alm{name}"] 

                    alm_sum = alm + alm1

                    alm_fil = hp.almxfl(alm_sum, list_fil[f][name])

                    alm2 = data_n[f"alm_noise_{name}"]

                    alm_obs.append(alm_fil + alm2) 
                
                np.savez_compressed(
                    os.path.join(ruta_obs_r, f"alm_obs_{f}_LAT{i+1}.npz"),
                    almT=alm_obs[0],
                    almE=alm_obs[1],
                    almB=alm_obs[2]
                    )

if __name__ == "__main__":
    main()