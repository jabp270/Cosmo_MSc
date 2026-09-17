import os
import numpy as np
import healpy as hp
from config import NSIDE, LMAX, NSIM
from curvedsky import rec_lens, norm_quad, utils as cs_utils


# Genera la reconstruccion del potencial de lensing usando los datos del CMB

# Es necesario correrlo con el enviroment de cmblensplus

# Es necesario cambiar lo de los Cls y añadir el "EB"

ruta = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/HILC_maps/Full_sky"

ruta_f = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/fiducial/"

ruta_out = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/rec_lensing"

ruta_CI = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/CI_filter"

vect_r = np.array([0,0.01,0.05,0.1])
freq = np.array([27, 39, 93, 145, 225, 280])
names = np.array(["T", "E" , "B"])
names1 = np.array(["TT", "EE", "BB", "TE"])

nside = NSIDE
lmax  = LMAX
nsim  = NSIM

rlmin, rlmax = 100, lmax #100, 3000  # CMB multipole range for reconstruction

for r in vect_r:

    print(f"r = {r}")

    ruta_r = os.path.join(ruta, f"r_{r}")

    ruta_f_r = os.path.join(ruta_f, f"r_{r}")

    ruta_CI_r = os.path.join(ruta_CI, f"r_{r}")

    out_dir = os.path.join(ruta_out, f"r_{r}")

    os.makedirs(out_dir, exist_ok=True)

    Cl_total = []
    for name2 in names1:
        tot_cl =  np.loadtxt(os.path.join(ruta_f_r, f"Cl_total_{name2}.txt"))
        Cl_total.append(tot_cl)

    for i in range(nsim):

        glm, clm = {}, {}

        Ag, Ac = {}, {}

        data = np.load(os.path.join(ruta_r, f"alms_{i+1}.npz"))

        data_CI = np.load(os.path.join(ruta_CI_r, f"CI_{i+1}.npz"))

        dic_alm = {}

        for name in names:

            alm = data[f"alm{name}"]

            C_inv = data_CI[f"CI_{name}"]

            alm_CI = hp.almxfl(alm, C_inv)

            alm_healpix = cs_utils.lm_healpy2healpix(alm_CI, lmax=lmax)  # devuelve (rlmax+1, rlmax+1)

            dic_alm[f"{name}"] = alm_healpix #los alm segun healpix


        # Calcula el estimador cuadratico de cada combinacion

        QDO = [True,True,True,True,True,False] # this means that TT, TE, EE, TB and EB are used for MV estimator
            

        Ag, Ac, Wg, Wc = norm_quad.qall('lens',QDO,lmax,rlmin,rlmax,Cl_total, Cl_total) # AQUI DEBO CAMBIAR EL ULTIMO POR EL OBSERVADO

        glm['TT'], clm['TT'] = rec_lens.qtt(lmax,rlmin,rlmax,Cl_total[0],dic_alm["T"],dic_alm["T"],nside_t=nside)
        glm['EE'], clm['EE'] = rec_lens.qee(lmax,rlmin,rlmax,Cl_total[1],dic_alm["E"],dic_alm["E"],nside_t=nside)
        glm['EB'], clm['EB'] = rec_lens.qeb(lmax,rlmin,rlmax,Cl_total[1],dic_alm["E"],dic_alm["B"],nside_t=nside)
        glm['TB'], clm['TB'] = rec_lens.qtb(lmax,rlmin,rlmax,Cl_total[3],dic_alm["T"],dic_alm["B"],nside_t=nside)
        glm['TE'], clm['TE'] = rec_lens.qte(lmax,rlmin,rlmax,Cl_total[3],dic_alm["T"],dic_alm["E"],nside_t=nside)
        #glm['BB'], clm['BB'] = rec_lens.qbb(lmax,rlmin,rlmax,Cl_total[2],dic_alm["B"],dic_alm["B"],nside_t=nside) #Se ignora

        # Aplicamos la normalizacion a los estimadores
        for qi, q in enumerate(['TT','TE','EE','TB','EB']):
            glm[q] *= Ag[qi,:,None]
            #clm[q] *= Ac[qi,:,None]


        # Se calcula el estimador MV
        glm['MV'], clm['MV'] = 0., 0.
        for qi, q in enumerate(['TT','TE','EE','TB','EB']):
            glm['MV'] += Wg[qi,:,None]*glm[q]
            clm['MV'] += Wc[qi,:,None]*clm[q]
        glm['MV'] *= Ag[5,:,None] #Normalizacion
        #clm['MV'] *= Ac[5,:,None]

        np.savez_compressed(
            os.path.join(out_dir, f"rec_norm_{i+1}.npz"),
            agTT=Ag[0,:],
            agEE=Ag[1,:],
            agEB=Ag[2,:],
            agTB=Ag[3,:],
            agTE=Ag[4,:],
            agMV=Ag[5,:]  
        )  

        np.savez_compressed(
            os.path.join(out_dir, f"rec_pot_{i+1}.npz"),
            glmTT=glm["TT"],
            glmEE=glm["EE"],
            glmEB=glm["EB"],
            glmTB=glm["TB"],
            glmTE=glm["TE"],
            glmMV=glm["MV"]  
        )      

        # np.savez_compressed(
        #     os.path.join(out_dir, f"rec_seudo_{i+1}.npz"),
        #     clmTT=clm["TT"],
        #     clmEE=clm["EE"],
        #     clmBB=clm["BB"],
        #     clmTE=clm["TE"]    
        # )      




