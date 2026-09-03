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

###### Esta funcion creo que esta mal REVISAR ###################


###### ARREGLAR LO DEL RUIDO, HACER SIMUALCIONES Y HACER LIMPIEZA CON DISTINTOS TIPOS DE METODOS ######


# MOSTRARLE ESO A CLAUDIA

# iDEAS 
# 1) MULTI-TRACER COMO NILC
# 2) HACER QE CON 21-CM Y PROBAR COMO CAMBIA EL MULTI-TRACER
# 3) VER COMO SE PROPAGA EL RESIDUO DE FOREGROUND EN LA ESTIMACION r
# 4) 

# LO QUE ESTOY HACIENDO: AVANZAR CON EL CODIGO PARA PODER HACER UNA ESTIMACION DE r, CON LOS METODOS ACTUALES DE SO Y A LA PAR ESTUDIAR QUE SE PUEDE AÑADIR.


    def white_noise_cls(
        self,
        noise_t: int,
        noise_p: int,
    ) -> dict[str, np.ndarray]:
        """
        Construct constant white-noise spectra.

        Parameters
        -----------
        - noise_t: Map depth of one frecuency in microkelvin-arcmin 
        - noise_p: Map depth of one frecuency in microkelvin-arcmin, equal to noise_t*sqrt(2) 

        Returns N_ell^TT, N_ell^EE and N_ell^BB in K^2.
        """

        noise_t_uk_rad = self.uk_arcmin_to_uk_radian(
            noise_t
        )

        noise_p_uk_rad = self.uk_arcmin_to_uk_radian(
            noise_p
        )

        lmax = self.noise_config.lmax

        n_ell_tt = np.full(
            lmax + 1,
            noise_t_uk_rad**2,
            dtype=float,
        )

        n_ell_ee = np.full(
            lmax + 1,
            noise_p_uk_rad**2,
            dtype=float,
        )

        n_ell_bb = np.full(
            lmax + 1,
            noise_p_uk_rad**2,
            dtype=float,
        )

        return {
            "TT": n_ell_tt,
            "EE": n_ell_ee,
            "BB": n_ell_bb,
        }

    def _component_seed(
            self,
            sim: int,
            sep: int
        ) -> int:
            """
            Generate deterministic independent seeds for
            frequency, simulation and T/E/B component.

            Parameters:
            -----------
            - sim: simulation number
            - sep: number to identify simulation on T = 0, E = 1 and B = 2
            """
            # Quizas añadir mas parametros que cambien la seed como la freq, nside, etc.
            return (
                self.noise_config.noise_seed
                + 10*sim
                + sep
            )

    @staticmethod
    def _synalm_with_seed(
        cls: np.ndarray,
        lmax: int,
        seed: int,
    ) -> np.ndarray:
        """
        Generate alm reproducibly without permanently
        modifying NumPy's global random state.
        """
        random_state = np.random.get_state()

        try:
            np.random.seed(seed)

            alm = hp.synalm(
                cls,
                lmax=lmax,
                new=True,
            )
        finally:
            np.random.set_state(
                random_state
            )

        return alm


    def generate_white_noise_alms(
        self,
        experiment: str,
        model: str,
        frequency: float,
        noise_t: int,
        noise_p: int,
        sim: int,
        overwrite: bool = False,
    ) -> dict[str, Path]:
        """
        Generate, save or reuse homogeneous white-noise alm
        for one frequency and one realization.

        Returns
        -------
        dict[str, Path]
            Paths to the saved noise spectra and alm.
        """
        # ---------------- PATH ------------------

        output_cls_dir = self.paths.noise_cls_dir(
            experiment=experiment,
            noise_model=model,
            create_dir=True,
        )

        output_alms_dir = self.paths.noise_alms_dir(
            experiment=experiment,
            frequency_ghz= frequency,
            noise_model=model,
            create_dir=True,
        )

        cls_name = f"freq_{frequency}_lmax_{self.noise_config.lmax}"

        alms_name = (
            f"lmax_{self.noise_config.lmax}_"
            f"sim_{sim:04d}"
        )

        cls_file = output_cls_dir / f"{cls_name}.npz"
        alms_file = output_alms_dir / f"{alms_name}.npz"

        # ----------------- Cls -------------------

        cls = self.white_noise_cls(
            noise_t=noise_t,
            noise_p=noise_p
        )

        if self.paths.should_compute(
            cls_file,
            overwrite=overwrite,
        ):
            self.save_npz(
                output_dir=output_cls_dir,
                name=cls_name,
                ell=np.arange(
                    self.noise_config.lmax + 1
                ),
                noise_TT=cls["TT"],
                noise_EE=cls["EE"],
                noise_BB=cls["BB"],
            )

            print(
                f"[SAVE] White-noise spectra: {cls_file}"
            )
        else:
            print(
                f"[LOAD] White-noise spectra: {cls_file}"
            )

        if self.paths.should_compute(
            alms_file,
            overwrite=overwrite,
        ):

            seed_t = self._component_seed(
                sim=sim,
                sep=0,
            )

            seed_e = self._component_seed(
                sim=sim,
                sep=1,
            )

            seed_b = self._component_seed(
                sim=sim,
                sep=2,
            )

            alm_T = self._synalm_with_seed(
                cls=cls["TT"],
                lmax=self.noise_config.lmax,
                seed=seed_t,
            )

            alm_E = self._synalm_with_seed(
                cls=cls["EE"],
                lmax=self.noise_config.lmax,
                seed=seed_e,
            )

            alm_B = self._synalm_with_seed(
                cls=cls["BB"],
                lmax=self.noise_config.lmax,
                seed=seed_b,
            )

            self.save_npz(
                output_dir=output_alms_dir,
                name=alms_name,
                alm_T=alm_T,
                alm_E=alm_E,
                alm_B=alm_B,
                seed_T=np.asarray(seed_t),
                seed_E=np.asarray(seed_e),
                seed_B=np.asarray(seed_b),
            )

            print(
                f"[SAVE] White-noise alms: {alms_file}"
            )
        else:
            print(
                f"[LOAD] White-noise alms: {alms_file}"
            )

        return {
            "noise_cls": cls_file,
            "noise_alms": alms_file,
        }


    def simulate_one(
        self,
        sim: int,
        overwrite: bool = False,
        **kwargs,
    ) -> dict[str, Path]:
        """
        Generate one noise realization for every configured
        frequency using the selected model.
        """
        outputs: dict[str, Path] = {}

        model = self.noise_config.model

        for frequency_index, frequency_ghz in enumerate(self.noise_config.freq):
            frequency_tag = self.paths.frequency_tag(
                frequency_ghz
            )

            if model == "white":
                noise_t = self.noise_config.noise_t[frequency_index]

                noise_p = self.noise_config.noise_p[frequency_index]

                products = self.generate_white_noise_alms(
                    experiment=self.noise_config.experiment,
                    model=model,
                    frequency=frequency_ghz,
                    noise_t=noise_t,
                    noise_p=noise_p,
                    sim=sim,
                    overwrite=overwrite,
                )

            elif model == "one_over_f":
                pass

            else:
                raise ValueError(
                    f"Unknown noise model: {model}"
                )

            for product_name, product_path in products.items():
                outputs[
                    f"{product_name}_{frequency_tag}"
                ] = product_path

        return outputs