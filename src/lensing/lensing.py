from dataclasses import dataclass
from pathlib import Path

import healpy as hp
import numpy as np

from curvedsky import delens, norm_quad, rec_lens, utils as cs_utils

from src.simulations.config import LensingConfig
from src.simulations.cmb_simulator import CmbSimulator
from src.core.paths import PathManager


class CmbLensing():

    def __init__(self, config):

        self.cfg = config
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
        normalize: bool = True,
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


        if not normalize:
            return {"glm": glm, "clm": clm, "Ag": Ag, "Ac": Ac}

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
    # Mean field (MF)
    # ---------------------------------------------------------------  


    def QE_mv_mean_field_corrected(
        self,
        rec_raw,
        mean_field,
    ):
        """
        Construye el estimador MV a partir de QE individuales
        sin normalizar y corregidos por su mean field.

        Parameters
        ----------
        rec_raw : dict
            Salida de QE_reconstruct_one(normalize=False).

        mean_field : dict
            Mean field sin normalizar por estimador:
            {"TT": alm, "TE": alm, ...}

        Returns
        -------
        np.ndarray
            Estimador gradiente MV corregido por mean field,
            en formato curvedsky [L, m].
        """

        Ag = rec_raw["Ag"]
        Wg = rec_raw["Wg"]
        raw_glm = rec_raw["glm"]

        lmax = self.config.lmax

        glm_mv = np.zeros((lmax + 1, lmax + 1),dtype=np.float64)

        for qi, q in enumerate(self.ESTIMATORS):

            if q not in raw_glm:
                continue

            # Sustraer mean field sin normalizar
            glm_corr = raw_glm[q] - mean_field[q]

            # Normalizar estimador individual
            glm_corr = glm_corr * Ag[qi, :, None]

            # 3. Aplicar peso MV de curvedsky
            glm_mv += Wg[qi, :, None] * glm_corr

        # 4. Normalización final MV
        glm_mv *= Ag[5, :, None]

        return glm_mv



# que reciba el Cl del cmb, la mascara, el numero de sim, y que con la semilla puede reproducir los mapas y hacer el QE a cada uno de forma recursiva. todos tienen que estar lenseados por el mismo potencial?? 
# o es que 
        
    def _mask_and_filter_cmb(
        self,
        alms,
        mask,
        CI,
        lmax,
        nside,
    ):
        """
        Aplica máscara a mapas T/Q/U y filtra los alms
        resultantes con CI_T, CI_E y CI_B.
        """

        alm_T, alm_E, alm_B = alms
        CI_T, CI_E, CI_B = CI

        mask = np.asarray(mask, dtype=np.float64)

        #Alms -> mapas T/Q/U
        maps_TQU = hp.alm2map(
            [alm_T, alm_E, alm_B],
            nside=nside,
            lmax=lmax,
            pol=True,
        )

        #Aplicar máscara
        masked_TQU = maps_TQU * mask[None, :]

        # Mapas enmascarados -> alms T/E/B
        alm_T_mask, alm_E_mask, alm_B_mask = hp.map2alm(
            masked_TQU,
            lmax=lmax,
            pol=True,
            iter=0,
        )

        # Aplicar filtros diagonales
        alm_CI = (
            hp.almxfl(alm_T_mask, CI_T),
            hp.almxfl(alm_E_mask, CI_E),
            hp.almxfl(alm_B_mask, CI_B),
        )

        return alm_CI


    def cmb_mean_field(
        self,
        cl,
        mask,
        lmax,
        nside,
        nsim,
        start_sim,
        normalize: bool = False,
    ):
        """
        Calcula el mean field para cada
        estimador cuadrático de lensing.

        Returns
        -------
        dict[str, np.ndarray]
            {
                "TT": alm_mean_TT,
                "TE": alm_mean_TE,
                "EE": alm_mean_EE,
                "TB": alm_mean_TB,
                "EB": alm_mean_EB,
            }

            Los alms están en formato curvedsky [L, m].
            Solo incluye estimadores habilitados en QDO.
        """

        mask = np.asarray(mask, dtype=np.float64)


        # Espectros CMB
        cl_unl = np.asarray(cl["unlensed_total"])
        cl_phi = np.asarray(cl["lens_potential"])
        cl_len = np.asarray(cl["total"])

        # self.cfg contiene el Config completo
        cmb = CmbSimulator(self.cfg)

        rlmin = self.config.rlmin
        rlmax = self.config.rlmax


        # Construir filtros CI
        ell = np.arange(lmax + 1)
        valid = (ell >= rlmin) & (ell <= rlmax)

        filters = []
        for idx in range(3):
            spectrum = cl_len[:lmax + 1, idx]
            CI = np.zeros(lmax + 1)
            CI[valid] = 1.0 / spectrum[valid]
            filters.append(CI)


        # Espectros fiduciales y observados
        FC = [
            cl_len[:lmax + 1, 0],
            cl_len[:lmax + 1, 1],
            cl_len[:lmax + 1, 2],
            cl_len[:lmax + 1, 3],
        ]

        OC = FC


        #Solo para el inicio de la suma
        mf_sum = None

        # Simulaciones Monte Carlo

        for sim in range(start_sim, start_sim + nsim):

            # CMB lenseado
            alm_T, alm_E, alm_B, alm_phi = cmb.simulate_one(
                cls=(cl_unl, cl_phi),
                sim=sim,
                same_phi=False,
            )

            # Enmascarar y filtrar
            alm_CI = self._mask_and_filter_cmb(
                alms=(alm_T, alm_E, alm_B),
                mask=mask,
                CI=filters,
                lmax=lmax,
                nside=nside,
            )

            # QE
            rec = self.QE_reconstruct_one(
                FC=FC,
                OC=OC,
                alms_CI=alm_CI,
                normalize=normalize,
            )

            glm = rec["glm"]

            # Inicia sola vez
            if mf_sum is None:
                mf_sum = {est: np.zeros_like(alm, dtype=np.complex128) for est, alm in glm.items()}

            # Acumular cada QE sin normalizar
            for est, alm in glm.items():

                mf_sum[est] += alm

            print(f"[Mean Field] {sim - start_sim + 1}/{nsim}")


        # Promedio Monte Carlo

        mean_field = {est: alm_sum / nsim for est, alm_sum in mf_sum.items()}

        print(f"\n[OK] Mean field calculado con {nsim} simulaciones")

        return mean_field




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