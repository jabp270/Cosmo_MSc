from pathlib import Path
import gc
from types import SimpleNamespace

import numpy as np
import healpy as hp
from src.pipeline import plot
import broom as bm

from src.pipeline.simulation_pipelines import pipeline_simulation

from src.core.paths import PathManager

# Path fiducial Cl's
fid_cl_dir = Path("outputs_main/simulations/cmb/cls/r_0.00000/lmax_3000.npz")

cl_fid = np.load(fid_cl_dir)["total"]

# FITS que utilizará BROOM
fid_cl_fits = Path(
    "outputs_main/simulations/cmb/cls/r_0.00000/lmax_3000.fits"
)

hp.write_cl(
    fid_cl_fits,
    cl_fid.T,
    overwrite=True,
)

# Path products
prod_dir = Path("outputs_main/results/plots/BROOM")

# Path output cleaning 
output_dir = Path("outputs_main/products/Comp_sep broom simulations")


# Instrument config
instrument = {

    "frequency": [27, 39, 93, 145, 225, 280],

    "beams": "gaussian",

    "fwhm": [7.4, 5.1, 2.2, 1.4, 1.0, 0.9],

    "depth_I": np.array([71,36,8.0,10,22,54]),

    # "channels_tags": ["27", "39", "93", "145", "225", "280"],

    # SIN 1/f noise

    "ell_knee": None,

    "alpha_knee": None,

    # SIN MAPAS DE PROFUNDIDAD / HITSMAPS
    
    # "path_depth_maps": "",
    # "path_hits_maps": "",
    # "path_beams": "",
}


#Definir el config de broom:
config_values = {

    # --------------------------------------
    # GENERAL CONFIG
    # --------------------------------------

    "lmin": 2, # Minimum multipole considered in the analysis (compsep, power spectrum computation)

    "lmin_in": 0, # Minimum multipole considered in the simulations generation

    "nside": 2048, #256, 

    "nside_in": 2048, #256,

    "lmax": 3000,  #128, # Maximum multipole considered in the analysis (compsep, power spectrum computation)

    "lmax_in": 3000, #128,  # Maximum multipole considered in the simulations generation

    "data_type": "alms",

    "verbose": True,

    "nsim_start": 0,
    
    "nsims": 1,

    "units": "uK_CMB",

    "coordinates": "G",

    "pixel_window_in": True, # Whether to apply pixel window smoothing to the input maps.

    # PATH

    # "data_path": "",

    # "fgds_path": "",

    # "cmb_path": "",

    # "noise_path": "",


    # --------------------------------------
    # CMB CONFIG
    # --------------------------------------

    "generate_input_cmb": False,

    "cls_cmb_path": "",

    "cmb_path": "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs_main/simulations/cmb/alms/r_0.00000/lensed_broom/lmax_3000",

    "cls_cmb_new_ordered": True,

    "seed_cmb": 1000,


    # --------------------------------------
    # FOREGROUND CONFIG
    # --------------------------------------

    "foreground_models": ["s6", "d11"], #"s6", "d11"

    "generate_input_foregrounds": True,

    "return_fgd_components": False, # Whether to return individual foreground components.

    "bandpass_integrate": False, # Whether to integrate sky components across bandpasses.


    # --------------------------------------
    # INSTRUMENT CONFIG
    # --------------------------------------

    "instrument": instrument,


    # --------------------------------------
    # NOISE CONFIG
    # --------------------------------------

    "generate_input_noise": True,

    "seed_noise": 2000,

    # NO ENTIENDO ESTOS PARAMENTROS

    "data_splits": False, # Whether to generate/load noise and data splits.

    "only_splits": False, # Whether to generate/load only noise and data splits, without full coadded maps.

    # --------------------------------------
    # TOTAL DATA CONFIG
    # --------------------------------------

    "generate_input_data": True,

    "save_inputs": True,

    # --------------------------------------
    # COMPONENT SEPARATION CONFIG
    # --------------------------------------

    "fwhm_out": 7.4,

    "bring_to_common_resolution": True,

    "pixel_window_out": False, # Full path (including filename) to the mask .fits file which refers to the observed region.

    "mask_observations": None,

    "mask_covariance": None,

    "leakage_correction": None,

    "save_compsep_products": True,

    "return_compsep_products": True,

    "path_outputs": output_dir,

    "field_in": "TEB",

    "field_out": "TEB",

    ## NILC
    "compsep":[{
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
        "save_weights": True,
        "ilc_bias": 0.001,
        "reduce_ilc_bias": False,
        "cov_noise_debias": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }],


    ## ILC

    # "compsep": [{

    #     "method": "ilc",

    #     "domain": "pixel",

    #     "component_out": "cmb",
        
    # }]

}

