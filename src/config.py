from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    nsim: int
    nside: int
    lmax: int
    r_values: list[float]
    freqs: list[float] 
    beam: list[float]
    noise: list[float]

    base_input: Path
    base_output: Path

    experiment_name: str

    base_seed: int = 972581
    overwrite: bool = False
    verbose: bool = True