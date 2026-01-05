import numpy as np
import healpy as hp
import lenspyx as ls
import os

ruta = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/camb_outputs/fiducial/"

vect_r = np.array([0,0.01,0.05,0.1])
names = np.array(["T", "E" , "B"])

nside = 128
lmax = 128
nsim = 20

for r in vect_r:

    print(f"> r = {r}")
    
    ruta_r = os.path.join(ruta, f"r_{r}")

    # lista de alms orden T, E y B 
    
    ells = np.loadtxt(os.path.join(ruta_r, "ells.txt"))

    for i in range(nsim):

        alm = []
        for name in names:

            data1 = np.load(os.path.join(ruta_r, f"cmb_alms_unlensed{i+1}.npz"))
            alm1 = data1[f"alm{name}"] 
            alm.append(alm1)
            
        data2 = np.load(os.path.join(ruta_r, f"cmb_alms_phi{i+1}.npz"))
        alm_phi = data2["alm_phi"] 

        # Generar el angulo de desviacion d = sqrt(L(L+1))\phi
        F_l = np.sqrt(ells*(ells+1))
        dglm =  hp.almxfl(alm_phi, F_l)

        T_len, Q_len, U_len = ls.alm2lenmap(
            [alm[0], alm[1], alm[2]],
            dlms=[dglm],  # (gradiente) ; curl omitido
            geometry=('healpix', {'nside': nside}),
            epsilon=1e-7,
            pol=True
            )

        # Pasamos los mapas a alms
        almT_len = hp.map2alm(T_len, lmax=lmax)

        almE_len, almB_len = hp.map2alm_spin([Q_len, U_len], spin=2, lmax=lmax)

        # Guardamos
        np.savez_compressed(
            os.path.join(ruta_r, f"cmb_alms_total{i+1}.npz"),
            almT=almT_len,  
            almE=almE_len,  
            almB=almB_len     
            )