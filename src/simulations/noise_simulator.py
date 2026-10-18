from pathlib import Path

import healpy as hp
import numpy as np

from src.core.paths import PathManager
from src.simulations.base_simulator import BaseSimulator
from src.simulations.config import Config



class NoiseSimulator(BaseSimulator):
    """
    Generate homogeneous and isotropic white-noise realizations.
    """

    def __init__(
        self,
        config: Config,
    ):

        path_manager = PathManager(
            config.base_dir
        )

        super().__init__(
            config=config,
            path_manager=path_manager,
        )

        self.noise_config = config.noise

    @staticmethod
    def uk_arcmin_to_uk_radian(
        noise_uk_arcmin: float,
    ) -> float:
        """
        Convert map depth from microkelvin-arcmin
        to kelvin-radian.
        """
        return (
            noise_uk_arcmin
            * np.pi       # 1e-6 se multiplica por 1e-6 para convertir de microkelvin a kelvin
            / (180.0 * 60.0)       
        )

    def white_noise_cls(
        self,
        noise_t: float,
        noise_p: float,
    ) -> dict[str, np.ndarray]:
        """
        Construct homogeneous white-noise angular power spectra.

        Parameters
        ----------
        noise_t : float
            Temperature map depth [uK arcmin].

        noise_p : float
            Polarization map depth [uK arcmin].

        Returns
        -------
        dict
            White-noise spectra:
            TT, EE, BB, TE
            in uK^2.
        """

        delta_t = self.uk_arcmin_to_uk_radian(noise_t)

        delta_p = self.uk_arcmin_to_uk_radian(noise_p)

        lmax = self.noise_config.lmax

        nl_tt = np.full(lmax + 1,delta_t**2,dtype=float)

        nl_ee = np.full(lmax + 1,delta_p**2,dtype=float)

        nl_bb = np.full(lmax + 1,delta_p**2,dtype=float)

        nl_te = np.zeros(lmax + 1)

        return {
            "TT": nl_tt,
            "EE": nl_ee,
            "BB": nl_bb,
            "TE": nl_te,
        }

    
    def _noise_seed(
        self,
        sim: int,
        freq: float,
    ) -> int:
        """
        Generate deterministic seed for one
        frequency and simulation.
        """

        freq_key = int(round(freq * 1000))

        seed_sequence = np.random.SeedSequence(
            [
                int(self.noise_config.noise_seed),
                int(sim),
                freq_key,
            ]
        )

        return int(seed_sequence.generate_state(1)[0])

    @staticmethod
    def _synalm_with_seed(
        cls: list[np.ndarray],
        lmax: int,
        seed: int,
    ) -> np.ndarray:
        """
        Generate a polarized T,Q,U realization from
        TT, EE, BB and TE spectra.

        Returns
        -------
        np.ndarray
            Shape (3, npix), ordered as T,E,B.
        """

        random_state = np.random.get_state()

        try:

            np.random.seed(seed)
            maps = hp.synalm(cls, lmax=lmax, new=True)

        finally:

            np.random.set_state(random_state)

        return maps


    def generate_white_noise_maps(
        self,
        experiment: str,
        model: str,
        frequency: float,
        noise_t: float,
        noise_p: float,
        sim: int,
        save: bool = False,
        overwrite: bool = False,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate or load homogeneous white-noise
        T,E,B maps.

        Noise spectra are defined in harmonic space as

            N_l^TT = Delta_T^2
            N_l^EE = Delta_P^2
            N_l^BB = Delta_P^2
            N_l^TE = 0

        where Delta is expressed in uK-radian.
        """

        # ==========================================================
        # PATHS
        # ==========================================================

        output_cls_dir = self.paths.noise_cls_dir(
            experiment=experiment,
            noise_model=model,
            create_dir=True,
        )

        output_alms_dir = self.paths.noise_alms_dir(
            experiment=experiment,
            frequency_ghz=frequency,
            noise_model=model,
            create_dir=True,
        )

        cls_name = (
            f"freq_{frequency}_"
            f"lmax_{self.noise_config.lmax}"
        )

        alms_name = (
            f"nside_{self.noise_config.nside}_"
            f"sim_{sim:04d}"
        )

        cls_file = (
            output_cls_dir
            / f"{cls_name}.npz"
        )

        alms_file = (
            output_alms_dir
            / f"{alms_name}.fits"
        )


        # ==========================================================
        # WHITE-NOISE Cl
        # ==========================================================

        cls = self.white_noise_cls(noise_t=noise_t, noise_p=noise_p)


        # ==========================================================
        # SAVE Cl
        # ==========================================================

        if save:

            self.save_npz(
                output_dir=output_cls_dir,
                name=cls_name,

                ell=np.arange(
                    self.noise_config.lmax + 1
                ),

                noise_TT=cls["TT"],
                noise_EE=cls["EE"],
                noise_BB=cls["BB"],
                noise_TE=cls["TE"],
            )

            print(
                f"[SAVE] White-noise spectra: "
                f"{cls_file}"
            )


        # ==========================================================
        # LOAD EXISTING MAP
        # ==========================================================

        if not self.paths.should_compute(
            alms_file,
            overwrite=overwrite,
        ):

            print(
                f"[LOAD] White-noise alms: "
                f"{alms_file}"
            )

            alms = hp.read_map(
                alms_file,
                field=(0, 1, 2),
                dtype=np.float64,
            )

            return (alms[0],alms[1],alms[2])


        # ==========================================================
        # SEED
        # ==========================================================

        seed = self._noise_seed(sim=sim,freq=frequency)


        # ==========================================================
        # GENERATE T,Q,U
        # ==========================================================

        alms = self._synalm_with_seed(
            cls=[cls["TT"],cls["EE"],cls["BB"],cls["TE"]],
            lmax=self.noise_config.lmax,
            seed=seed,
        )

        # ==========================================================
        # SAVE MAP
        # ==========================================================

        if save:

            hp.write_map(alms_file,alms,overwrite=overwrite,dtype=np.float64)

            print(f"[SAVE] White-noise alms: "f"{alms_file}")


        return alms

    def simulate_one(
        self,
        sim: int,
        frequency_ghz: float,
        save: bool = False,
        overwrite: bool = False,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:

        model = self.noise_config.model

        index = self.noise_config.freq.index(
            frequency_ghz
        )

        if model == "white":

            noise_t = self.noise_config.noise_t[index]

            noise_p = self.noise_config.noise_p[index]

            maps = self.generate_white_noise_maps(
                experiment=self.noise_config.experiment,
                model=model,
                frequency=frequency_ghz,
                noise_t=noise_t,
                noise_p=noise_p,
                sim=sim,
                save=save,
                overwrite=overwrite,
            )

        elif model == "one_over_f":

            raise NotImplementedError(
                "1/f noise is not implemented yet."
            )

        else:

            raise ValueError(
                f"Unknown noise model: {model}"
            )

        return maps