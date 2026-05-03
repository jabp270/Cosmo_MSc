from abc import ABC, abstractmethod

class BaseSimulator(ABC):
    def __init__(self, nside, lmax):
        self.nside = nside
        self.lmax = lmax

    @abstractmethod
    def run(self, seed):
        pass



