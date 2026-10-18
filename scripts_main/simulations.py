from pathlib import Path

import numpy as np
import healpy as hp
from src.pipeline import plot

from src.core.paths import PathManager
from src.simulations.cmb_simulator import CmbSimulator
from src.pipeline.simulation_pipelines import pipeline_simulation

from src.simulations.config import (
    Config,
    CmbConfig,
    ForegroundConfig,
    NoiseConfig,
    CleaningConfig,
    InstrumentConfig,
)

# PATH PRODUCTS
prod_dir = Path("outputs_main/results/plots")

def main() -> None:

    cmb_settings = CmbConfig(
        nside=2048, #2048 1024 512
        lmax=3000,  #3000 2048 1024
        r=0.00,
        nsim=1,
        start_sim=1
    )

    foreground_settings = ForegroundConfig(
        models=["s1", "d1"],
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


        ## NILC
        compsep = [{
            "method": "ilc",
            "domain": "needlet",
            "component_out": "cmb",
            "needlet_config": {
                "needlet_windows": "cosine",
                "ell_peaks": [0, 30, 60, 100, 180, 300, 500, 800, 1200, 1800, 2400, 3000],
            },
            "b_squared": False,
            "adapt_nside": True,
            "save_needlets": False,
            "save_weights": False,
            "ilc_bias": 0.001,
            "reduce_ilc_bias": False,
            "cov_noise_debias": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            }],


        # ILC
        # compsep=[
        #     {
        #         "method": "ilc",
        #         "domain": "pixel",
        #         "component_out": "cmb",
        #     }
        # ],

        bring_to_common_resolution=False,

        pixel_window_in=False, ### NO CACHO MUY BIEN A QUE SE REFIEREN
        pixel_window_out=False,

        save_compsep_products=True,

        mask_observations= None, #"SO_maps/Mask_SO/LAT_a5.0deg.fits",
        mask_covariance= None,
        leakage_correction=None, #True

        data_type="maps",
        field_in="TQU",
        field_out="TEB",

    )

    config = Config(
        base_dir="outputs_main",
        cmb=cmb_settings,
        foreground=foreground_settings,
        noise = noise_settings,
        cleaning = cleaning_settings,
    )

    # -------------- PATHS -----------------

    # Instancia de CmbSimulator
    simulator = CmbSimulator(config=config)

    powers = simulator.compute_cls(names=["unlensed_total", "lens_potential"], overwrite=False)

    cl_unl = powers["unlensed_total"]

    cl_phi = powers["lens_potential"]

    sim_pipe = pipeline_simulation(config)

    for sim in range(cmb_settings.start_sim, cmb_settings.start_sim + cmb_settings.nsim):

        maps_clean = sim_pipe.obs_maps(cls=[cl_unl, cl_phi], sim=sim, save=False, overwrite=False, output_prod= prod_dir, mask_tag=None) #"LAT_a5.0deg"
        
if __name__ == "__main__":
    main()