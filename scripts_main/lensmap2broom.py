from pathlib import Path

import numpy as np
import healpy as hp


# ============================================================
# INPUT
# ============================================================

input_dir = Path(
    "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/"
    "outputs_main/simulations/cmb/alms/r_0.00000/lensed"
)

# Directorio donde quedarán los archivos compatibles con BROOM
output_dir = Path(
    "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/"
    "outputs_main/simulations/cmb/alms/r_0.00000/lensed_broom"
)

output_dir.mkdir(parents=True, exist_ok=True)


# ============================================================
# INSTRUMENTO
# ============================================================

frequencies = [27, 39, 93, 145, 225, 280]

fwhm_arcmin = [7.4, 5.1, 2.2, 1.4, 1.0, 0.9]

lmax = 3000


# ============================================================
# CONVERTIR SIMULACIONES
# ============================================================

nsims = 10

for sim in range(nsims):

    # Tus archivos comienzan en 0001
    input_file = (
        input_dir
        / f"lmax_3000_sim_{sim + 1:04d}.npz"
    )

    print(f"Leyendo: {input_file}")

    with np.load(input_file) as f:

        alm_T = f["alm_T"]
        alm_E = f["alm_E"]
        alm_B = f["alm_B"]

    print("Nalm =", len(alm_T))

    # --------------------------------------------------------
    # Array que BROOM espera:
    #
    # (Nfreq, Nfields, Nalm)
    #
    # fields = T,E,B
    # --------------------------------------------------------

    cmb_broom = np.empty(
        (
            len(frequencies),
            3,
            len(alm_T),
        ),
        dtype=np.complex128,
    )

    pixwin_T, pixwin_P = hp.pixwin(
        nside=2048,
        lmax=lmax,
        pol=True,
    )

    for i, fwhm in enumerate(fwhm_arcmin):

        fwhm_rad = np.deg2rad(fwhm / 60.0)

        beam = hp.gauss_beam(
            fwhm=fwhm_rad,
            lmax=lmax,
            pol=True,
        )

        beam_T = beam[:, 0]
        beam_E = beam[:, 1]
        beam_B = beam[:, 2]

        window_T = beam_T * pixwin_T
        window_E = beam_E * pixwin_P
        window_B = beam_B * pixwin_P

        cmb_broom[i, 0] = hp.almxfl(
            alm_T,
            window_T,
        )

        cmb_broom[i, 1] = hp.almxfl(
            alm_E,
            window_E,
        )

        cmb_broom[i, 2] = hp.almxfl(
            alm_B,
            window_B,
        )

    # --------------------------------------------------------
    # BROOM buscará cmb_path_{nsim}.npy
    # --------------------------------------------------------

    output_file = (
        output_dir
        / f"lmax_3000_{sim:05d}.npy"
    )

    np.save(
        output_file,
        cmb_broom,
    )

    print(f"Guardado: {output_file}")
    print("shape =", cmb_broom.shape)
    print()