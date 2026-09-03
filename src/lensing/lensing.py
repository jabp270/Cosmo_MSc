"""
CMB lensing reconstruction and delensing using cmblensplus (``curvedsky``).

Reconstruction reproduces ``scripts/rec_lensing_full.py``:
the cleaned (BROOM) alm are C-inverse filtered, the quadratic estimators
(quadratic estimators combination, or QDO) are evaluated, normalized and
combined into a minimum-variance (MV) lensing-potential alm.

Delensing reproduces ``scripts/Delensing_full.py`` via
``curvedsky.delens.lensingb``: the lensing B-mode is estimated from the
reconstructed potential and the Wiener-filtered E alm.
"""

from dataclasses import dataclass
from pathlib import Path

import healpy as hp
import numpy as np

from src.simulations.config import LensingConfig
from src.utils.broom_loader import load_clean_alms


class CmbLensing:
    """
    Reconstruct the CMB lensing potential from the cleaned alm and
    optionally delens the observed B mode.
    """

    # Order of the quadratic estimators (matches ``QDO`` indexing).
    ESTIMATORS = ("TT", "TE", "EE", "TB", "EB")

    def __init__(self, config: LensingConfig):
        self.config = config

    # ---------------------------------------------------------------
    # C-inverse prefiltering
    # ---------------------------------------------------------------

    def ci_filter(self, cl_signal: np.ndarray, residual_nl: np.ndarray | None):
        """
        Build the C-inverse transfer functions for T, E and B.

        Returns ``Cinv = 1 / (Cl_signal + Nl_residual)`` per field.
        """
        cls = np.asarray(cl_signal, dtype=float)
        if residual_nl is None:
            residual_nl = np.zeros_like(cls)

        cols = {"TT": 0, "EE": 1, "BB": 2}
        keys = ("TT", "EE", "BB")
        ci = []
        for key in keys:
            denom = cls[:, cols[key]] + residual_nl[key]
            denom[: self.config.rlmin] = 1.0
            denom[denom == 0.0] = 1e-30
            transfer = np.zeros_like(denom)
            transfer[self.config.rlmin:] = 1.0 / denom[self.config.rlmin:]
            ci.append(transfer)
        return ci

    # ---------------------------------------------------------------
    # Reconstruction
    # ---------------------------------------------------------------

    def _reconstruction_cls(self) -> tuple[list[np.ndarray], list[np.ndarray]]:
        """Return (FC, OC) signal spectra as lists [TT, EE, BB, TE]."""
        if self.config.cl_signal is None:
            raise ValueError(
                "LensingConfig.cl_signal is required."
            )
        cls = np.asarray(self.config.cl_signal, dtype=float)
        if cls.shape[1] != 4:
            raise ValueError(
                "cl_signal must have shape (lmax+1, 4) "
                "with columns TT, EE, BB, TE."
            )
        fc = [cls[:, 0], cls[:, 1], cls[:, 2], cls[:, 3]]
        rl = self.config.rlmax + 1
        return [c[:rl] for c in fc], [c[:rl] for c in fc]

    def compute_normalizations(self):
        """
        Compute the normalizations and MV weights via ``norm_quad.qall``.
        """
        from curvedsky import norm_quad

        cfg = self.config
        fc, oc = self._reconstruction_cls()
        return norm_quad.qall(
            "lens",
            list(cfg.QDO),
            cfg.lmax,
            cfg.rlmin,
            cfg.rlmax,
            fc,
            oc,
        )

    def reconstruct_one(
        self,
        sim: int,
    ) -> dict[str, np.ndarray]:
        """
        Reconstruct the lensing-potential alm of one realization.

        Returns
        -------
        dict
            ``glm`` : per-estimator and MV gradient-potential alm in the
            cmblensplus ``[l,m]`` layout; ``ag`` : the normalizations.
        """
        from curvedsky import rec_lens, utils as cs_utils

        cfg = self.config

        from curvedsky import norm_quad

        ag, ac, wg, wc = self.compute_normalizations()

        fc, _ = self._reconstruction_cls()

        # 1) C-inverse filter the cleaned alm.
        alms = load_clean_alms(
            cfg.clean_maps_dir, sim, nside=cfg.nside, lmax=cfg.lmax
        )
        ci = self.ci_filter(np.asarray(cfg.cl_signal, dtype=float), cfg.residual_nl)
        filtered = [hp.almxfl(alm, t) for alm, t in zip(alms, ci)]

        # 2) Convert to the (lmax+1, lmax+1) ['l,m'] layout and truncate to rlmax.
        sl = cfg.rlmax + 1
        T = cs_utils.lm_healpy2healpix(filtered[0], lmax=cfg.lmax)[:sl, :sl]
        E = cs_utils.lm_healpy2healpix(filtered[1], lmax=cfg.lmax)[:sl, :sl]
        B = cs_utils.lm_healpy2healpix(filtered[2], lmax=cfg.lmax)[:sl, :sl]

        glm = {}
        for qi, q in enumerate(self.ESTIMATORS):
            if not cfg.QDO[qi]:
                continue
            if q == "TT":
                r = rec_lens.qtt(
                    cfg.lmax, cfg.rlmin, cfg.rlmax, fc[0],
                    T, T, nside_t=cfg.nside,
                )
            elif q == "TE":
                r = rec_lens.qte(
                    cfg.lmax, cfg.rlmin, cfg.rlmax, fc[3],
                    T, E, nside_t=cfg.nside,
                )
            elif q == "EE":
                r = rec_lens.qee(
                    cfg.lmax, cfg.rlmin, cfg.rlmax, fc[1],
                    E, E, nside_t=cfg.nside,
                )
            elif q == "TB":
                r = rec_lens.qtb(
                    cfg.lmax, cfg.rlmin, cfg.rlmax, fc[3],
                    T, B, nside_t=cfg.nside,
                )
            elif q == "EB":
                r = rec_lens.qeb(
                    cfg.lmax, cfg.rlmin, cfg.rlmax, fc[1],
                    E, B, nside_t=cfg.nside,
                )
            else:
                continue
            glm[q] = r[0]

        # 3) Normalize each estimator.
        for qi, q in enumerate(self.ESTIMATORS):
            if q in glm:
                glm[q] *= ag[qi, :, None]

        # 4) Minimum-variance combination.
        glm_mv = 0.0
        for qi, q in enumerate(self.ESTIMATORS):
            if q in glm:
                glm_mv += wg[qi, :, None] * glm[q]
        glm_mv *= ag[5, :, None]

        glm["MV"] = glm_mv

        return {"glm": glm, "ag": ag}

    def save_reconstruction(
        self,
        rec: dict[str, np.ndarray],
        sim: int,
    ) -> dict[str, Path]:
        """Save the reconstructed potential and normalizations of one sim."""
        out_dir = Path(self.config.out_dir or "outputs_rec")
        out_dir.mkdir(parents=True, exist_ok=True)

        glm, ag = rec["glm"], rec["ag"]

        pot_path = out_dir / f"rec_pot_{sim}.npz"
        np.savez_compressed(
            pot_path,
            glmTT=glm.get("TT"),
            glmTE=glm.get("TE"),
            glmEE=glm.get("EE"),
            glmTB=glm.get("TB"),
            glmEB=glm.get("EB"),
            glmMV=glm.get("MV"),
        )

        norm_path = out_dir / f"rec_norm_{sim}.npz"
        np.savez_compressed(
            norm_path,
            agTT=ag[0, :],
            agEE=ag[1, :],
            agEB=ag[2, :],
            agTB=ag[3, :],
            agTE=ag[4, :],
            agMV=ag[5, :],
        )

        return {"pot": pot_path, "norm": norm_path}

    # ---------------------------------------------------------------
    # Delensing
    # ---------------------------------------------------------------

    def wiener_e_alm(
        self,
        alms: tuple[np.ndarray, np.ndarray, np.ndarray],
    ) -> np.ndarray:
        """
        Build the Wiener-filtered E alm used for the delensing convolution.

        Heuristic Wiener filter ``W_l = Cl_EE / (Cl_EE + Nl_EE)`` on the
        cleaned E alm, returned in the cmblensplus ``[l,m]`` layout.
        """
        from curvedsky import utils as cs_utils

        cfg = self.config
        cls = np.asarray(cfg.cl_signal, dtype=float)
        cl_ee = cls[:, 1]
        n_ee = (
            np.zeros(self.config.lmax + 1)
            if cfg.residual_nl is None
            else np.asarray(cfg.residual_nl["EE"])
        )
        w = np.zeros(self.config.lmax + 1)
        denom = cl_ee + n_ee
        en = np.arange(self.config.lmax + 1)
        w[en >= self.config.elmin] = (
            cl_ee[en >= self.config.elmin] / denom[en >= self.config.elmin]
        )
        e_wiener = hp.almxfl(alms[1], w)
        return cs_utils.lm_healpy2healpix(e_wiener, lmax=cfg.lmax)

    def delens_one(
        self,
        sim: int,
        phi_alm: np.ndarray | None = None,
    ) -> dict[str, np.ndarray]:
        """
        Estimate the lensing B-mode from the E alm and a lensing potential.

        Returns the lensing-B alm (``lb``) and, if a ``phi_alm`` is given,
        the delensed B alm (``b_delensed``) computed as ``B_obs - lb``.
        """
        from curvedsky import delens, utils as cs_utils

        cfg = self.config

        alms = load_clean_alms(
            cfg.clean_maps_dir, sim, nside=cfg.nside, lmax=cfg.lmax
        )

        # Wiener-filtered E alm (cmblensplus layout).
        w_e = self.wiener_e_alm(alms)

        phi = cfg.phi_alm if phi_alm is None else phi_alm
        if phi is None:
            raise ValueError(
                "A lensing potential is required for delensing "
                "(set LensingConfig.phi_alm)."
            )
        phi_hp = cs_utils.lm_healpy2healpix(phi, lmax=cfg.lmax)

        lb = delens.lensingb(
            cfg.lmax,
            cfg.elmin,
            cfg.elmax,
            cfg.rlmin,
            cfg.rlmax,
            w_e[: cfg.elmax + 1, : cfg.elmax + 1],
            phi_hp[: cfg.rlmax + 1, : cfg.rlmax + 1],
            nside_t=cfg.nside,
            gtype="p",
        )

        # Observed B alm in the (lmax+1, lmax+1) layout.
        b_obs = cs_utils.lm_healpy2healpix(alms[2], lmax=cfg.lmax)

        return {
            "lb": lb,
            "b_delensed": b_obs - lb,
        }

    def save_delensed(
        self,
        result: dict[str, np.ndarray],
        sim: int,
    ) -> Path:
        out_dir = Path(self.config.out_dir or "outputs_rec")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"delens_{sim}.npz"
        np.savez_compressed(
            path,
            lb=result["lb"],
            b_delensed=result["b_delensed"],
        )
        return path

    # ---------------------------------------------------------------
    # Driver
    # ---------------------------------------------------------------

    def run_one(
        self,
        sim: int,
    ) -> dict[str, Path]:
        """Reconstruct (and optionally delens) one realization."""
        outputs = self.save_reconstruction(self.reconstruct_one(sim), sim)

        if self.config.delens:
            rec = self.reconstruct_one(sim)["glm"]["MV"]
            phi = self.config.phi_alm if self.config.phi_alm is not None else rec
            result = self.delens_one(sim, phi_alm=phi)
            outputs["delens"] = self.save_delensed(result, sim)

        return outputs

    def run_many(
        self,
        start_sim: int | None = None,
    ) -> list[dict[str, Path]]:
        """Reconstruct every configured realization."""
        start = start_sim if start_sim is not None else self.config.start_sim
        outputs = []
        for sim in range(start, start + self.config.nsim):
            print(f"[CmbLensing] sim {sim}")
            outputs.append(self.run_one(sim))
        return outputs