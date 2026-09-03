from pathlib import Path
import numpy as np

class StorageManager:

    def __init__(self, base_dir: Path, overwrite: bool = False):
        self.base_dir = base_dir
        self.overwrite = overwrite


    def exists(self, path: Path) -> bool:
        """ 
        Checks if the path exists.
        """
        return path.exists()

    # -----------------
    # Save and load files
    # -----------------

    def save_npz(self, path: Path, **arrays):
        """ 
        Save the files in .npz format. 
        """
        if path.exists() and not self.overwrite:
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, **arrays)

    def load_npz(self, path: Path):
        """ 
        Load the files in .npz format.
        """
        if not path.exists():
            raise FileNotFoundError(f"Don't exist the file: {path}")
        return np.load(path, allow_pickle=True)

    def save_txt(self, path: Path, array, header: str = ""):
        """ 
        Save the files in .txt format.
        """
        if path.exists() and not self.overwrite:
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(path, array, header=header)

    def load_txt(self, path: Path):
        """ 
        Load the files in .txt format.
        """
        if not path.exists():
            raise FileNotFoundError(f"Don't exist the file: {path}")
        return np.loadtxt(path)

    # -----------
    # Delete folders
    # -----------

    # IN PROCESS / ONGOING

# Global Instance
storage = StorageManager()
    

