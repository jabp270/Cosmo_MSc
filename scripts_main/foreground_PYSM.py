from pathlib import Path

from src.simulations.foreground_simulator import ForegroundSimulator
from src.simulations.config import Config, ForegroundConfig

# This is a script to simulate FOREGROUND alms using the ForegroundSimulator class. It defines a configuration for the simulation, creates the simulator, and runs multiple simulations, saving the outputs to disk.

# --------------------- FOREGROUND with PYSM3 ---------------------
# FULL-SKY


def main() -> None:
    foreground_settings = ForegroundConfig(
        models=["s6", "d11"],
        freq=[27, 39, 93, 145, 225, 280], 
        nside=2048,
        lmax=3000,
        nsim=10,
    )

    simulation_config = Config(
        base_dir=Path("outputs_main"),
        foreground=foreground_settings,
    )

    foreground_sim = ForegroundSimulator(
        Config=simulation_config,
    )

    outputs = foreground_sim.run_many(
        nsims=simulation_config.foreground.nsim,
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