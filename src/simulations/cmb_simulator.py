from collections.abc import Sequence
from pathlib import Path

import camb
import healpy as hp
import lenspyx as ls
import numpy as np

from src.simulations.base_simulator import BaseSimulator
from src.core.paths import PathManager

class CmbSimulator(BaseSimulator):
    """
    class for CMB, compute cls, alms unlensed and lensed. 
    """

    VALID_SPECTRA = {
        "total",
        "unlensed_scalar",
        "unlensed_total",
        "lensed_scalar",
        "tensor",
        "lens_potential",
    }

    def __init__(self, config):
        path_manager = PathManager(config.base_dir)

        super().__init__(
            config=config.cmb,
            path_manager=path_manager,
        )


    def get_camb_results(self):
        """
        Configure and run CAMB.

        Returns
        -------
        - pars: The CAMB parameters used for the simulation.
        - results: The results from CAMB, including the computed power spectra.
        """
        pars = camb.CAMBparams()

        pars.set_cosmology(
            H0=67.66,
            ombh2=0.02242,
            omch2=0.11933,
            tau=0.0561,
        )

        pars.WantTensors = True
        pars.Want_CMB_lensing = True

        pars.InitPower.set_params(
            As=2.105e-9,
            ns=0.9665,
            r=self.config.r,
        )

        pars.set_for_lmax(
            self.config.lmax,
            lens_potential_accuracy=5,
        )

        results = camb.get_results(pars)

        return pars, results

    def compute_cls(
        self,
        names: Sequence[str],
        overwrite: bool = False,
    ) -> dict[str, np.ndarray]:
        """
        Compute or load CAMB angular power spectra.

        All requested spectra are stored in the same NPZ file.
        """
        names = list(names)

        if not names:
            raise ValueError(
                "At least one spectrum must be requested."
            )

        invalid_names = set(names) - self.VALID_SPECTRA

        if invalid_names:
            raise ValueError(
                f"Invalid CAMB spectra: {sorted(invalid_names)}"
            )

        output_dir = self.paths.cmb_cls_file(
            r=self.config.r,
        )

        output_file = (
            output_dir
            / f"lmax_{self.config.lmax}.npz"
        )

        # If overwrite=True or the file does not exist,
        # compute all requested spectra.
        if self.paths.should_compute(
            output_file,
            overwrite=overwrite,
        ):
            print(
                "[CAMB] Computing spectra: "
                + ", ".join(names)
            )

            pars, results = self.get_camb_results()

            powers = results.get_cmb_power_spectra(
                pars,
                lmax=self.config.lmax,
                CMB_unit="muK",
                spectra=names,
                raw_cl=True,
            )

            arrays_to_save = {
                name: powers[name]
                for name in names
            }

            arrays_to_save["ell"] = np.arange(
                self.config.lmax + 1
            )

            self.save_npz(
                output_dir,
                name=f"lmax_{self.config.lmax}",
                **arrays_to_save,
            )

            print(f"[SAVE] CMB spectra: {output_file}")

            return {
                name: powers[name]
                for name in names
            }

        # Otherwise, load the existing file.
        stored = self.load_npz(output_file)

        missing_in_file = [
            name
            for name in names
            if name not in stored
        ]

        if missing_in_file:
            raise KeyError(
                "The existing Cl file does not contain the "
                f"requested spectra: {missing_in_file}. "
                "Use overwrite=True to recompute the file."
            )

        print(f"[LOAD] CMB spectra: {output_file}")

        return {
            name: stored[name]
            for name in names
        }


    def generate_unlensed_cmb_alms(
        self,
        cmb_cls: np.ndarray,
        sim: int,
        overwrite: bool = False,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:

        """
        Generate or load T, E and B alm.

        Parameters
        ----------
        - cmb_cls: The angular power spectra (Cls) for the CMB [TT, EE, BB, TE].
        - sim: The simulation index, used to derive a unique random seed.
        - overwrite: Whether to overwrite existing alm files.  

        Returns
        -------
        A tuple containing the alm coefficients for T, E, and B modes. 
        """
        
        output_path = self.paths.cmb_alms_file(
            spectrum="unlensed",
            r=self.config.r,
        )

        output_path1 = output_path / f"lmax_{self.config.lmax}_sim_{sim:04d}.npz"
        # Check if the alms already exist and should be loaded instead of generated.
        if not self.paths.should_compute(output_path1, overwrite=overwrite):
            stored = self.load_npz(output_path1)

            print(f"[LOAD] CMB alms: {output_path1}")

            return (
                stored["alm_T"],
                stored["alm_E"],
                stored["alm_B"],
            )

        cl_tt = cmb_cls[:, 0]
        cl_ee = cmb_cls[:, 1]
        cl_bb = cmb_cls[:, 2]
        cl_te = cmb_cls[:, 3]

        # Generate a unique seed for this simulation.
        seed = self.config.cmb_seed + sim

        np.random.seed(seed)
        alms = hp.synalm(
            [cl_tt, cl_ee, cl_bb, cl_te],
            lmax=self.config.lmax,
            new=True,
        )

        self.save_npz(
            output_path,
            name=f"lmax_{self.config.lmax}_sim_{sim:04d}",
            alm_T=alms[0],
            alm_E=alms[1],
            alm_B=alms[2],
        )

        print(f"[SAVE] Unlensed alms, simulation {sim}: {output_path}")

        return alms

    def generate_phi_alm(
            self,
        lens_potential_cls: np.ndarray,
        sim: int,
        overwrite: bool = False,
    ) -> np.ndarray:
        """
        Generate or load lensing potential alm.

        Parameters
        ----------
        - lens_potential_cls: The angular power spectrum (Cls) for the lensing potential.
        - sim: The simulation index, used to derive a unique random seed.
        - overwrite: Whether to overwrite existing alm files.  

        Returns
        -------
        The alm coefficients for the lensing potential.
        """

        output_path = self.paths.cmb_alms_file(
            spectrum="lens_potential",
            r=self.config.r,
        )

        output_path1 = output_path / f"lmax_{self.config.lmax}_sim_{sim:04d}.npz"
        # Check if the alms already exist and should be loaded instead of generated.
        if not self.paths.should_compute(output_path1, overwrite=overwrite):
            stored = self.load_npz(output_path1)

            print(f"[LOAD] Lensing potential alms: {output_path1}")

            return stored["alm_phi"]

        cl_phi = lens_potential_cls[:, 0]

        # Generate a unique seed for this simulation.
        seed = self.config.phi_seed + sim

        np.random.seed(seed)
        alm_phi = hp.synalm(
            cl_phi,
            lmax=self.config.lmax,
            new=True,
        )

        self.save_npz(
            output_path,
            name=f"lmax_{self.config.lmax}_sim_{sim:04d}",
            alm_phi=alm_phi,
        )

        print(f"[SAVE] Lensing potential alms, simulation {sim}: {output_path}")

        return alm_phi

    def lens_alm(
        self,
        cmb_alms: tuple[np.ndarray, np.ndarray, np.ndarray],
        alm_phi: np.ndarray,
        sim: int,
        overwrite: bool = False,
    ) -> np.ndarray:
        """
        Generate or load a lensed T, E and B alms.
        """
        output_path = self.paths.cmb_alms_file(
            spectrum="lensed",
            r=self.config.r,
        )

        output_path1 = output_path / f"lmax_{self.config.lmax}_sim_{sim:04d}.npz"
        if not self.paths.should_compute(output_path1, overwrite=overwrite):
            stored = self.load_npz(output_path1)

            print(f"[LOAD] lensed alms: {output_path}")

            return np.asarray([
                stored["alm_T"],
                stored["alm_E"],
                stored["alm_B"],
            ])

        alm_T, alm_E, alm_B = cmb_alms

        phi_lmax = hp.Alm.getlmax(len(alm_phi))

        if phi_lmax < 0:
            raise ValueError("Invalid alm_phi size.")

        ell = np.arange(phi_lmax + 1)

        # Deflection field:
        # d_LM = sqrt(L(L+1)) phi_LM
        deflection_filter = np.sqrt(ell * (ell + 1.0))

        dglm = hp.almxfl(
            alm_phi,
            deflection_filter,
        )

        # Lens the CMB alms using lenspyx
        T_len, Q_len, U_len = ls.alm2lenmap(
            [alm_T, alm_E, alm_B],
            dlms=[dglm],  # (gradient) ; curl omitted
            geometry=("healpix",{"nside": self.config.nside}),
            epsilon=1e-7,
            pol=True,
        )

        maps = np.asarray([
            T_len,
            Q_len,
            U_len,
        ])

        # Generate the lensed alms from the lensed maps
        alms = hp.map2alm(
            maps,
            lmax=self.config.lmax,
            pol=True,
        )

        self.save_npz(
            output_path,
            name=f"lmax_{self.config.lmax}_sim_{sim:04d}",
            alm_T=alms[0],
            alm_E=alms[1],
            alm_B=alms[2],
        )

        print(f"[SAVE] lensed alms: {output_path1}")

        return alms


    def simulate_one(
        self,
        sim: int,
        overwrite: bool = False,
    ) -> dict[str, Path]:
        """
        Generate one complete CMB realization.
        """

        path_cls = self.paths.cmb_cls_file(
                    r=self.config.r,
                )

        powers = self.compute_cls(
            names=[
                "unlensed_scalar",
                "lens_potential",
                "total"
            ],
            overwrite=overwrite,
        )

        path_alm_unl = self.paths.cmb_alms_file(
                    spectrum="unlensed",
                    r=self.config.r,
                )        

        cmb_alms = self.generate_unlensed_cmb_alms(
            cmb_cls=powers["unlensed_scalar"],
            sim=sim,
            overwrite=overwrite,
        )

        path_alm_phi = self.paths.cmb_alms_file(
                    spectrum="lens_potential",
                    r=self.config.r,
                )

        alm_phi = self.generate_phi_alm(
            lens_potential_cls=powers["lens_potential"],
            sim=sim,
            overwrite=overwrite,
        )

        path_alm_len = self.paths.cmb_alms_file(
            spectrum="lensed",
            r=self.config.r,
        )      

        self.lens_alm(
            cmb_alms=cmb_alms,
            alm_phi=alm_phi,
            sim=sim,
            overwrite=overwrite,
        )

        outputs = {
            "Cls": path_cls / f"lmax_{self.config.lmax}.npz",
            "alm_unl": path_alm_unl / f"lmax_{self.config.lmax}_sim_{sim:04d}.npz",
            "alm_phi": path_alm_phi / f"lmax_{self.config.lmax}_sim_{sim:04d}.npz",
            "alm_len": path_alm_len / f"lmax_{self.config.lmax}_sim_{sim:04d}.npz",
        }

        return outputs



