from pathlib import Path

import numpy as np
import healpy as hp

from src.core.paths import PathManager
from src.filtering.wiener import WienerFilter
from src.lensing.lensing import CmbLensing
from src.pipeline.simulation_pipelines import pipeline_simulation

from src.simulations.config import (
    Config,
    CmbConfig,
    ForegroundConfig,
    NoiseConfig,
    CleaningConfig,
    InstrumentConfig,
    LensingConfig,
)

# Path fiducial Cl's
fid_cl_dir = Path("outputs_main/simulations/cmb/cls/r_0.00000/lmax_3000.npz")

def main() -> None:

    cmb_settings = CmbConfig(
        nside=2048, #2048 1024 512
        lmax=3000,  #3000 2048 1024
        r=0.00,
        nsim=1,
    )

    foreground_settings = ForegroundConfig(
        models=["s6", "d11"],
        freq=[27, 39, 93, 145, 225, 280], 
        nside=2048,
        lmax=3000,
        nsim=1,
    )

    noise_settings = NoiseConfig(
        model="white",
        experiment="SO_LAT",
        freq=[27, 39, 93, 145, 225, 280], 
        noise_t=[71,36,8.0,10,22,54],
        noise_p=np.array(np.array([71,36,8.0,10,22,54]))*np.sqrt(2),
        nside=2048,
        lmax=3000,
        nsim=1,
    )

    instrument_settings = InstrumentConfig(
        frequency=noise_settings.freq,
        depth_I=noise_settings.noise_t,
        depth_P=noise_settings.noise_p,
        fwhm=np.array([7.4, 5.1, 2.2, 1.4, 1.0, 0.9]),
        channels_tags=["f027","f039","f093","f145","f225","f280"],
        beams="gaussian",
        )

    cleaning_settings = CleaningConfig(
        freq=[27, 39, 93, 145, 225, 280],

        fwhm_arcmin=np.array([7.4, 5.1, 2.2, 1.4, 1.0, 0.9]),

        fwhm_out=7.4,

        lmax=3000,
        nside=2048,

        instrument=instrument_settings,

        path_outputs=Path("outputs_main/products/component_separation"),

        compsep=[
            {
                "method": "ilc",
                "domain": "pixel",
                "component_out": "cmb",
            }
        ],

        bring_to_common_resolution=False,

        pixel_window_in=True,
        pixel_window_out=False,

        save_compsep_products=True,

        mask_observations= None, #"SO_maps/Mask_SO/LAT_a5.0deg.fits",
        mask_covariance= None,
        leakage_correction=None, #True

        data_type="maps",
        field_in="TQU",
        field_out="TQU",

    )

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
        cmb=cmb_settings,
        foreground=foreground_settings,
        noise = noise_settings,
        cleaning = cleaning_settings,
        lensing=lensing_settings
    )

    # -------------- PATHS -----------------
    paths = PathManager(config.base_dir)

    sim_pipe = pipeline_simulation(config)

    # instancia de wiener filter
    filter = WienerFilter(config.wiener)

    # Instancia de CmbLensing
    lensing = CmbLensing(config)

    # fiducial spectra.
    cl_fid = np.load(fid_cl_dir)["total"] #(ells, 4)

    for sim in range(lensing_settings.start_sim, lensing_settings.start_sim + lensing_settings.nsim):

        maps_clean = sim_pipe.obs_maps(cl=cl_fid, sim=sim, save=False, overwrite=False, mask_tag=None) #"LAT_a5.0deg"

        # Observed Cls
        Cl_obs = hp.anafast(maps_clean.total[0], maps_clean.total[0], nspec=4, lmax=config.lensing.lmax, pol=True) #(4,)
        
        # Noise spectra (Here we can include a effective noise spectra)
        nl_signal = None 

        # Instancia de Wieneer filter
        #filter = filter.harmonic_filters()

        ##### ESTO ES TEMPORAL HASTA SABER BIEN QUE PONER EN RESIDUAL_NL #####
        CI_filt = np.zeros((3, config.lensing.lmax + 1))

        CI_filt[:, config.lensing.rlmin:] = (1.0 / cl_fid[config.lensing.rlmin:,:3].T)

        print(CI_filt.shape)

        # Cinverse filter
        # CI_filt = filter.harmonic_filters(signal_cl= cl_fid, residual_nl=nl_signal)["Cinv"]

        alm_obs = hp.map2alm(maps_clean.total[0], lmax=config.lensing.lmax, pol=True) #(3, Npix)

        for i, name in enumerate(["T", "E", "B"]):
            print(
                name,
                "shape =", alm_obs[i].shape,
                "dtype =", alm_obs[i].dtype,
                "max =", np.max(np.abs(alm_obs[i])),
                "mean =", np.mean(np.abs(alm_obs[i])),
                "nonzero =", np.count_nonzero(alm_obs[i]),
                "finite =", np.all(np.isfinite(alm_obs[i])),
            )

        del maps_clean

        alm_CI = filter.apply_harmonic(alms=alm_obs, transfer=CI_filt)

        for i, name in enumerate(["T", "E", "B"]):
            print(
                name,
                "shape =", alm_CI[i].shape,
                "dtype =", alm_CI[i].dtype,
                "max =", np.max(np.abs(alm_CI[i])),
                "mean =", np.mean(np.abs(alm_CI[i])),
                "nonzero =", np.count_nonzero(alm_CI[i]),
                "finite =", np.all(np.isfinite(alm_CI[i])),
            )

        reconstruction = lensing.QE_reconstruct_one(FC=[cl_fid[:,0], cl_fid[:,1], cl_fid[:,2], cl_fid[:,3]], OC=Cl_obs, alms_CI=alm_CI)

        lensing.save_reconstruction(rec=reconstruction, sim=sim)

if __name__ == "__main__":
    main()