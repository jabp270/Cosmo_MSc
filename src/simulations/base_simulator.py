from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np


class BaseSimulator(ABC):
    """
    Base class for CMB, foreground and noise simulators.
    """
    def __init__(self, config, path_manager):
        self.config = config
        self.paths = path_manager

    @staticmethod
    def save_npz(
        output_dir: str | Path,
        name: str,
        **arrays: np.ndarray,
    ) -> Path:
        """
        Save named NumPy arrays into a compressed NPZ file.

        Parameters
        ----------
        output_dir
            Directory where the file will be saved.
        name
            Name of the NPZ file.
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not name.endswith(".npz"):
            name = f"{name}.npz"

        output_file = output_dir / name

        np.savez_compressed(
            output_file,
            **arrays,
        )

        return output_file

    @staticmethod
    def load_npz(input_path: str | Path) -> dict[str, np.ndarray]:
        """
        Load all arrays stored in an NPZ file.
        """
        input_path = Path(input_path)

        if not input_path.is_file():
            raise FileNotFoundError(f"File not found: {input_path}")

        with np.load(input_path, allow_pickle=False) as data:
            return {
                key: data[key]
                for key in data.files
            }

    def run_many(
        self,
        nsims: int,
        start_sim: int = 0,
        overwrite: bool = False,
        **kwargs: Any,
    ) -> list[dict[str, Path]]:
        """
        Run several independent realizations.
        """
        if nsims <= 0:
            raise ValueError("nsims must be greater than zero.")

        outputs = []

        for sim in range(start_sim, start_sim + nsims):

            print(f"> Running simulation {sim} of {start_sim + nsims - 1}...")

            simulation_paths = self.simulate_one(
                sim=sim,
                overwrite=overwrite,
                **kwargs,
            )

            outputs.append(simulation_paths)

        return outputs

    
    @abstractmethod
    def simulate_one(
        self,
        sim: int,
        overwrite: bool = False,
        **kwargs: Any,
    ) -> dict[str, Path]:
        """
        Generate one realization.

        Each child simulator must implement this method.
        """
        raise NotImplementedError

