import camb
import numpy as np
import os
import healpy as hp

# Crear carpeta de salida
base_outdir = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/camb_outputs/fiducial"
os.makedirs(base_outdir, exist_ok=True)

# ---------------------------
# 1. Simulamos con CAMB el best-fit de Planck con distintos r's
# ---------------------------

# Diversos valores de r para nuestras simulaciones
vect_r = np.array([0,0.01,0.05,0.1])

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
    lmax = 3000
    pars.set_for_lmax(lmax, lens_potential_accuracy=2)
    
    # ---------------------------
    # 2. Correr CAMB
    # ---------------------------

    results = camb.get_results(pars)
    
    # ---------------------------
    # 3. Obtener Cls y matter power spectrum
    # ---------------------------

    powers = results.get_cmb_power_spectra(pars, lmax=3000, CMB_unit='K', spectra=['total', 'unlensed_scalar', 'lens_potential'], raw_cl=True)
    
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

    print(f"> Archivos guardados en {r_dir}\n")

    # ---------------------------
    # 4) Generamos mapas
    # ---------------------------

    print("> Generando mapas con healpy ...") 
    np.random.seed(1234)
    alm_tot = hp.synalm((total_Cl[:, 0], total_Cl[:, 1],total_Cl[:, 2], total_Cl[:, 3]), lmax=3000, new=True)
    np.random.seed(1234)
    alm_unlensed = hp.synalm((unlensed_Cl[:, 0], unlensed_Cl[:, 1], unlensed_Cl[:, 2], unlensed_Cl[:, 3]), lmax=3000, new=True)

    nside = 1024
    #lmax = 3*nside - 1 debe ser mayor al dado por camb

    cmb_map_total = hp.alm2map(alm_tot, nside=nside, lmax=3000)
    cmb_map_unlensed = hp.alm2map(alm_unlensed, nside=nside, lmax=3000)

    hp.write_map(os.path.join(r_dir, "map_total_T.fits"), cmb_map_total[0], overwrite=True)
    hp.write_map(os.path.join(r_dir, "map_total_Q.fits"), cmb_map_total[1], overwrite=True)
    hp.write_map(os.path.join(r_dir, "map_total_U.fits"), cmb_map_total[2], overwrite=True)

    hp.write_map(os.path.join(r_dir, "map_unlensed_T.fits"), cmb_map_unlensed[0], overwrite=True)
    hp.write_map(os.path.join(r_dir, "map_unlensed_Q.fits"), cmb_map_unlensed[1], overwrite=True)
    hp.write_map(os.path.join(r_dir, "map_unlensed_U.fits"), cmb_map_unlensed[2], overwrite=True)

    np.random.seed(1234)
    map_phi = hp.synfast([lens_potential_Cl[:,0]], nside=nside, lmax=3000, pol=False, new=True)

    hp.write_map(os.path.join(r_dir, "map_phiphi.fits"), map_phi, overwrite=True)

    print("> Guardando los mapas...")

