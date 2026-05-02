import os
import numpy as np
import healpy as hp
from config import NSIDE, LMAX, NSIM

# GENERA WIENER FILTER Y C-INVERSE FILTER

# Usamos aproximacion del paper de LiteBIRD

# --------------------------------
# El calculo del Cl de la señal no esta bien ARREGLARLO !!!
# Uso como conocido y debo derivarlo de los alms de HILC
# --------------------------------

def main():

    ruta = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/HILC_maps/Full_sky"

    ruta_1 = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/fiducial"

    ruta_CI = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/CI_filter"

    ruta_W = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/W_filter"

    ruta_HILC = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/HILC_maps/Full_sky"

    r_residuo = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/HILC_residuals"

    vect_r = np.array([0,0.01,0.05,0.1])
    names = np.array(["T", "E" , "B"])

    nsim  = NSIM

    for r in vect_r:

        r_res_r = os.path.join(r_residuo, f'r_{r}')

        d_res = np.load(os.path.join(r_res_r, f"mean_residual_cls.npz"))

        ruta_r = os.path.join(ruta, f'r_{r}')

        ruta_r1 = os.path.join(ruta_1, f'r_{r}')

        out_dir_CI = os.path.join(ruta_CI, f"r_{r}")

        os.makedirs(out_dir_CI, exist_ok=True)

        out_dir_W = os.path.join(ruta_W, f"r_{r}")

        os.makedirs(out_dir_W, exist_ok=True)

        out_HILC_r = os.path.join(ruta_HILC, f"r_{r}")

        # # Calculamos el promedio del Ruido

        # mean_N = {
        #     "T": np.zeros(LMAX + 1),
        #     "E": np.zeros(LMAX + 1),
        #     "B": np.zeros(LMAX + 1),
        # }

        # for i in range(nsim):

        #     data = np.load(os.path.join(ruta_r, f"Nl_HILC{i+1}.npz"))

        #     for name in names:

        #         mean_N[f"{name}"] += data[f"N{name}"]

        # mean_N["T"] /=NSIM
        # mean_N["E"] /=NSIM
        # mean_N["B"] /=NSIM

        # np.savez_compressed(
        #         os.path.join(out_HILC_r, f"Mean_Nl.npz"),
        #         N_T=mean_N["T"],  
        #         N_E=mean_N["E"],  
        #         N_B=mean_N["B"]     
        #         )

        for i in range(nsim):

            Ci = []
            Wi = []

            for name in names:
                
                Cl = np.loadtxt(os.path.join(ruta_r1, f"Cl_total_{name}{name}.txt"))

                C_inv = np.zeros_like(Cl)

                C_inv[2:] = 1/(Cl[2:] + d_res[f"{name}{name}"][2:])

                W_Fil = np.zeros_like(Cl)  

                W_Fil[2:] = Cl[2:]/(Cl[2:] + d_res[f"{name}{name}"][2:])           

                Ci.append(C_inv)

                Wi.append(W_Fil)

            np.savez_compressed(
                os.path.join(out_dir_CI, f"CI_{i+1}.npz"),
                CI_T=Ci[0],  
                CI_E=Ci[1],  
                CI_B=Ci[2]     
                )
            
            np.savez_compressed(
                os.path.join(out_dir_W, f"WF_{i+1}.npz"),
                W_T=Wi[0],  
                W_E=Wi[1],  
                W_B=Wi[2]     
                )


if __name__ == "__main__":
    main()

