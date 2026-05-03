from .example import Example

class SimulatorFactory:

    @staticmethod
    def get_available_config():
        """ 
        Diccionario de metodos de la factory, que crean instancias de simuladores.
        """
        return {
            "example": SimulatorFactory.create_example_simulator,
        }
    
    @staticmethod
    def get_simulator(name_str):
        """ 
        A partir de un nombre, me entrega la instancia de la clase
        """
        simulators = SimulatorFactory.get_available_config()
        return simulators[name_str]()

    @staticmethod
    def create_example_simulator():
        """ 
        Genera instancias de clases, para luego hacer .run()
        """
        return Example(nside=2024, lmax=3000, a=0, b=0)