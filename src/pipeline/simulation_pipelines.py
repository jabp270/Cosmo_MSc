# Este archivo tiene como proposito ser el responsable de hacer simulaciones de una forma u otra.from pathlib import Path

from types import SimpleNamespace

import numpy as np
import healpy as hp
import broom as bm

from src.core.paths import PathManager
from pathlib import Path
from src.pipeline.plot import *

from src.component_separation.cleaning import ComponentSeparation
from src.simulations.cmb_simulator import CmbSimulator
from src.simulations.foreground_simulator import ForegroundSimulator
from src.simulations.noise_simulator import NoiseSimulator 


class pipeline_simulation:

    def __init__(self, config):

        self.config = config
        self.paths = PathManager(config.base_dir)
        self.cmb = CmbSimulator(config)
        self.foreground = ForegroundSimulator(config)
        self.noise = NoiseSimulator(config)
        self.comp_sep = ComponentSeparation(config)

    def obs_maps(self, cls, sim, save, overwrite, output_prod = None,  mask_tag= str | None, return_cmb=False, return_fgds=False, return_noise=False):
        """ 
        Retorna los mapas observados TQU de una realización


        CONSIDERACION LOS CMB; FOREGROUND Y NOISE RETORNADOS EN SIMPLENAMESPACE NO ESTAN APLICADOS CON EL BEAM NI EL PIXEL PARA COMPARARLOS CON LOS MAPA CLEAN DEBERIA AÑADIR ESO.

        ------
        Return

        SimpleNamespace["total", "cmb", "fgds", "noise"]
        """

        cfg = self.config

        freqs = list(cfg.foreground.freq)
        fwhm = cfg.cleaning.instrument.fwhm
        fwhm_out = cfg.cleaning.fwhm_out

        nside = cfg.cmb.nside
        lmax = cfg.cmb.lmax

        cmb_alms = self.cmb.simulate_one(cls=cls, sim=sim)[:3] #guarda phi tambien con [:3] queda fuera

        # Simula todas las configuraciones de foreground a toda frecuencia
        foreground_alms = self.foreground.simulate_one(sim=sim,save=save,overwrite=overwrite) 

        total = {}
        fgds = {}
        noise = {}

        for index, freq in enumerate(freqs):

            fg_alms = foreground_alms[str(freq)] # por frecuencia

            noise_alms = self.noise.simulate_one(sim=sim, frequency_ghz=freq, save=save, overwrite=overwrite) 

            # Generate TQU maps at common resolution
            obs_maps = self.comp_sep.observed_maps(cmb_alms=cmb_alms, foreground_alms=fg_alms, noise_alms=noise_alms, fwhm_arcmin=fwhm[index], fwhm_out=fwhm_out, nside= nside, lmax=lmax, return_cmb=return_cmb, return_fgds=return_fgds, return_noise=return_noise, apply_pixel_window=self.config.cleaning.pixel_window_in) #tuple[np.ndarray, np.ndarray, np.ndarray]

            total[freq] = obs_maps.total

            if return_fgds:
                fgds[freq] = obs_maps.fgds
            del fg_alms

            if return_noise:
                noise[freq] = obs_maps.noise
            del noise_alms

        freqs = self.config.foreground.freq

        #crear SimpleNameSpace multifrecuencia
        output = {"total": np.asarray([total[f] for f in freqs])}  #(nfreq, nfields, npix)
        del total

        if return_cmb:
            cmb_maps = hp.alm2map(cmb_alms,nside=nside,lmax=lmax,pol=True)

            output["cmb"] = np.broadcast_to(cmb_maps, (len(freqs), *cmb_maps.shape))
            del cmb_maps, cmb_alms

        if return_fgds:
            output["fgds"] = np.asarray([fgds[f] for f in freqs])
        del fgds

        if return_noise:
            output["noise"] = np.asarray([noise[f] for f in freqs])
        del noise

        data = SimpleNamespace(**output)
        del output

        data1 = self.comp_sep.component_separation(data=data, sim=sim, mask_tag=mask_tag)
        del data

        if output_prod!=None:
            plot_teb(data1.total[0], output_dir=output_prod, name="Clean maps")


        return data1 # TEB maps with leakage purification by Broom
