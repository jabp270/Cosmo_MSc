from pathlib import Path

from src.component_separation.cleaning import (
    ComponentSeparation,
)

from src.simulations.config import (
    Config,
    CmbConfig,
    ForegroundConfig,
    NoiseConfig,
    CleaningConfig,
    InstrumentConfig,
)

import numpy as np

def main() -> None:

    cmb_settings = CmbConfig(
        nside=2048, #2048 1024 512
        lmax=3000,  #3000 2048 1024
        r=0.00,
        nsim=10,
    )

    foreground_settings = ForegroundConfig(
        models=["s6", "d11"],
        freq=[27, 39, 93, 145, 225, 280], 
        nside=2048,
        lmax=3000,
        nsim=10,
    )

    noise_settings = NoiseConfig(
        model="white",
        experiment="SO_LAT",
        freq=[27, 39, 93, 145, 225, 280], 
        noise_t=[71,36,8.0,10,22,54],
        noise_p=np.array(np.array([71,36,8.0,10,22,54]))*np.sqrt(2),
        nside=2048,
        lmax=3000,
        nsim=10,
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

        path_outputs=Path(
            "outputs_main/products/component_separation"
        ),

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

        mask_observations=None,
        mask_covariance=None,
        leakage_correction=None,

        data_type="alms",
        field_in="TEB",

    )

    simulation_config = Config(
        base_dir=Path("outputs_main"),

        cmb=cmb_settings,

        foreground=foreground_settings,

        noise=noise_settings,

        cleaning=cleaning_settings,
    )

    component_sep = ComponentSeparation(
        config=simulation_config,
    )

    outputs = component_sep.run_many(
        nsims=simulation_config.cmb.nsim,
        start_sim=1,
    )

if __name__ == "__main__":
    main()