from src.simulations.simulator_factory import SimulatorFactory
#import storage ...


def main(simulator_str, output_name):

    simulator = SimulatorFactory.get_simulator(simulator_str)

    list_maps = simulator.run_iterative()

    #storage.save(simulations,output_name)


if __name__ == "__main__":
    main("example", "output_name")