from pathlib import Path
from types import SimpleNamespace

import numpy as np
import healpy as hp
import broom as bm

from src.core.paths import PathManager
from src.simulations.config import Config


class ComponentSeparation:

    def __init__(self, config):

        self.config = config
        self.cleaning_config = config.cleaning
        self.paths = PathManager(config.base_dir)

    def _load_alms(
        self,
        input_file: str | Path,
        keys: tuple[str, str, str],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Load alms from NPZ files.

        Parameter
        ---------
        - input_file: file's path
        - keys: key used in the dictionary 
        """
        input_file = Path(input_file)

        if not input_file.is_file():
            raise FileNotFoundError(
                f"File not found: {input_file}"
            )

        with np.load(input_file) as data:
            missing_keys = [key
                for key in keys
                if key not in data.files
            ]

            if missing_keys:
                raise KeyError(
                    f"Missing keys {missing_keys} "
                    f"in file {input_file}"
                )

            return tuple(data[key] for key in keys)

    @staticmethod
    def observed_alms(
        cmb_alms: tuple[np.ndarray, np.ndarray, np.ndarray],
        foreground_alms: tuple[np.ndarray, np.ndarray, np.ndarray],
        noise_alms: tuple[np.ndarray, np.ndarray, np.ndarray],
        fwhm_arcmin: float,
        nside: int,
        lmax: int,
        apply_pixel_window: bool = True,
    ) -> SimpleNamespace:
        """
        Combine CMB, foreground and instrumental noise in harmonic space.

        Returns
        -------
        SimpleNamespace
            total : Observed sky.

            cmb : CMB after beam/pixel transfer function.

            fgds : Foreground after beam/pixel transfer function.

            noise : Instrumental noise.
        """

        alm_cmb_T, alm_cmb_E, alm_cmb_B = cmb_alms

        alm_fg_T, alm_fg_E, alm_fg_B = foreground_alms

        alm_noise_T, alm_noise_E, alm_noise_B = noise_alms

        expected_size = hp.Alm.getsize(lmax)

        all_alms = (
            alm_cmb_T,
            alm_cmb_E,
            alm_cmb_B,
            alm_fg_T,
            alm_fg_E,
            alm_fg_B,
            alm_noise_T,
            alm_noise_E,
            alm_noise_B,
        )

        if any(len(alm) != expected_size for alm in all_alms):
            raise ValueError(
                "All alm arrays must have the size "
                f"corresponding to lmax={lmax}: "
                f"{expected_size}."
            )

        # Healpy expects FWHM in radians.
        fwhm_rad = fwhm_arcmin *np.pi / (180 * 60) 

        # Columns are approximately T, E, B and TE.
        beam = hp.gauss_beam(fwhm=fwhm_rad, lmax=lmax, pol=True)

        beam_T = beam[:, 0]
        beam_E = beam[:, 1]
        beam_B = beam[:, 2]

        if apply_pixel_window:
            pixel_T, pixel_P = hp.pixwin(nside=nside, pol=True, lmax=lmax)
        else:
            pixel_T = np.ones(lmax + 1)
            pixel_P = np.ones(lmax + 1)

        transfer_T = beam_T * pixel_T
        transfer_E = beam_E * pixel_P
        transfer_B = beam_B * pixel_P

        sky_T = alm_cmb_T + alm_fg_T
        sky_E = alm_cmb_E + alm_fg_E
        sky_B = alm_cmb_B + alm_fg_B

        # Apply instrumental response separately
        # to CMB and foregrounds.
        cmb_T = hp.almxfl(
            alm_cmb_T,
            transfer_T)

        cmb_E = hp.almxfl(
            alm_cmb_E,
            transfer_E)

        cmb_B = hp.almxfl(
            alm_cmb_B,
            transfer_B)

        fg_T = hp.almxfl(
            alm_fg_T,
            transfer_T)

        fg_E = hp.almxfl(
            alm_fg_E,
            transfer_E)

        fg_B = hp.almxfl(
            alm_fg_B,
            transfer_B)

        observed_T = cmb_T + fg_T + alm_noise_T

        observed_E = cmb_E + fg_E + alm_noise_E

        observed_B = cmb_B + fg_B + alm_noise_B

        return SimpleNamespace(
            total=(
                observed_T,
                observed_E,
                observed_B),
            cmb=(
                cmb_T,
                cmb_E,
                cmb_B),
            fgds=(
                fg_T,
                fg_E,
                fg_B),
            noise=(
                alm_noise_T,
                alm_noise_E,
                alm_noise_B))

    @staticmethod
    def bring_to_common_resolution(
        data: SimpleNamespace,
        fwhm_in_arcmin: float,
        fwhm_out_arcmin: float,
        lmax: int,
    ) -> SimpleNamespace:
        """
        Bring one frequency channel to a common angular resolution.
        """

        # Healpy expects FWHM in radians.
        fwhm_in_rad = fwhm_in_arcmin *np.pi / (180 * 60) 

        fwhm_out_rad = fwhm_out_arcmin *np.pi / (180 * 60) 

        beam_in = hp.gauss_beam(fwhm=fwhm_in_rad, lmax=lmax, pol=True)

        beam_out = hp.gauss_beam(fwhm=fwhm_out_rad, lmax=lmax, pol=True)

        transfer_T = beam_out[:, 0]/ beam_in[:, 0]

        transfer_E = beam_out[:, 1]/ beam_in[:, 1]

        transfer_B = beam_out[:, 2]/ beam_in[:, 2]

        return SimpleNamespace(
            total=(
                hp.almxfl(data.total[0], transfer_T),
                hp.almxfl(data.total[1], transfer_E),
                hp.almxfl(data.total[2], transfer_B)),
            cmb=(
                hp.almxfl(data.cmb[0], transfer_T),
                hp.almxfl(data.cmb[1], transfer_E),
                hp.almxfl(data.cmb[2], transfer_B)),
            fgds=(
                hp.almxfl(data.fgds[0], transfer_T),
                hp.almxfl(data.fgds[1], transfer_E),
                hp.almxfl(data.fgds[2], transfer_B)),
            noise=(
                hp.almxfl(data.noise[0], transfer_T),
                hp.almxfl(data.noise[1], transfer_E),
                hp.almxfl(data.noise[2], transfer_B)))

    def load_one_simulation(
        self,
        sim: int,
    ) -> SimpleNamespace:
        """
        Load CMB, foreground and noise products for one realization.

        Returns arrays files with (n_channels, 3, n_alms) shape
        """
        fwhm_out = self.cleaning_config.fwhm_out
        fwhm_armin = self.cleaning_config.fwhm_arcmin
        freq = self.cleaning_config.freq

        nside = self.config.cmb.nside
        lmax = self.config.cmb.lmax

        cmb_dir = self.paths.cmb_alms_file(spectrum="lensed", r=self.config.cmb.r, create_dir=False)

        cmb_file = cmb_dir / f"lmax_{lmax}_sim_{sim:04d}.npz"


        cmb_alms = self._load_alms(cmb_file, keys=("alm_T","alm_E","alm_B"))


        total_channels = []
        cmb_channels = []
        foreground_channels = []
        noise_channels = []

        for i, frequency_ghz in enumerate(freq):

            foreground_file = (self.paths.foreground_alms_dir(model_tag= self.paths.model_tag(self.config.foreground.models), frequency_ghz=frequency_ghz,create_dir=False) 
                               / (f"nside_{nside}_lmax_{lmax}_sim_{sim:04d}.npz"))


            noise_file = (self.paths.noise_alms_dir(experiment=self.config.noise.experiment, noise_model=self.config.noise.model, frequency_ghz=frequency_ghz, create_dir=False)
                          / (f"lmax_{lmax}_sim_{sim:04d}.npz"))

            foreground_alms = self._load_alms(foreground_file, keys=("alm_T","alm_E","alm_B"))

            noise_alms = self._load_alms(noise_file, keys=("alm_T","alm_E","alm_B"))

            observed = self.observed_alms(cmb_alms=cmb_alms, foreground_alms=foreground_alms, noise_alms=noise_alms, fwhm_arcmin=fwhm_armin[i], nside=nside, lmax=lmax)

            obs_common_res = self.bring_to_common_resolution(observed, fwhm_in_arcmin=fwhm_armin[i], fwhm_out_arcmin=fwhm_out, lmax=lmax)

            total_channels.append(obs_common_res.total)

            cmb_channels.append(obs_common_res.cmb)

            foreground_channels.append(obs_common_res.fgds)

            noise_channels.append(obs_common_res.noise)

        return SimpleNamespace(
            total=np.asarray(total_channels),
            cmb=np.asarray(cmb_channels),
            fgds=np.asarray(foreground_channels),
            noise=np.asarray(noise_channels),
            )
    

    def component_separation(
        self,
        data: SimpleNamespace,
        sim: int,
    ) -> list[Path]:
        """
        Perform component separation using the BROOM library.

        Parameters
        ----------
        data: Input data with shape (n_frequency, n_field, n_alm).

        sim: Simulation number to be saving the outputs.

        Returns
        -------
        list[Path]
            Paths to files generated by BROOM.
        """

        output_dir = self.paths.component_separation_dir(create_dir=True)

        self.cleaning_config.path_outputs = output_dir

        self.cleaning_config.save_compsep_products = True
        self.cleaning_config.return_compsep_products = False
        self.cleaning_config.nside_in = self.config.cmb.nside


        bm.component_separation(
            self.cleaning_config,
            data,
            nsim=sim,
        )

        return 

#  FALTA AÑADIR LO DE SI EXISTE ESE ARCHIVO, QUIZAS CON ESTE METODO NO HACE FALTA YA QUE AUN NO SE COMO GUARDA LOS ARCHIVOS.

    def run_many(
        self,
        nsims: int,
        start_sim: int = 0,
    ) -> list[list[Path]]:
        """
        Run component separation for several simulations.

        Parameters
        ----------
        nsims
            Number of simulations to process.

        start_sim
            Index of the first simulation.

        Returns
        -------
        list[list[Path]]
            Generated BROOM products for each simulation.
        """

        outputs = []

        for sim in range(start_sim, start_sim + nsims):
            print(
                f"\nRunning component separation "
                f"for simulation {sim}")

            data = self.load_one_simulation(sim=sim)

            simulation_outputs = (
                self.component_separation(
                    data=data,
                    sim=sim,
                )
            )

            # outputs.append(
            #     simulation_outputs
            # )

        return 

    