from dataclasses import dataclass
from pathlib import Path

import healpy as hp
import numpy as np

from curvedsky import delens, norm_quad, rec_lens, utils as cs_utils

from src.simulations.config import LensingConfig
from src.core.paths import PathManager


class CmbLensing():

    def __init__(self, config):

        self.config = config.lensing
        self.paths = PathManager(config.base_dir)
        
    ESTIMATORS = ("TT", "TE", "EE", "TB", "EB", "BB")

    # ---------------------------------------------------------------
    # QE Reconstruction gradient + Curl
    # ---------------------------------------------------------------

    def compute_normalizations(self, FC, OC):
        """
        Compute the normalizations and MV weights via ``norm_quad.qall``.

        Parameter:
        -------

        - FC: Fiducial Cl
        - OC: Observed Cl

        Return
        -------
        list: (Ag, Ac, Wg, Wc) g/c: gradient and curl
        """
        

        cfg = self.config

        return norm_quad.qall("lens", list(cfg.QDO), cfg.lmax, cfg.rlmin, cfg.rlmax, FC, OC)

    def QE_reconstruct_one(
        self,
        FC: np.ndarray,
        OC: np.ndarray,
        alms_CI: list,
    ) -> dict[str, np.ndarray]:
        """
        Reconstruct the lensing-potential alm of one realization.

        Returns
        -------
        dict
            glm: lensing potential
            clm: curl lensing
            Ag: gradient normalization
            Ac: Curl normalization
        """

        cfg = self.config

        Ag, Ac, Wg, Wc = self.compute_normalizations(FC,OC)


        # Convert Healpy to Healpix the (lmax+1, lmax+1) ['l,m'] layout and truncate to rlmax.
        T = cs_utils.lm_healpy2healpix(alms_CI[0], lmax=cfg.lmax)
        E = cs_utils.lm_healpy2healpix(alms_CI[1], lmax=cfg.lmax)
        B = cs_utils.lm_healpy2healpix(alms_CI[2], lmax=cfg.lmax)

        glm = {}
        clm = {}
        for qi, q in enumerate(self.ESTIMATORS):

            if not cfg.QDO[qi]:
                continue
            if q == "TT":
                r = rec_lens.qtt(
                    cfg.lmax, cfg.rlmin, cfg.rlmax, FC[0],
                    T, T, nside_t=cfg.nside,
                )
            elif q == "TE":
                r = rec_lens.qte(
                    cfg.lmax, cfg.rlmin, cfg.rlmax, FC[3],
                    T, E, nside_t=cfg.nside,
                )
            elif q == "EE":
                r = rec_lens.qee(
                    cfg.lmax, cfg.rlmin, cfg.rlmax, FC[1],
                    E, E, nside_t=cfg.nside,
                )
            elif q == "TB":
                r = rec_lens.qtb(
                    cfg.lmax, cfg.rlmin, cfg.rlmax, FC[3],
                    T, B, nside_t=cfg.nside,
                )
            elif q == "EB":
                r = rec_lens.qeb(
                    cfg.lmax, cfg.rlmin, cfg.rlmax, FC[1],
                    E, B, nside_t=cfg.nside,
                )
            else:
                continue

            glm[q] = r[0] #gradient
            clm[q] = r[1] #curl

        # Normalize each estimator.
        for qi, q in enumerate(self.ESTIMATORS):
            if q in glm:
                glm[q] *= Ag[qi, :, None]
                clm[q] *= Ac[qi,:,None]

        # Minimum-variance combination.
        glm_mv = 0.
        clm_mv = 0.
        for qi, q in enumerate(self.ESTIMATORS):
            if q in glm:
                glm_mv += Wg[qi, :, None] * glm[q]
                clm_mv += Wc[qi, :, None] * clm[q]
        glm_mv *= Ag[5, :, None]
        clm_mv *= Ac[5, :, None]

        glm["MV"] = glm_mv
        clm["MV"] = clm_mv

        return {"glm": glm, "clm": clm, "Ag": Ag, "Ac": Ac}

    def save_reconstruction(
        self,
        rec: dict[str, np.ndarray],
        sim: int,
    ):
        """Save the lensing reconstruction"""

        cfg = self.config

        out_dir = self.paths.cmb_lensing_dir(
                    estimator= cfg.Folder_name,
                    create_dir= True,
                )
        
        pot_path = out_dir / f"potential_{sim}.npz"
        glm = rec["glm"]
        np.savez_compressed(
            pot_path,
            glmTT=glm.get("TT"),
            glmTE=glm.get("TE"),
            glmEE=glm.get("EE"),
            glmTB=glm.get("TB"),
            glmEB=glm.get("EB"),
            glmMV=glm.get("MV"),
        )

        curl_path = out_dir / f"curl_{sim}.npz"
        clm = rec["clm"]
        np.savez_compressed(
            curl_path,
            clmTT=clm.get("TT"),
            clmTE=clm.get("TE"),
            clmEE=clm.get("EE"),
            clmTB=clm.get("TB"),
            clmEB=clm.get("EB"),
            clmMV=clm.get("MV"),
        )

        pot_norm_path = out_dir / f"potential_norm_{sim}.npz"
        Ag = rec["Ag"] 
        np.savez_compressed(
            pot_norm_path,
            AgTT=Ag[0, :],
            AgTE=Ag[1, :],
            AgEE=Ag[2, :],
            AgTB=Ag[3, :],
            AgEB=Ag[4, :],
            AgMV=Ag[5, :],
        )

        curl_norm_path = out_dir / f"curl_norm_{sim}.npz"
        Ac = rec["Ac"] 
        np.savez_compressed(
            curl_norm_path,
            AcTT=Ac[0, :],
            AcTE=Ac[1, :],
            AcEE=Ac[2, :],
            AcTB=Ac[3, :],
            AcEB=Ac[4, :],
            AcMV=Ac[5, :],
        )

        return 

    # ---------------------------------------------------------------
    # Iterative Reconstruction gradient + Curl
    # ---------------------------------------------------------------

    # ---------------------------------------------------------------
    # Bias hardened QE
    # ---------------------------------------------------------------


    # ---------------------------------------------------------------
    # Delensing
    # ---------------------------------------------------------------

    def delens_one(
        self,
        almB:np.ndarray,
        almE: np.ndarray,
        phi_alm: np.ndarray,
        save: bool,
        sim: int,
    ) -> np.ndarray:
        """
        Ralm E y B en formato healpy

        se retornan en formato curvedsky
        """

        cfg = self.config

        almE = cs_utils.lm_healpy2healpix(almE, lmax=cfg.lmax)
        almB = cs_utils.lm_healpy2healpix(almB, lmax=cfg.lmax)

        # Wiener-filter E alm OMITIDO POR EL MOMENTO
        #w_e = self.wiener_e_alm(alms)

        # Wiener-filter phi alm OMITIDO POR EL MOMENTO
        #wplm = 1/(Cl + N^0)

        B_template = delens.lensingb(
            cfg.lmax,
            cfg.elmin,
            cfg.elmax,
            cfg.rlmin,
            cfg.rlmax,
            wElm= almE,
            wplm= phi_alm,
            nside_t=cfg.nside,
            gtype="p",
        )

        ## Delensing nivel armonico
        B_del = almB - B_template

        if save:
            cfg = self.config

            out_dir = self.paths.cmb_lensing_dir(
                        estimator= cfg.Folder_name,
                        create_dir= True,
                    )

            np.savez(
                out_dir/f"delensing_{sim}.npz",
                B_temp=B_template,
                B_del=B_del,
            )

        return B_template, B_del

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