config = bm.Configs(config=config_values)

fwhm_rad = np.deg2rad(config.fwhm_out / 60.0) # pasar a radianes

beam = hp.gauss_beam(fwhm=fwhm_rad, lmax=config.lmax, pol=True)

beam_T = beam[:, 0]
beam_E = beam[:, 1]
beam_B = beam[:, 2]

cl_fid_beam = np.zeros((config.lmax + 1, 4))

cl_fid_beam[:, 0] = (cl_fid[:config.lmax + 1, 0] * beam_T**2)

cl_fid_beam[:, 1] = (cl_fid[:config.lmax + 1, 1] * beam_E**2)

cl_fid_beam[:, 2] = (cl_fid[:config.lmax + 1, 2] * beam_B**2)

cl_fid_beam[:, 3] = (cl_fid[:config.lmax + 1, 3] * beam_T * beam_E)

for sim in range(config_values["nsim_start"],config_values["nsim_start"] + config_values["nsims"]):

    #Generar datos SimpleNamespace (total, cmb, foreground, noise)
    data = bm.get_input_data(config, nsim=sim) # (nfreq, nfields, npix)

    #PLOTS MAPS
    # CMB map
    plot.plot_teb_alm(data.cmb[0], prod_dir, f"CMB map", nside=config.nside, lmax=config.lmax)
    del data.cmb

    # Foreground map
    for index, frequency in enumerate(config.instrument.frequency):
        plot.plot_teb_alm(data.fgds[index], prod_dir, f"Foreground map", nside=config.nside, lmax=config.lmax, freq=frequency)
    del data.fgds

    # Noise map
    for index, frequency in enumerate(config.instrument.frequency):
        plot.plot_teb_alm(data.noise[index], prod_dir, f"Noise map", nside=config.nside, lmax=config.lmax, freq=frequency)
    del data.noise

    # Observed map
    for index, frequency in enumerate(config.instrument.frequency):
        plot.plot_teb_alm(data.total[index], prod_dir, f"Observed map", nside=config.nside, lmax=config.lmax, freq=frequency)

    data_cs = SimpleNamespace(total=data.total)
    del data
    gc.collect() # libera las referencias a esos arrays grandes.

    data1 = bm.component_separation(config, data_cs, nsim=sim)
    del data_cs

    # data1 tiene keys "total", "settings"
    # data1.total es una lista

    # data1.total es una lista con un solo elemento
    # data1.total[0] tiene 3 objetos que son mapas no alm
    plot.plot_teb(data1.total[0], output_dir=prod_dir , name="Clean maps")

    # Observed Cls
    Cl_obs = hp.anafast(data1.total[0], data1.total[0], nspec=4, lmax=config.lmax, pol=False) #(4,)

    cl_output_dir = output_dir / "observed Cls"

    cl_output_dir.mkdir(parents=True, exist_ok=True)

    method = config.compsep[0]["method"]

    cl_output_file = (cl_output_dir/ f"Cl_clean_{method}_sim_{sim:04d}.npz")

    np.savez(
    cl_output_file,
    TT=Cl_obs[0],
    EE=Cl_obs[1],
    BB=Cl_obs[2],
    TE=Cl_obs[3],
)


    #   # CMB Cls
    #     Cl_cmb = hp.anafast(data1.cmb, data1.cmb, nspec=4, lmax=config.lmax, pol=False) #(4,)

    #   # Residual foreground Cls
    #     Cl_fgds = hp.anafast(data1.fgds, data1.fgds, nspec=4, lmax=config.lmax, pol=False) #(4,)

    #   # Residual Noise Cls    
    #     Cl_noise = hp.anafast(data1.noise, data1.noise, nspec=4, lmax=config.lmax, pol=False) #(4,)

    ### Plots comparando espectros.
    spectra_names = ["TT","EE","BB","TE"]

    for i, spectrum_name in enumerate(spectra_names):


        fig, ax = plot.plot_spectrum(
            cls=[Cl_obs[i], cl_fid_beam[:, i]],

            lmax=config.lmax,

            label=[
                f"Estimated CMB - {method}",
                "Fiducial CMB",
            ],

            ymin=None,
            ymax=None,

            xlabel=r"$\ell$",
            ylabel=r"$C_\ell\ [\mu K^2]$",

            xlog=False,

            # TE puede ser negativo, por eso no log
            ylog=(spectrum_name != "TE"),
        )

        plot.save_figure(
            output_dir=prod_dir,
            name=f"Cl_{spectrum_name}_comparison_{method}_sim_{sim:04d}.png",
            facecolor="white",
            transparent=False,
        )
