import numpy as np
import os
import healpy as hp
import pysm3 as pysm
import pysm3.units as u
from config import NSIDE, LMAX, NSIM, BASE_SEED

def main():
    ruta_f = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/fiducial/Foreground"

    nside = NSIDE
    lmax  = LMAX
    nsim  = NSIM
    base_seed  = BASE_SEED

    freq = np.array([27, 39, 93, 145, 225, 280])

    os.makedirs(ruta_f, exist_ok=True) # crea la carpeta Foreground de ser necesario

    # -----------------------------
    # Modelo 1: SIMPLE s1 + d1
    # -----------------------------

    print('Formando mapas del modelo simple')

    dir_1 = os.path.join(ruta_f, "Simple")
    os.makedirs(dir_1, exist_ok=True)

    # Crear un cielo fisico con modelos d1 polvo y s1 sincrotron
    sky = pysm.Sky(nside=nside, preset_strings=["d1", "s1"],output_unit="K_CMB") 

    for f in freq:
        print(f"Formando mapas de frecuencia: {f}")
        map = sky.get_emission(f*u.GHz) #tiene I, Q y U

        alm_fg_T = hp.map2alm(map[0], lmax=lmax, use_pixel_weights=True)

        alm_fg_E, alm_fg_B = hp.sphtfunc.map2alm_spin(np.array([map[1],map[2]]), spin=2, lmax=lmax)

        np.savez_compressed(
                os.path.join(dir_1, f"alms_fg_{f}.npz"),
                almT=alm_fg_T, 
                almE=alm_fg_E, 
                almB=alm_fg_B     
                )


    # -----------------------------
    # Modelo 2: 
    # -----------------------------

if __name__ == "__main__":
    main()