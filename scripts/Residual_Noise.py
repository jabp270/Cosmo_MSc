import os
import numpy as np
import healpy as hp
from config import LMAX, NSIM

def main():
    # alms de salida del HILC
    ruta_hilc = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/HILC_maps/Full_sky"

    # alms del CMB verdadero 
    ruta_true = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/fiducial"

    # salida de residuals
    out_dir = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/HILC_residuals"
    os.makedirs(out_dir, exist_ok=True)

    vect_r = np.array([0, 0.01, 0.05, 0.1])

    for r in vect_r:
        print(f"> r = {r}")

        ruta_r_hilc = os.path.join(ruta_hilc, f"r_{r}")
        ruta_r_true = os.path.join(ruta_true, f"r_{r}")
        out_dir_r = os.path.join(out_dir, f"r_{r}")
        os.makedirs(out_dir_r, exist_ok=True)

        mean_res_TT = np.zeros(LMAX + 1)
        mean_res_EE = np.zeros(LMAX + 1)
        mean_res_BB = np.zeros(LMAX + 1)

        for sim in range(NSIM):
            # HILC output
            d_clean = np.load(os.path.join(ruta_r_hilc, f"alms_{sim+1}.npz"))
            almT_clean = d_clean["almT"]
            almE_clean = d_clean["almE"]
            almB_clean = d_clean["almB"]

            # true CMB input
            d_true = np.load(os.path.join(ruta_r_true, f"cmb_alms_total{sim+1}.npz"))
            almT_true = d_true["almT"]
            almE_true = d_true["almE"]
            almB_true = d_true["almB"]

            # residual = clean - true
            almT_res = almT_clean - almT_true
            almE_res = almE_clean - almE_true
            almB_res = almB_clean - almB_true

            # spectra del residual
            ClTT_res = hp.alm2cl(almT_res, lmax=LMAX)
            ClEE_res = hp.alm2cl(almE_res, lmax=LMAX)
            ClBB_res = hp.alm2cl(almB_res, lmax=LMAX)

            mean_res_TT += ClTT_res
            mean_res_EE += ClEE_res
            mean_res_BB += ClBB_res

        mean_res_TT /= NSIM
        mean_res_EE /= NSIM
        mean_res_BB /= NSIM

        np.savez_compressed(
            os.path.join(out_dir_r, "mean_residual_cls.npz"),
            TT=mean_res_TT,
            EE=mean_res_EE,
            BB=mean_res_BB
        )

if __name__ == "__main__":
    main()