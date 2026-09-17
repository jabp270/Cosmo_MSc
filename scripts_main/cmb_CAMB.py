from pathlib import Path

from src.simulations.cmb_simulator import CmbSimulator
from src.simulations.config import Config, CmbConfig

# This is a script to simulate CMB maps using the CmbSimulator class. It defines a configuration for the simulation, creates the simulator, and runs multiple simulations, saving the outputs to disk.

# --------------------- CMB with CAMB ---------------------
# Using the best Planck 2018 cosmological parameters, we will simulate CMB maps with a tensor-to-scalar ratio of r=0.0. FULL-SKY


def main() -> None:
    cmb_settings = CmbConfig(
        nside=2048, #2048 1024 512
        lmax=3000,  #3000 2048 1024
        r=0.00,
        nsim=10,
    )

    simulation_config = Config(
        base_dir=Path("outputs_main"),
        cmb=cmb_settings,
    )

    cmb_sim = CmbSimulator(
        config=simulation_config,
    )

    outputs = cmb_sim.run_many(
        nsims=simulation_config.cmb.nsim,
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