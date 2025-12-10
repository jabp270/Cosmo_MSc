import camb
import numpy as np
import os

# Crear carpeta de salida
base_outdir = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/camb_outputs/fiducial"
os.makedirs(base_outdir, exist_ok=True)

# ---------------------------
# 1. Simulamos con CAMB el best-fit de Planck con distintos r's
# ---------------------------

# Diversos valores de r para nuestras simulaciones
vect_r = np.array([0,0.05,0.1])

for r in vect_r:
    print(f"> Procesando r = {r}")
    print("HOLA")
    r_dir = os.path.join(base_outdir, f"r_{r}")
    print(f"{r_dir}")
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
    lmax = 3000
    pars.set_for_lmax(lmax, lens_potential_accuracy=2)
    
    # ---------------------------
    # 2. Correr CAMB
    # ---------------------------

    results = camb.get_results(pars)
    
    # ---------------------------
    # 3. Obtener Cls y matter power spectrum
    # ---------------------------

    powers = results.get_cmb_power_spectra(pars, CMB_unit='muK', spectra=['total', 'unlensed_scalar', 'lens_potential'], raw_cl=True)
    
    # LLamamos los diferentes CLs
    total_Cl = powers['total']
    unlensed_Cl = powers['unlensed_scalar']
    lens_potential_Cl = powers['lens_potential']

    #crea un vector de los \ells 
    vect_ells = np.arange(unlensed_Cl[:, 0].shape[0]) 

    # Multipolos
    np.savetxt(os.path.join(r_dir, "ells.txt"), vect_ells)

    # # Cl totales (lensed)
    # np.savetxt(os.path.join(r_dir, "Cl_total_TT.txt"), total_Cl[:, 0])
    # np.savetxt(os.path.join(r_dir, "Cl_total_EE.txt"), total_Cl[:, 1])
    # np.savetxt(os.path.join(r_dir, "Cl_total_BB.txt"), total_Cl[:, 2])
    # np.savetxt(os.path.join(r_dir, "Cl_total_TE.txt"), total_Cl[:, 3])

    # # Cl unlensed
    # np.savetxt(os.path.join(r_dir, "Cl_unlensed_TT.txt"), unlensed_Cl[:, 0])
    # np.savetxt(os.path.join(r_dir, "Cl_unlensed_EE.txt"), unlensed_Cl[:, 1])
    # np.savetxt(os.path.join(r_dir, "Cl_unlensed_BB.txt"), unlensed_Cl[:, 2])
    # np.savetxt(os.path.join(r_dir, "Cl_unlensed_TE.txt"), unlensed_Cl[:, 3])

    # # Cl del lensing potential
    # np.savetxt(os.path.join(r_dir, "Cl_phiphi.txt"), lens_potential_Cl[:, 0])

    # print(f"> Archivos guardados en {r_dir}\n")

