from pathlib import Path

import healpy as hp
import pysm3 as pysm
import pysm3.units as u
import numpy as np

from src.simulations.base_simulator import BaseSimulator
from src.core.paths import PathManager
from src.simulations.config import Config

class ForegroundSimulator(BaseSimulator):
    """
    class for foregrounds, compute model with PYSM3.
    """

    def __init__(self, Config):
        path_manager = PathManager(Config.base_dir)

        super().__init__(
            config=Config.foreground,
            path_manager=path_manager,
        )

    def get_foreground_maps(
        self,
        models: list[str],
        frequency_ghz: float,
        sim: int,
        save: bool = False,
        overwrite: bool = False,
    ) -> np.ndarray:
        """
        Generate foreground I, Q and U maps, for one frequency.

        Returns
        -------
        np.ndarray
            Array with shape (3, npix), ordered as I, Q, U, in mK_CMB.
        """

        model_name = self.paths.model_tag(models)

        maps_dir = self.paths.foreground_maps_dir(
            model_tag=model_name,
            frequency_ghz=frequency_ghz,
        )

        filename = (
            f"nside_{self.config.nside}_"
            f"lmax_{self.config.lmax}_"
            f"sim_{sim:04d}"
        )

        map_file = maps_dir / f"{filename}.fits"

        # Load or generate alm.
        if self.paths.should_compute(
            map_file,
            overwrite=overwrite,
        ):

            sky = pysm.Sky(
                nside= self.config.nside,
                preset_strings= models,
                output_unit=u.uK_CMB,
            )
    
            emission = sky.get_emission(
                frequency_ghz * u.GHz
            )
    
            maps = emission.to_value(u.uK_CMB)

            if save == True:
                hp.write_map(
                    map_file,
                    maps,
                    overwrite=overwrite,
                    dtype=np.float64,
                )

                print(
                    f"[SAVE] Foreground map: {map_file}"
                )

        else:
            print(
                f"[LOAD] Foreground map: {map_file}"
            )

            maps = hp.read_map(
                map_file,
                field=(0,1,2)
            )

        return maps #(3, npix)

    def get_foreground_alms(
        self,
        maps: np.ndarray,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        """
        Transform I, Q and U foreground maps into T, E and B alm.
        """

        alm_T, alm_E, alm_B = hp.map2alm(
            maps,
            lmax=self.config.lmax,
            pol=True,
            use_pixel_weights=False,
        )

        return alm_T, alm_E, alm_B

    # def simulate_frequency(
    #     self,
    #     models: list[str],
    #     frequency_ghz: float,
    #     sim: int,
    #     overwrite: bool = False,
    # ) -> dict[str, Path]:
    #     """
    #     Generate or load foreground maps and alm for one frequency.
    #     """
    #     model_name = self.paths.model_tag(models)

    #     alm_dir = self.paths.foreground_alms_dir(
    #         model_tag=model_name,
    #         frequency_ghz=frequency_ghz,
    #     )

    #     filename = (
    #         f"nside_{self.config.nside}_"
    #         f"lmax_{self.config.lmax}_"
    #         f"sim_{sim:04d}"
    #     )

    #     alm_file = alm_dir / f"{filename}.npz"

    #     # Load or generate alm.
    #     if self.paths.should_compute(
    #         alm_file,
    #         overwrite=overwrite,
    #     ):

    #         maps = self.get_foreground_maps(
    #             models=models,
    #             frequency_ghz=frequency_ghz,
    #         )

    #         alm_T, alm_E, alm_B = (
    #             self.get_foreground_alms(maps)
    #         )

    #         self.save_npz(
    #             output_dir=alm_dir,
    #             name=filename,
    #             alm_T=alm_T,
    #             alm_E=alm_E,
    #             alm_B=alm_B,
    #         )

    #         print(
    #             f"[SAVE] Foreground alms: {alm_file}"
    #         )

    #     else:
    #         print(
    #             f"[LOAD] Foreground alms: {alm_file}"
    #         )

    #     return {
    #         "alms": alm_file,
    #     }

    def simulate_one(
        self,
        sim: int,
        save: bool = False,
        overwrite: bool = False,
    ) -> dict[str, np.ndarray]:
        """
        Generate all configured foreground frequencies
        for one realization.
        """
        outputs: dict[str, np.ndarray] = {}

        models = self.config.models

        for frequency_ghz in self.config.freq:
            maps = self.get_foreground_maps(
                models=models,
                frequency_ghz=frequency_ghz,
                sim=sim,
                save=save,
                overwrite=overwrite,
            )

            alms = self.get_foreground_alms(maps)


            outputs[f"{frequency_ghz}"] = alms

        return outputs

    ### Configurar usando parametros de foregrounds


