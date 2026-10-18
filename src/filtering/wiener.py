from dataclasses import dataclass
from pathlib import Path

import healpy as hp
import numpy as np

from src.simulations.config import WienerConfig



class WienerFilter:

    def __init__(self, config: WienerConfig):

        self.config = config

    # ---------------------------------------------------------------
    # Harmonic filter
    # ---------------------------------------------------------------

    @staticmethod
    def harmonic_filters(
        signal_cl: np.ndarray,
        residual_nl: np.ndarray,
        lmin: int = 2,
    ) -> dict[str, np.ndarray]:
        """Return the Wiener ``W`` and C-inverse ``Cinv`` transfer functions."""

        denom = signal_cl + residual_nl
        denom[:lmin] = 1.0

        w_fil = np.zeros_like(denom)
        w_fil[lmin:] = signal_cl[lmin:] / denom[lmin:]
        c_inv = np.zeros_like(denom)
        c_inv[lmin:] = 1.0 / denom[lmin:]

        return {"WF": w_fil, "Cinv": c_inv}

    @staticmethod
    def apply_harmonic(
        alms: tuple[np.ndarray, np.ndarray, np.ndarray],
        transfer: list[np.ndarray],
    ) -> list[np.ndarray]:
        
        return [hp.almxfl(alm, t) for alm, t in zip(alms, transfer)]

    # ---------------------------------------------------------------
    # Space filter (wiener filter equation)
    # ---------------------------------------------------------------