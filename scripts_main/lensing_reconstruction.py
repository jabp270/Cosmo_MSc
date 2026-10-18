from pathlib import Path

import numpy as np
import healpy as hp

from src.core.paths import PathManager
from src.filtering.wiener import WienerFilter
from src.lensing.lensing import CmbLensing
from src.simulations.config import Config, LensingConfig

# Path after component separation 
maps_cs_dir = Path("outputs_main/products/component_separation/ilc_needlet_bias0.001/cosine_0_30_60_100_180_300_500_800_1200_1800_2400_3000/cmb_reconstruction")

# Path fiducial Cl's
fid_cl_dir = Path("outputs_main/simulations/cmb/cls/r_0.00000/lmax_3000.npz")


### VER COMO CAMBIA AL AÑADIR MASCARA !!!

def main() -> None:

    lensing_settings = LensingConfig(
        nside=2048,
        lmax=3000,
        rlmin=100,
        rlmax=3000,
        elmin=100,
        elmax=3000,
        QDO=(True, True, True, True, True, False),
        nsim=1,
        start_sim=1,

        fwhm_out = 7.4,
        Folder_name="Full_ILC_reconstruction"
    )

    config = Config(
        base_dir="outputs_main",
        lensing=lensing_settings
    )

    # -------------- PATHS -----------------
    paths = PathManager(config.base_dir)

    # fiducial spectra.
    cl_fid = np.load(fid_cl_dir)["total"] #(ells, 4)

    def load_cs_maps(name, sim):
        path = paths.path_output_cs(
            files_dir=maps_cs_dir, name=name,
            sim=sim, lmax=config.lensing.lmax, nside=config.lensing.nside, beam_out=config.lensing.fwhm_out)
        m = hp.read_map(path, field=None)  # (3, npix) -> T, E, B
        return m 

    for sim in range(lensing_settings.start_sim, lensing_settings.start_sim + lensing_settings.nsim):

        maps_clean = load_cs_maps(name="output_total", sim=sim)  # T, E, B after component separation (3, Npix)

        # Observed Cls
        Cl_obs = hp.anafast(maps_clean, maps_clean, nspec=4, lmax=config.lensing.lmax, pol=False) #(3,)

        # Noise spectra (Here we can include a effective noise spectra)
        nl_signal = None 

        # Instancia de Wieneer filter
        filter = WienerFilter("Harmonic")

        # Cinverse filter
        # CI_filt = filter.harmonic_filters(signal_cl= cl_fid, residual_nl=nl_signal)["Cinv"]

        # Instancia de CmbLensing
        lensing = CmbLensing(config)

        alm_obs = hp.map2alm(maps_clean, lmax=config.lensing.lmax, pol=False) #(3, Npix)

        # Esto hay que arreglarlo, no se hace en un pipeline real
        alm_CI = [hp.almxfl(alm_obs[i], cl_fid[:, i]/Cl_obs[i]) for i in range(3)]
        
        reconstruction = lensing.QE_reconstruct_one(FC=[cl_fid[:,0], cl_fid[:,1], cl_fid[:,2], cl_fid[:,3]], OC=Cl_obs, alms_CI=alm_CI)

        lensing.save_reconstruction(rec=reconstruction, sim=sim)

if __name__ == "__main__":
    main()