
from pathlib import Path

import numpy as np
import healpy as hp

from src.lensing.lensing import CmbLensing
from src.simulations.cmb_simulator import CmbSimulator

from src.simulations.config import (
    Config,
    CmbConfig,
    LensingConfig,
)

# Normalizacion de mean field
normalize = True

def test_0() -> None:

    nside = 2048
    lmax = 3000

    rlmin = 100
    rlmax = 3000

    cmb_settings = CmbConfig(
        nside=nside,
        lmax=lmax,
        r=0.0,
        nsim=100,
        start_sim=1,
    )

    lensing_settings = LensingConfig(
        nside=nside,
        lmax=lmax,
        rlmin=rlmin,
        rlmax=rlmax,
        elmin=rlmin,
        elmax=rlmax,
        QDO=(True, True, True, True, True, False),
        nsim=100,
        start_sim=1,
        fwhm_out=0.0,
        Folder_name="mean_field",
    )

    config = Config(
        base_dir="outputs_main",
        cmb=cmb_settings,
        lensing=lensing_settings,
    )

    cmb = CmbSimulator(config)
    lensing = CmbLensing(config)

    #Cargar espectros
    powers = cmb.compute_cls(
        names=["unlensed_total", "lens_potential", "total"],
        overwrite=False,
    )

    # Cargar máscara
    path_mask = "SO_maps/Mask_SO/my_mask.fits"

    mask = hp.read_map(path_mask)

    if hp.get_nside(mask) != nside:
        raise ValueError(f"Máscara nside={hp.get_nside(mask)}, pero se requiere nside={nside}")

    #Calcular mean field
    mean_field = lensing.cmb_mean_field(
        cl=powers,
        mask=mask,
        lmax=lmax,
        nside=nside,
        nsim=config.cmb.nsim,
        start_sim=config.cmb.start_sim,
        normalize=normalize,
    )

    # Guardar mean field
    output_dir = Path("outputs_main/products/Lensing reconstruction/Mean Field")

    output_dir.mkdir(parents=True, exist_ok=True,)

    output_file = output_dir / "cmb_mean_field.npz"

    np.savez_compressed(
        output_file,
        **mean_field,
    )

    print(f"[OK] Mean field guardado en: {output_file}")

if __name__ == "__main__":
    test_0()
