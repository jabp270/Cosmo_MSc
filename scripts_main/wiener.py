from pathlib import Path

import numpy as np

from src.filtering.wiener import WienerFilter
from src.simulations.config import WienerConfig


def main() -> None:

    clean_maps_dir = Path(
        "outputs_main/products/component_separation/"
        "ilc_pixel_bias0.0/cmb_reconstruction/output_total"
    )

    # CAMB 'total' spectra (TT, EE, BB, TE) as the signal for the filter.
    cl_signal = np.load(
        "outputs_main/simulations/cmb/cls/r_0.00000/lmax_3000.npz"
    )["total"]

    # Mean residual noise <clean - true>, computed as in Residual_Noise.py.
    # Optional; set to None to filter without a noise term.
    residual_nl_path = Path(
        "outputs_main/products/wiener/residuals/r_0.00000/"
        "mean_residual_cls.npz"
    )

    wiener_settings = WienerConfig(
        method="harmonic",  # or "cninv" or "harmonic"
        nside=2048,
        lmax=3000,
        lmin=2,
        nsim=10,
        start_sim=1,
        clean_maps_dir=clean_maps_dir,
        cl_signal=cl_signal,
        residual_nl_path=residual_nl_path
        
        if residual_nl_path.exists()
        else None,
        out_dir=Path("outputs_main/products/wiener"),
    )

    wiener = WienerFilter(wiener_settings)

    outputs = wiener.run_many()


if __name__ == "__main__":
    main()