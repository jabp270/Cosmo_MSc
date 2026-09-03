"""
Wiener / C-inverse filter for cleaned CMB maps.

Two implementations are available:

- ``harmonic``: the simple per-multipole filter
  ``W_l = Cl_signal / (Cl_signal + Nl_residual)`` (and its inverse
  ``Cinv_l = 1 / (Cl_signal + Nl_residual)``) applied to the cleaned alm.
  This reproduces ``scripts/filters.py``.

- ``cninv``: the optimal (C-inverse / Wiener) multi-frequency filter in
  pixel space provided by cmblensplus (``curvedsky.cninv.cnfilter_freq``).

The cleaned maps are read from the BROOM product
``output_total/TEB_output_total_*.fits`` (T, Q, U maps) and converted to alm.
"""

from dataclasses import dataclass
from pathlib import Path

import healpy as hp
import numpy as np

from src.simulations.config import WienerConfig
from src.utils.broom_loader import load_clean_alms


class WienerFilter:
    """
    Turn a cleaned (BROOM) map into a Wiener- or C-inverse-filtered alm.
    """

    def __init__(self, config: WienerConfig):
        if config.method not in ("harmonic", "cninv"):
            raise ValueError(
                f"Unknown Wiener method: {config.method!r}"
            )
        self.config = config

    # ---------------------------------------------------------------
    # Harmonic filter
    # ---------------------------------------------------------------

    @staticmethod
    def compute_filters(
        signal_cl: np.ndarray,
        residual_nl: np.ndarray | None = None,
        lmin: int = 2,
    ) -> dict[str, np.ndarray]:
        """Return the Wiener ``W`` and C-inverse ``Cinv`` transfer functions."""
        signal_cl = np.asarray(signal_cl, dtype=float)
        noise = (
            np.zeros_like(signal_cl)
            if residual_nl is None
            else np.asarray(residual_nl, dtype=float)
        )
        denom = signal_cl + noise
        denom[:lmin] = 1.0
        denom[denom == 0.0] = 1e-30
        with np.errstate(divide="ignore", invalid="ignore"):
            w_fil = np.zeros_like(denom)
            w_fil[lmin:] = signal_cl[lmin:] / denom[lmin:]
            c_inv = np.zeros_like(denom)
            c_inv[lmin:] = 1.0 / denom[lmin:]
        return {"W": w_fil, "Cinv": c_inv}

    def harmonic_filters(self) -> dict[str, list[np.ndarray]]:
        """
        Build the Wiener / C-inverse transfer functions for T, E and B.

        The signal comes from ``signal_cl_keys`` stored in ``cl_signal``
        (shape ``(lmax+1, 4)`` with columns TT, EE, BB, TE).
        """
        if self.config.cl_signal is None:
            raise ValueError(
                "WienerConfig.cl_signal must be set for the harmonic method."
            )
        cls = np.asarray(self.config.cl_signal, dtype=float)
        col = {n: i for i, n in enumerate(("TT", "EE", "BB", "TE"))}
        key_col = {n: col[n] for n in self.config.signal_cl_keys}

        residual = None
        if self.config.residual_nl_path is not None:
            with np.load(self.config.residual_nl_path) as data:
                residual = np.asarray([
                    data[self.config.signal_cl_keys[i]]
                    for i in range(len(self.config.signal_cl_keys))
                ])

        filters = {"W": [], "Cinv": []}
        for i, key in enumerate(self.config.signal_cl_keys):
            sig = cls[:, key_col[key]]
            res = None if residual is None else residual[i]
            fil = self.compute_filters(
                sig, res, lmin=self.config.lmin
            )
            filters["W"].append(fil["W"])
            filters["Cinv"].append(fil["Cinv"])
        return filters

    def apply_harmonic(
        self,
        alms: tuple[np.ndarray, np.ndarray, np.ndarray],
        transfer: list[np.ndarray],
    ) -> list[np.ndarray]:
        """Apply a list of per-\u2113 transfer functions to (T, E, B) alm."""
        if len(alms) != len(transfer):
            raise ValueError("alms and transfer must have the same length")
        return [
            hp.almxfl(alm, t)
            for alm, t in zip(alms, transfer)
        ]

    # ---------------------------------------------------------------
    # cmblensplus cninv filter
    # ---------------------------------------------------------------

    def filter_cninv(
        self,
        maps: np.ndarray,
        method: str = "W",
    ) -> np.ndarray:
        """
        Run the cmblensplus optimal (C-inverse / Wiener) filter on pixel maps.

        Parameters
        ----------
        maps
            Beam-convolved T, Q, U maps with shape ``(n, mn, npix)`` where
            ``n`` is the number of signal fields (1=T, 2=Q,U, 3=T,Q,U) and
            ``mn`` the number of frequencies.
        method
            ``"W"`` for the Wiener filter, ``""`` for the C-inverse filter.

        Returns
        -------
        ndarray
            Filtered multipoles with shape ``(n, lmax+1, lmax+1)`` in the
            cmblensplus (``[l,m]``) layout.
        """
        try:
            from curvedsky import cninv
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "cmblensplus is required for the 'cninv' method."
            ) from exc

        cfg = self.config
        if cfg.beams is None or cfg.inv_noise_var is None:
            raise ValueError(
                "WienerConfig.beams and WienerConfig.inv_noise_var "
                "must be set for the cninv method."
            )

        n, mn = maps.shape[0], maps.shape[1]
        if cfg.inv_noise_var.shape[:2] != (n, mn):
            raise ValueError(
                "inv_noise_var must have shape (n, mn, npix)."
            )

        xlm = cninv.cnfilter_freq(
            n=n,
            mn=mn,
            nside=cfg.nside,
            lmax=cfg.lmax,
            cl=np.asarray(cfg.cl_signal, dtype=float),
            bl=np.asarray(cfg.beams, dtype=float),
            iNcov=np.asarray(cfg.inv_noise_var, dtype=float),
            maps=np.asarray(maps, dtype=float),
            itns=cfg.itns,
            eps=cfg.eps,
            filter=method,
            verbose=cfg.verbose,
        )
        return xlm

    # ---------------------------------------------------------------
    # Driver
    # ---------------------------------------------------------------

    def run_one(
        self,
        sim: int,
        method: str | None = None,
    ) -> dict[str, Path]:
        """
        Filter the cleaned map of one realization.

        Returns the paths of the saved Wiener (``WF``) and C-inverse (``CI``)
        alm.
        """
        cfg = self.config
        method = method or cfg.method

        out_dir = Path(cfg.out_dir or "outputs_filtered")
        out_dir.mkdir(parents=True, exist_ok=True)

        alms = load_clean_alms(
            files_dir=cfg.clean_maps_dir,
            sim=sim,
            nside=cfg.nside,
            lmax=cfg.lmax,
        )

        if method == "harmonic":
            filters = self.harmonic_filters()
            w_alms = self.apply_harmonic(alms, filters["W"])
            ci_alms = self.apply_harmonic(alms, filters["Cinv"])
            w_path = self._save_alms(out_dir, f"WF_{sim}", w_alms)
            ci_path = self._save_alms(out_dir, f"CI_{sim}", ci_alms)
            return {"W": w_path, "Cinv": ci_path}

        # cninv ----------------------------------------------------
        maps = hp.alm2map(
            np.array(alms), nside=cfg.nside, lmax=cfg.lmax, pol=True
        )  # (3, npix)
        maps = maps[None, :, :]  # (n=3, mn=1, npix)

        w_xlm = self.filter_cninv(maps, method="W")
        c_xlm = self.filter_cninv(maps, method="")
        name = f"WF_{sim}"
        w_path = out_dir / f"{name}.npz"
        np.savez_compressed(w_path, xlm=w_xlm)
        ci_path = out_dir / f"CI_{sim}.npz"
        np.savez_compressed(ci_path, xlm=c_xlm)
        return {"W": w_path, "Cinv": ci_path}

    @staticmethod
    def _save_alms(out_dir: Path, name: str, alms) -> Path:
        path = out_dir / f"{name}.npz"
        np.savez_compressed(
            path,
            almT=np.asarray(alms[0]),
            almE=np.asarray(alms[1]),
            almB=np.asarray(alms[2]),
        )
        return path

    def run_many(self, start_sim: int | None = None) -> list[dict[str, Path]]:
        """Filter every configured realization."""
        start = start_sim if start_sim is not None else self.config.start_sim
        outputs = []
        for sim in range(start, start + self.config.nsim):
            print(f"[WienerFilter] sim {sim} ({self.config.method})")
            outputs.append(self.run_one(sim))
        return outputs