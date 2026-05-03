from src.simulations.base_simulator import BaseSimulator
from src.utils import utils

class Example(BaseSimulator):

    def __init__(self, nside, lmax, a, b):

        self.nside = nside
        self.lmax = lmax
        self.a = a
        self.b = b

        super().__init__(nside=self.nside, lmax=self.lmax)

    def run(self, seed):
        pass

