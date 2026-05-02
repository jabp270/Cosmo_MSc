from abc import ABC, abstractmethod
import camb
import numpy as np
import utils ### debo revisar esto

class BaseSimulator(ABC):

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def simulate(self):
        pass
    
           



