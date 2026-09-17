import camb
import numpy as np
import os
import healpy as hp
from utils_JB import make_seeds
from config import NSIDE, LMAX, NSIM, BASE_SEED, RUTA_0, RUTA_1

def main():

    # Crear carpeta de salida
    base_outdir = RUTA_1
    os.makedirs(base_outdir, exist_ok=True)

    # #lmax = 3*nside - 1 debe ser mayor al dado por camb
    nside = NSIDE
    lmax  = LMAX
    nsim  = NSIM
    base_seed  = BASE_SEED

    seeds = make_seeds(nsim, base_seed=base_seed)

    # ---------------------------
    # 1. Simulamos con CAMB el best-fit de Planck con distintos r's
    # ---------------------------

    # Diversos valores de r para nuestras simulaciones
    vect_r = np.array([0, 0.01, 0.05, 0.1])

    for r in vect_r:
        print(f"> Procesando r = {r}")

        r_dir = os.path.join(base_outdir, f"r_{r}")
        os.makedirs(r_dir, exist_ok=True)

        pars = camb.CAMBparams()
        pars.set_cosmology(
            H0 = 67.66,
            ombh2 = 0.02242 ,
            omch2 = 0.11933,
            tau = 0.0561
        )

        # Activar calculo de perturbaciones tensoriales y lensing
        pars.WantTensors = True
        pars.Want_CMB_lensing = True

        pars.InitPower.set_params(
            As = 2.105e-9,
            ns = 0.9665,
            r=r
        )

        # Máximo multipolo que queremos
        pars.set_for_lmax(lmax, lens_potential_accuracy=5)
        
        # ---------------------------
        # 2. Correr CAMB
        # ---------------------------

        results = camb.get_results(pars)
        
        # ---------------------------
        # 3. Obtener Cls y matter power spectrum
        # ---------------------------

        powers = results.get_cmb_power_spectra(pars, lmax=lmax, CMB_unit='K', spectra=['total', 'unlensed_scalar', 'lens_potential'], raw_cl=True)
        
        # LLamamos los diferentes CLs
        total_Cl = powers['total']
        unlensed_Cl = powers['unlensed_scalar']
        lens_potential_Cl = powers['lens_potential']

        #crea un vector de los \ells 
        vect_ells = np.arange(unlensed_Cl[:, 0].shape[0]) 

        # Multipolos
        np.savetxt(os.path.join(r_dir, "ells.txt"), vect_ells)

        # Cl totales (lensed)
        np.savetxt(os.path.join(r_dir, "Cl_total_TT.txt"), total_Cl[:, 0])
        np.savetxt(os.path.join(r_dir, "Cl_total_EE.txt"), total_Cl[:, 1])
        np.savetxt(os.path.join(r_dir, "Cl_total_BB.txt"), total_Cl[:, 2])
        np.savetxt(os.path.join(r_dir, "Cl_total_TE.txt"), total_Cl[:, 3])

        # Cl unlensed
        np.savetxt(os.path.join(r_dir, "Cl_unlensed_TT.txt"), unlensed_Cl[:, 0])
        np.savetxt(os.path.join(r_dir, "Cl_unlensed_EE.txt"), unlensed_Cl[:, 1])
        np.savetxt(os.path.join(r_dir, "Cl_unlensed_BB.txt"), unlensed_Cl[:, 2])
        np.savetxt(os.path.join(r_dir, "Cl_unlensed_TE.txt"), unlensed_Cl[:, 3])

        # Cl del lensing potential
        np.savetxt(os.path.join(r_dir, "Cl_phiphi.txt"), lens_potential_Cl[:, 0])

        ### FALTA AÑADIR EL MATTER POWER SPECTRUM ###

        print(f"> Generando {nsim} simulaciones")

        # ---------------------------
        # 4) Generamos mapas
        # ---------------------------

        for i in range(nsim):

            seed = seeds[i]

            # np.random.seed(seed["cmb"])
            # alm_tot_T, alm_tot_E, alm_tot_B = hp.synalm((total_Cl[:, 0], total_Cl[:, 1],total_Cl[:, 2], total_Cl[:, 3]), lmax=lmax, new=True)
            np.random.seed(seed["cmb"])
            alm_unlensed_T, alm_unlensed_E, alm_unlensed_B = hp.synalm((unlensed_Cl[:, 0], unlensed_Cl[:, 1], unlensed_Cl[:, 2], unlensed_Cl[:, 3]), lmax=lmax, new=True)

            # Debido al peso de los mapas guardamos de manera compacta como alm's y archivo npz
            # np.savez_compressed(
            #     os.path.join(r_dir, f"cmb_alms_total{i+1}.npz"),
            #     almT=alm_tot_T,  
            #     almE=alm_tot_E,  
            #     almB=alm_tot_B     
            #     )
    
            np.savez_compressed(
                os.path.join(r_dir, f"cmb_alms_unlensed{i+1}.npz"),
                almT=alm_unlensed_T, 
                almE=alm_unlensed_E, 
                almB=alm_unlensed_B     
                )

            np.random.seed(seed["phi"])
            map_phi = hp.synfast([lens_potential_Cl[:,0]], nside=nside, lmax=lmax, pol=False, new=True)
            alm_phi = hp.map2alm(map_phi, lmax=lmax)


            np.savez_compressed(
                os.path.join(r_dir, f"cmb_alms_phi{i+1}.npz"),
                alm_phi=alm_phi,     
                )

        print("> Guardando los mapas...")

if __name__ == "__main__":
    main()