import numpy as np
import healpy as hp

from pathlib import Path
from typing import Literal

from src.simulations.config import Config


class PathManager:
    """
    Manage paths for simulations, products, configurations and results.
    """

    def __init__(self, base_dir: str | Path, create: bool = True):

        self.base_dir = Path(base_dir).expanduser().resolve()

        self.configs_dir = self.base_dir / "configs" # Save configs for each run
        self.simulations_dir = self.base_dir / "simulations" # save cmb, foregrounds, noise, etc. simulations
        self.products_dir = self.base_dir / "products" # Save cleaned maps, lensing reconstruction, etc.
        self.results_dir = self.base_dir / "results" # Save results of analysis, plots, etc.

        self.root_dirs = {
            "configs": self.configs_dir,
            "simulations": self.simulations_dir,
            "products": self.products_dir,
            "results": self.results_dir,
        }

        if create:
            self.create_directories()

    def create_directories(self) -> None:
        for path in self.root_dirs.values():
            path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sim_tag(sim: int) -> str:
        if sim < 0:
            raise ValueError("sim must be non-negative.")
        return f"sim_{sim:04d}"

    @staticmethod
    def run_tag(run: int) -> str:
        if run < 0:
            raise ValueError("run must be non-negative.")
        return f"run_{run:03d}"

    @staticmethod
    def resolution_tag(nside: int, lmax: int) -> str:
        return f"nside_{nside}_lmax_{lmax}"

    @staticmethod
    def r_tag(r: float) -> str:
        return f"r_{r:.5f}"

    @staticmethod
    def frequency_tag(frequency_ghz: float) -> str:
        return f"freq_{frequency_ghz:06.1f}"

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """
        Ensure that the directory of the given path exists.
        """
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def exists(path: str | Path) -> bool:
        """
        Check if a file exists at the given path.
        """
        return Path(path).is_file()

    @staticmethod
    def should_compute(path: str | Path, overwrite: bool = False) -> bool:
        """
        Return True when a result must be computed.

        - If the file does not exist, compute it.
        - If overwrite=True, compute it again.
        - Otherwise, reuse the existing result.
        """
        path = Path(path)
        return overwrite or not path.is_file()

    #------------------------------------------------------
    #------------------------ CMB -------------------------
    #------------------------------------------------------

    def cmb_cls_file(
        self,
        r: float,
        create_dir: bool = True,
    ) -> Path:
        """
        Return the path for the CMB Cl files.

        Parameters
        ----------
        - r: The tensor-to-scalar ratio.
        - create_dir: Whether to create the directory if it doesn't exist.
        """
        output = (
            self.simulations_dir
            / "cmb"
            / "cls"
            / self.r_tag(r)
        )

        return self.ensure_directory(output) if create_dir else output

    def cmb_alms_file(
        self,
        spectrum: Literal[ "lensed", "unlensed", "lens_potential"],
        r: float,
        create_dir: bool = True,
    ) -> Path:
        """
        Return the path for the CMB alm files.

        Parameters
        ----------
        - spectrum: The type of CMB spectrum (lensed, unlensed, lens_potential).
        - r: The tensor-to-scalar ratio.
        - create_dir Whether to create the directory if it doesn't exist.
        """
        output = (
            self.simulations_dir
            / "cmb"
            / "alms"
            / self.r_tag(r)
            / spectrum
        )

        return self.ensure_directory(output) if create_dir else output
    
    #------------------------------------------------------
    #------------------ FOREGROUND ------------------------
    #------------------------------------------------------

    @staticmethod
    def model_tag(models: list[str]) -> str:
        if not models:
            raise ValueError(
                "At least one foreground model is required."
            )

        return "_".join(sorted(models))

    def foreground_alms_dir(
        self,
        model_tag: str,
        frequency_ghz: float,
        create_dir: bool = True,
    ) -> Path:
        """
        Return the path for foreground directory
        """
        output = (
            self.simulations_dir
            / "foregrounds"
            / model_tag
            / self.frequency_tag(frequency_ghz)
        )

        return (
            self.ensure_directory(output)
            if create_dir
            else output
        )

    #------------------------------------------------------
    #---------------------- NOISE -------------------------
    #------------------------------------------------------
    
    def noise_alms_dir(
        self,
        experiment: str,
        frequency_ghz: float,
        noise_model: str = "white",
        create_dir: bool = True,
    ) -> Path:
        """
        Return the path for noise alm directory
        """
        output = (
            self.simulations_dir
            / "noise"
            / experiment
            / noise_model
            / "alms"
            / self.frequency_tag(frequency_ghz)
        )

        return (
            self.ensure_directory(output)
            if create_dir
            else output
        )

    def noise_cls_dir(
        self,
        experiment: str,
        noise_model: str = "white",
        create_dir: bool = True,
    ) -> Path:
        """
        Return the path for noise cls directory
        """
        output = (
            self.simulations_dir
            / "noise"
            / experiment
            / noise_model
            / "cls"
        )

        return (
            self.ensure_directory(output)
            if create_dir
            else output
        )

    #------------------------------------------------------
    #---------------- COMPONENT SEPARATION ----------------
    #------------------------------------------------------

    def component_separation_dir(
        self,
        create_dir: bool = True,
    ) -> Path:
        """
        Return the path for Component separation method.
        """
        output = (
            self.products_dir
            / "component_separation"
        )

        return (
            self.ensure_directory(output)
            if create_dir
            else output
        )

    @staticmethod
    def path_output_cs(
        files_dir: Path | None,
        name: Literal["output_cmb", "fgds_residuals", "noise_residuals", "output_total", "weights"],
        sim: int,
        lmax: int,
        nside: int,
        beam_out: float,
    ) -> Path:
        """
        Return the path after component separation

        - name: take this values ["output_cmb", "fgds_residuals", "noise_residuals", "output_total", "weights"]
        """

        if name == "output_cmb":
            path = files_dir / f"{name}" / f"TEB_output_cmb_{beam_out}acm_ns{nside}_lmax{lmax}_{sim:05d}.fits"

        elif name == "fgds_residuals":
            path = files_dir / f"{name}" / f"TEB_fgds_residuals_{beam_out}acm_ns{nside}_lmax{lmax}_{sim:05d}.fits"

        elif name == "noise_residuals":

            path = files_dir / f"{name}" / f"TEB_noise_residuals_{beam_out}acm_ns{nside}_lmax{lmax}_{sim:05d}.fits"   

        elif name == "output_total":

            path = files_dir / f"{name}" / f"TEB_output_total_{beam_out}acm_ns{nside}_lmax{lmax}_{sim:05d}.fits" 

        elif name == "weights":

            path = files_dir / f"{name}" / f"{sim:05d}" / f"weights_B_{beam_out}acm_ns{nside}_lmax{lmax}_{sim:05d}.npy"

        return path 



    


# Global Instance
# path = PathManager(Config.base_dir)