from dataclasses import dataclass, Field, asdict
from pathlib import Path
from typing import Any

import numpy as np

# Configuration for simulation parameters

# -------------------------------------------------
# ------------------- CAMB ------------------------
# -------------------------------------------------

@dataclass
class CmbConfig:
    nside: int
    nsim: int
    lmax: int
    r: int
    full_sky: bool = True
    cmb_seed: int = 10000
    phi_seed: int = 20000
    overwrite: bool = False
    start_sim: int = 1

# -------------------------------------------------
# ------------------ Noise ------------------------
# -------------------------------------------------

@dataclass
class NoiseConfig:
    model: str
    experiment: str
    freq: list[float]
    noise_t: list[float]
    noise_p: list[float]
    nside: int
    lmax: int
    nside: int
    nsim: int

    noise_seed: int = 40000
    overwrite: bool = False

# -------------------------------------------------
# ------------------ PYSM3 ------------------------
# -------------------------------------------------

@dataclass
class ForegroundConfig:
    models: list[str]
    freq: list[float]
    nside: int
    nsim: int
    lmax: int

    foreground_seed: int = 30000
    overwrite: bool = False

# Falta ExternalConfig, etc.

# -------------------------------------------------
# ------------------ BROOM ------------------------
# -------------------------------------------------

# @dataclass
# class CompsepConfig:
#     method: str
#     domain: str
#     component_out: str

#     needlet_config: list[dict[str, Any]] | None = None

#     b_squared: bool | None = None # If True, needlet bands are squared. Therefore needlet transformation is performed just once before component separation. 
#     adapt_nside: bool | None = None # If True, the HEALPix resolution of needlet maps is adapted to the sampled range of multipoles.
#     save_needlets: bool | None = None # If True, needlet bands are saved in the specific method path. 
#     save_weights: bool | None = None # If True, the weights used to reconstruct the maps are saved in the path specified in path_outputs.

#     ilc_bias: float = 0.1
#     reduce_ilc_bias: bool = True
#     cov_noise_debias: float = 0.2
#     load_noise_covariance: bool = False
#     minimize_variance: bool = False


@dataclass
class InstrumentConfig:

    frequency: list[float]

    depth_I: list[float]
    depth_P: list[float]

    fwhm: list[float]

    channels_tags: list[str]

    beams: str = "gaussian"

    ell_knee: list[float] | None = None
    alpha_knee: list[float] | None = None

@dataclass
class CleaningConfig:

    # Required parameters
    instrument: InstrumentConfig
    lmax: int
    nside: int
    compsep: list[dict[str, Any]]
    path_outputs: str | Path

    # Optional parameters
    fwhm_out: float | None = None

    data_type: str = "maps"

    field_in: str = "TEB"
    field_out: str = "TEB"

    nside_in: int | None = None

    lmin: int = 2

    bring_to_common_resolution: bool = False

    pixel_window_in: bool = True
    pixel_window_out: bool = False

    mask_observations: str | Path | None = None
    mask_covariance: str | Path | None = None
    leakage_correction: str | None = None

    save_compsep_products: bool = True
    return_compsep_products: bool = False

    verbose: bool = True

    units: str = "uK_CMB"

    bandpass_integrate: bool = False

    fwhm_arcmin: list[float] | None = None
    freq: list[float] | None = None

    def __post_init__(self):

        if self.nside_in is None:
            self.nside_in = self.nside

        if self.fwhm_out is None:
            self.fwhm_out = max(
                self.instrument.fwhm
            )

        if self.freq is None:
            self.freq = self.instrument.frequency

        if self.fwhm_arcmin is None:
            self.fwhm_arcmin = self.instrument.fwhm


# -------------------------------------------------
# ------------------- WIENER -----------------------
# -------------------------------------------------

@dataclass
class WienerConfig:
    
    method: str


# -------------------------------------------------
# ------------------ LENSING ----------------------
# -------------------------------------------------

@dataclass
class LensingConfig:

    nside: int 
    lmax: int

    # Multipoles used by the quadratic estimators.
    rlmin: int
    rlmax: int 

    # Multipoles used by the delensing convolution.
    elmin: int 
    elmax: int 

    fwhm_out: float
    Folder_name: str

    # Estimators to combine (order: TT, TE, EE, TB, EB, BB).
    QDO: tuple[bool, ...] 

    nsim: int = 1
    start_sim: int = 1

    # Delensing -----------------------------------------------------
    delens: bool = False
    phi_alm: np.ndarray | None = None
    wiener_e: bool = True


@dataclass
class Config:
    base_dir: Path
    cmb: CmbConfig | None = None
    foreground: ForegroundConfig | None = None
    noise: NoiseConfig | None = None
    cleaning: CleaningConfig | None = None
    wiener: WienerConfig | None = None
    lensing: LensingConfig | None = None