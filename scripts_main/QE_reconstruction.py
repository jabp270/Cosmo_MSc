from pathlib import Path
from curvedsky import utils as cs_utils

import numpy as np
import healpy as hp

from src.core.paths import PathManager
from src.filtering.wiener import WienerFilter
from src.lensing.lensing import CmbLensing
from src.simulations.cmb_simulator import CmbSimulator
from src.simulations.noise_simulator import NoiseSimulator
from src.pipeline.simulation_pipelines import pipeline_simulation

from src.simulations.config import (
    Config,
    CmbConfig,
    ForegroundConfig,
    NoiseConfig,
    CleaningConfig,
    InstrumentConfig,
    LensingConfig,
)

# Prueba que funciona el estimador cuadratico para señal de solo CMB
def test_0() -> None:

    sim = 1

    nside = 2048
    lmax = 3000

    rlmin = 100
    rlmax = 3000

    cmb_settings = CmbConfig(
        nside=nside,
        lmax=lmax,
        r=0.0,
        nsim=1,
        start_sim=sim,
    )

    lensing_settings = LensingConfig(
        nside=nside,
        lmax=lmax,
        rlmin=rlmin,
        rlmax=rlmax,
        elmin=rlmin,
        elmax=rlmax,
        QDO=(True, True, True, True, True, False),
        nsim=1,
        start_sim=sim,
        fwhm_out=0.0,
        Folder_name="TEST_CMB_ONLY",
    )

    config = Config(
        base_dir="outputs_main",
        cmb=cmb_settings,
        lensing=lensing_settings,
    )

    cmb = CmbSimulator(config)
    lensing = CmbLensing(config)

    #Cargar spectros
    powers = cmb.compute_cls(names=["unlensed_total", "lens_potential", "total"], overwrite=False)

    cl_len = powers["total"]

    cl_unl = powers["unlensed_total"]

    cl_phi = powers["lens_potential"]

    #hacer simulaciones
    alm_T, alm_E, alm_B, alm_phi = cmb.simulate_one(cls=(cl_unl, cl_phi), sim=sim)

    alm_obs = (alm_T, alm_E, alm_B)

    print("[OK] Lensed CMB generated")

    # Filtro CI
    ell = np.arange(lmax + 1)

    CI_T = np.zeros(lmax + 1)
    CI_E = np.zeros(lmax + 1)
    CI_B = np.zeros(lmax + 1)

    valid = (ell >= rlmin) & (ell <= rlmax)

    for CI, cl in zip([CI_T, CI_E, CI_B], [cl_len[:, 0], cl_len[:, 1], cl_len[:, 2]]):

        mask = valid & (cl > 0)
        CI[mask] = 1.0 / cl[mask]

    alm_CI = (
        hp.almxfl(alm_T, CI_T),
        hp.almxfl(alm_E, CI_E),
        hp.almxfl(alm_B, CI_B),
    )

    print("[OK] Harmonic filtering completed")

    # QUADRATIC ESTIMATOR
    # FC: Fiducial CMB spectra
    # OC: Observed CMB spectra

    FC = [cl_len[:, 0],cl_len[:, 1],cl_len[:, 2],cl_len[:, 3]]

    OC = [cl_len[:, 0],cl_len[:, 1],cl_len[:, 2],cl_len[:, 3]]

    reconstruction = lensing.QE_reconstruct_one(FC=FC,OC=OC,alms_CI=alm_CI)

    lensing.save_reconstruction(rec=reconstruction, sim=sim)

    alm_phi_rec = reconstruction["glm"]["MV"]

    print("[OK] Lensing reconstruction completed")

# if __name__ == "__main__":
#     test_0()



