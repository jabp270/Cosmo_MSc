from pathlib import Path

import numpy as np

from src.lensing.lensing import CmbLensing
from src.simulations.config import LensingConfig


def main() -> None:

    clean_maps_dir = Path(
        "outputs_main/products/component_separation/"
        "ilc_pixel_bias0.0/cmb_reconstruction/output_total"
    )

    # CAMB 'total' spectra (TT, EE, BB, TE) used as the (observed) Cl.
    cl_signal = np.load(
        "outputs_main/simulations/cmb/cls/r_0.00000/lmax_3000.npz"
    )["total"]

    # Mean residual noise <clean - true> for the C-inverse prefiltering.
    residual_nl_path = Path(
        "outputs_main/products/wiener/residuals/r_0.00000/"
        "mean_residual_cls.npz"
    )
    residual_nl = None
    if residual_nl_path.exists():
        with np.load(residual_nl_path) as data:
            residual_nl = {
                "TT": data["TT"],
                "EE": data["EE"],
                "BB": data["BB"],
            }

    lensing_settings = LensingConfig(
        nside=2048,
        lmax=3000,
        rlmin=100,
        rlmax=3000,
        elmin=100,
        elmax=3000,
        QDO=(True, True, True, True, True, False),
        nsim=10,
        start_sim=1,
        clean_maps_dir=clean_maps_dir,
        cl_signal=cl_signal,
        residual_nl=residual_nl,
        delens=True,
        out_dir=Path("outputs_main/products/lensing"),
    )

    lensing = CmbLensing(lensing_settings)

    outputs = lensing.run_many()


if __name__ == "__main__":
    main()