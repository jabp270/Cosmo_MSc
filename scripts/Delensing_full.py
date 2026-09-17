from curvedsky import delens, utils
import plottools as pl
import os
import numpy as np
import healpy as hp
import matplotlib.pyplot as plt
from scripts.config import NSIDE, LMAX, NSIM

ruta = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/rec_lensing/r_0.0"

ruta_f = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/fiducial/r_0.0"

nside = NSIDE
lmax  = LMAX
nsim  = NSIM

elmin, elmax = 100, lmax
rlmin, rlmax = 100, lmax

L = np.linspace(0,lmax,lmax+1)
Lfac = (L*(L+1.))**2/(2*np.pi)

data = np.load(os.path.join(ruta, f"rec_pot_{5}.npz"))

data2 = np.load(os.path.join(ruta_f, f"cmb_alms_phi{5}.npz")) # cargar phi
alm_phi = data2["alm_phi"]

cl_phi = hp.alm2cl(alm_phi,lmax=lmax)

alm_phi = utils.lm_healpy2healpix(alm_phi, lmax=lmax)

glm = data[f"glmMV"]

ruta_HILC = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/HILC_maps/Full_sky/r_0.0"

ruta_W ="/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/W_filter/r_0.0"

data = np.load(os.path.join(ruta_HILC, f"alms_{5}.npz"))

data_1 = np.load(os.path.join(ruta_W, f"WF_{5}.npz"))

W_l = data_1["W_E"]

Ealm = utils.lm_healpy2healpix(data["almE"], lmax=lmax)

Ealm *= W_l

lalm = delens.lensingb(lmax,elmin,elmax,rlmin,rlmax,Ealm[:elmax+1,:elmax+1],alm_phi[:rlmax+1,:rlmax+1])

bb = utils.alm2cl(lmax,lalm,lalm)

plt.plot(L,bb )
plt.show()
