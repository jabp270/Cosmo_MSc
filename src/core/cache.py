from pathlib import Path
import numpy as np

class CacheManager:
    def exists(self, path: Path) -> bool:
        return path.exists()

    def save_array(self, path: Path, array):
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, array)

    def load_array(self, path: Path):
        return np.load(path, allow_pickle=True)
    
    def load_txt(self, path: Path):
        return np.loadtxt(path)
    
    