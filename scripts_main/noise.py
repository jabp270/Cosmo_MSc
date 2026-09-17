from pathlib import Path

from src.simulations.noise_simulator import NoiseSimulator
from src.simulations.config import Config, NoiseConfig

import numpy as np

# This is a script to noise alms using the NoiseSimulator class. It defines a configuration for the simulation, creates the simulator, and runs multiple simulations, saving the outputs to disk.

# --------------------- Noise ---------------------
# FULL-SKY

def main() -> None:
    noise_settings = NoiseConfig(
        model="white",
        experiment="SO_LAT",
        freq=[27, 39, 93, 145, 225, 280], 
        noise_t=[71,36,8.0,10,22,54],
        noise_p=np.array(np.array([71,36,8.0,10,22,54]))*np.sqrt(2),
        nside=2048,
        lmax=3000,
        nsim=10,
    )

    simulation_config = Config(
        base_dir=Path("outputs_main"),
        noise=noise_settings,
    )

    noise_sim = NoiseSimulator(
        config=simulation_config
    )

    outputs = noise_sim.run_many(
        nsims=simulation_config.noise.nsim,
        start_sim=1,
        overwrite=False,
    )

    print("\nGenerated files:")

    for sim_index, simulation_outputs in enumerate(outputs):
        print(f"\nSimulation {sim_index}")

        for name, output_path in simulation_outputs.items():
            print(f"  {name}: {output_path}")


if __name__ == "__main__":
    main()