# Segunda prueba: CMB + ruido blanco de 93 GHz
def test_1() -> None:

    sim = 1
    frequency_ghz = 93

    nside = 2048
    lmax = 3000

    rlmin = 100
    rlmax = 3000

    cmb_settings = CmbConfig(
        nside=nside,
        lmax=lmax,
        r=0.0,
        nsim=1,
        start_sim=sim,
    )

    noise_settings = NoiseConfig(
        model="white",
        experiment="SO_LAT",
        freq=[frequency_ghz],
        noise_t=[8.0],
        noise_p=[8.0 * np.sqrt(2)],
        nside=nside,
        lmax=lmax,
        nsim=1,
        noise_seed=12345,
    )

    lensing_settings = LensingConfig(
        nside=nside,
        lmax=lmax,
        rlmin=rlmin,
        rlmax=rlmax,
        elmin=rlmin,
        elmax=rlmax,
        QDO=(True, True, True, True, True, False),
        nsim=1,
        start_sim=sim,
        fwhm_out=0.0,
        Folder_name="TEST_CMB_NOISE_93",
    )

    config = Config(
        base_dir="outputs_main",
        cmb=cmb_settings,
        noise=noise_settings,
        lensing=lensing_settings,
    )

    cmb = CmbSimulator(config)
    noise = NoiseSimulator(config)
    lensing = CmbLensing(config)

    powers = cmb.compute_cls(names=["unlensed_total", "lens_potential", "total"],overwrite=False)

    cl_unl = powers["unlensed_total"]
    cl_len = powers["total"]
    cl_phi = powers["lens_potential"]

    alm_T, alm_E, alm_B, alm_phi = cmb.simulate_one(cls=(cl_unl, cl_phi),sim=sim)

    print("[OK] Lensed CMB generated")


    noise_T, noise_E, noise_B = noise.simulate_one(sim=sim,frequency_ghz=frequency_ghz)

    print("[OK] White noise generated")


    # OBSERVED ALMS: CMB + NOISE
    alm_obs_T = alm_T + noise_T
    alm_obs_E = alm_E + noise_E
    alm_obs_B = alm_B + noise_B

    del noise_T, noise_E, noise_B
    del alm_T, alm_E, alm_B

    print("[OK] Observed alms generated")

    #noise spectra
    nl = noise.white_noise_cls(noise_t=8.0,noise_p=8.0 * np.sqrt(2))

    # Total covariance: lensed CMB + noise
    cl_obs = cl_len.copy()

    cl_obs[:, 0] += nl["TT"]
    cl_obs[:, 1] += nl["EE"]
    cl_obs[:, 2] += nl["BB"]

    ell = np.arange(lmax + 1)

    CI_T = np.zeros(lmax + 1)
    CI_E = np.zeros(lmax + 1)
    CI_B = np.zeros(lmax + 1)

    valid = (ell >= rlmin) & (ell <= rlmax)

    for CI, cl in zip([CI_T, CI_E, CI_B],[cl_obs[:, 0],cl_obs[:, 1],cl_obs[:, 2]]):

        mask = valid & (cl > 0)
        CI[mask] = 1.0 / cl[mask]

    alm_CI = (
        hp.almxfl(alm_obs_T, CI_T),
        hp.almxfl(alm_obs_E, CI_E),
        hp.almxfl(alm_obs_B, CI_B),
    )

    print("[OK] Harmonic filtering completed")


    # FC: Theoretical response spectra
    FC = [cl_len[:, 0], cl_len[:, 1], cl_len[:, 2], cl_len[:, 3]]

    # OC: Lensed CMB + instrumental noise
    OC = [cl_obs[:, 0], cl_obs[:, 1], cl_obs[:, 2], cl_obs[:, 3]]

    reconstruction = lensing.QE_reconstruct_one(FC=FC,OC=OC,alms_CI=alm_CI)

    print("[OK] Lensing reconstruction completed")

    lensing.save_reconstruction(rec=reconstruction,sim=sim)

if __name__ == "__main__":
    test_1()


############################################################################
# SERIA BUENO PROBAR UN TEST CON SOLO CMB + FOREGROUND EL MAS DEBIL 
# SOLO PARA COMPARAR SALIDAS DEL QE
############################################################################



##########################################
# --------------- MAIN ------------------
##########################################


# /home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs_main/products/Comp_sep broom simulations/ilc_pixel_bias0.0/cmb_reconstruction

# /home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs_main/products/Comp_sep broom simulations/ilc_needlet_bias0.001/cosine_0_30_60_100_180_300_500_800_1200_1800_2400_3000/cmb_reconstruction

# Path after component separation 
maps_cs_dir = Path("/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs_main/products/Comp_sep broom simulations/ilc_pixel_bias0.0/cmb_reconstruction")

# Path fiducial Cl's
fid_cl_dir = Path("outputs_main/simulations/cmb/cls/r_0.00000/lmax_3000.npz")

def main() -> None:

    lensing_settings = LensingConfig(
        nside=2048,
        lmax=3000,
        rlmin=100,
        rlmax=3000,
        elmin=100,
        elmax=3000,
        QDO=(True, True, True, True, True, False),
        nsim=1,
        start_sim=0,

        fwhm_out = 7.4,
        Folder_name="FULL_ILC_reconstruction"
    )

    config = Config(
        base_dir="outputs_main",
        lensing=lensing_settings
    )

    # -------------- PATHS -----------------
    paths = PathManager(config.base_dir)

    # instancia de wiener filter
    filter = WienerFilter(config.wiener)

    # Instancia de CmbLensing
    lensing = CmbLensing(config)

    # fiducial spectra.
    cl_fid = np.load(fid_cl_dir)["total"] #(ells, 4)

    def load_cs_maps(name, sim):
        path = paths.path_output_cs(
            files_dir=maps_cs_dir, name=name,
            sim=sim, lmax=config.lensing.lmax, nside=config.lensing.nside, beam_out=config.lensing.fwhm_out)
        m = hp.read_map(path, field=(0,1,2))  # (3, npix) TEB maps
        return m    

    Cl_BB_del_all = []
    Cl_BB_before_all = []
    Cl_BB_temp_all = []

    for sim in range(lensing_settings.start_sim, lensing_settings.start_sim + lensing_settings.nsim):
    # -------------- PATHS -----------------

        maps_clean = load_cs_maps(name="output_total", sim=sim) # TEB maps

        # Observed Cls
        Cl_obs = hp.anafast(maps_clean, maps_clean, nspec=4, lmax=config.lensing.lmax, pol=False) #(4,)


        # Noise spectra (Here we can include a effective noise spectra)
        nl_signal = None 

        # Instancia de Wieneer filter
        #filter = filter.harmonic_filters()

        #######################################################
        # ESTO ES TEMPORAL HASTA SABER BIEN QUE PONER EN RESIDUAL_NL #####
        # Crear los filtros vacíos
        CI_T = np.zeros(lensing_settings.lmax + 1)
        CI_E = np.zeros(lensing_settings.lmax + 1)
        CI_B = np.zeros(lensing_settings.lmax + 1)

        # Rango de multipolos que usaremos
        for ell in range(lensing_settings.rlmin, lensing_settings.rlmax + 1):

            CI_T[ell] = 1.0 / cl_fid[ell, 0]   # TT
            CI_E[ell] = 1.0 / cl_fid[ell, 1]   # EE
            CI_B[ell] = 1.0 / cl_fid[ell, 2]   # BB

        # Juntar los tres filtros
        CI_filt = [CI_T, CI_E, CI_B]

        ########################################################

        # Cinverse filter
        # CI_filt = filter.harmonic_filters(signal_cl= cl_fid, residual_nl=nl_signal)["Cinv"]

        alm_obs = hp.map2alm(maps_clean, lmax=config.lensing.rlmax, pol=False) #(3, Npix)

        del maps_clean

        alm_CI = filter.apply_harmonic(alms=alm_obs, transfer=CI_filt)

        reconstruction = lensing.QE_reconstruct_one(FC=[cl_fid[:,0], cl_fid[:,1], cl_fid[:,2], cl_fid[:,3]], OC=[cl_fid[:,0], cl_fid[:,1], cl_fid[:,2], cl_fid[:,3]], alms_CI=alm_CI) #Cl_obs

        lensing.save_reconstruction(rec=reconstruction, sim=sim)

        B_temp, B_del = lensing.delens_one(almB=alm_obs[2], almE=alm_obs[1], phi_alm=reconstruction["glm"].get("MV"), save=True, sim=sim)

    #     # ============================================================
    #     # POWER SPECTRA BEFORE / TEMPLATE / AFTER DELENSING
    #     # ============================================================

    #     # B_template y B_del están en formato curvedsky [l,m]
    #     Cl_BB_temp = cs_utils.alm2cl(B_temp)

    #     Cl_BB_del = cs_utils.alm2cl(B_del)

    #     # alm_obs[2] está en formato Healpy
    #     Cl_BB_before = hp.alm2cl(alm_obs[2],lmax=lensing_settings.lmax,)

    #     # Guardar para promediar sobre simulaciones
    #     Cl_BB_temp_all.append(Cl_BB_temp)

    #     Cl_BB_del_all.append(Cl_BB_del)

    #     Cl_BB_before_all.append(Cl_BB_before)

    # # ============================================================
    # # AVERAGE OVER SIMULATIONS
    # # ============================================================

    # Cl_BB_temp_all = np.asarray(
    #     Cl_BB_temp_all
    # )

    # Cl_BB_del_all = np.asarray(
    #     Cl_BB_del_all
    # )

    # Cl_BB_before_all = np.asarray(
    #     Cl_BB_before_all
    # )

    # mean_Cl_BB_temp = np.mean(
    #     Cl_BB_temp_all,
    #     axis=0,
    # )

    # mean_Cl_BB_del = np.mean(
    #     Cl_BB_del_all,
    #     axis=0,
    # )

    # mean_Cl_BB_before = np.mean(
    #     Cl_BB_before_all,
    #     axis=0,
    # )

    # # ============================================================
    # # FIDUCIAL BB WITH THE SAME COMMON BEAM
    # # ============================================================

    # ell = np.arange(
    #     lensing_settings.lmax + 1
    # )

    # fwhm_rad = np.deg2rad(
    #     lensing_settings.fwhm_out / 60.0
    # )

    # beam = hp.gauss_beam(
    #     fwhm=fwhm_rad,
    #     lmax=lensing_settings.lmax,
    #     pol=True,
    # )

    # beam_B = beam[:, 2]

    # Cl_BB_fid = cl_fid[:, 2]

    # Cl_BB_fid_beam = (
    #     beam_B**2 * Cl_BB_fid
    # )

    # # ============================================================
    # # DELENSING EFFICIENCY
    # # ============================================================

    # epsilon_fid = np.full(
    #     lensing_settings.lmax + 1,
    #     np.nan,
    # )

    # epsilon_before = np.full(
    #     lensing_settings.lmax + 1,
    #     np.nan,
    # )


    # valid_fid = (
    #     (ell >= lensing_settings.elmin)
    #     & (ell <= lensing_settings.elmax)
    #     & (Cl_BB_fid_beam > 0.0)
    # )

    # epsilon_fid[valid_fid] = (
    #     1.0
    #     - mean_Cl_BB_del[valid_fid]
    #     / Cl_BB_fid_beam[valid_fid]
    # )

    # valid_before = (
    #     (ell >= lensing_settings.elmin)
    #     & (ell <= lensing_settings.elmax)
    #     & (mean_Cl_BB_before > 0.0)
    # )

    # epsilon_before[valid_before] = (
    #     1.0
    #     - mean_Cl_BB_del[valid_before]
    #     / mean_Cl_BB_before[valid_before]
    # )

    # output_dir = (
    #     Path(config.base_dir)
    #     / "products"
    #     / "delensing"
    #     / lensing_settings.Folder_name
    # )

    # output_dir.mkdir(
    #     parents=True,
    #     exist_ok=True,
    # )

    # output_file = (
    #     output_dir
    #     / "delensing_efficiency.npz"
    # )

    # np.savez(
    #     output_file,
    #     ell=ell,

    #     Cl_BB_fid=Cl_BB_fid,
    #     Cl_BB_fid_beam=Cl_BB_fid_beam,

    #     Cl_BB_before=mean_Cl_BB_before,
    #     Cl_BB_template=mean_Cl_BB_temp,
    #     Cl_BB_del=mean_Cl_BB_del,

    #     epsilon_fid=epsilon_fid,
    #     epsilon_before=epsilon_before,
    # )

    # print(
    #     f"[SAVE] Delensing efficiency: "
    #     f"{output_file}"
    # )

# if __name__ == "__main__":
#     main()