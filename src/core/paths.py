from pathlib import Path


class PathManager:

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

        self.setup_paths()
        self.create_directories()

    def setup_paths(self):
        """ 
        Generate paths for directories.
        """
        self.data_dir = self.base_dir / "data"
        self.results_dir = self.base_dir / "results"

        self.dirs = {
            "cmb_cls": self.data_dir / "cmb" / "cls",
            "cmb_alms": self.data_dir / "cmb" / "alms",
            "cmb_kappa": self.data_dir / "cmb" / "kappa",
            "cmb_phi": self.data_dir / "cmb" / "phi",
            "noise_cmb": self.data_dir / "noise",
            "foregrounds": self.data_dir / "foregrounds",
            "hilc": self.results_dir / "hilc",
            "filters": self.results_dir / "filters",
            "rec_lensing": self.results_dir / "rec_lensing",
            
        }

    def create_directories(self):
        """ 
        Create folders of directories.
        """
        for path in self.dirs.values():
            path.mkdir(parents=True, exist_ok=True)

    def cmb_cl(self, r: float, filename: str) -> Path:
        """
        return the path of CMB Cl, but you should adds the Cl that you need.

        For example:
        - .../cl_unlensed_BB.txt
        - .../cl_phiphi.txt
        - .../mean_cl_ls_BB.txt
        """
        return self.dirs["cmb_cls"] / f"r_{r:.4f}" / f"{filename}.txt"

    def cmb_convergence(self, sim: int, r: float) -> Path:
        return self.dirs["cmb_kappa"] / f"r_{r:.4f}" / f"cmb_convergence_{sim:03d}.npz"

    def cmb_phi(self, sim: int, r: float) -> Path:
        return self.dirs["cmb_phi"] / f"r_{r:.4f}" / f"cmb_phi_{sim:03d}.npz"

    def cmb_unlensed(self, sim: int, r: float) -> Path:
        return self.dirs["cmb_alms"] / f"r_{r:.4f}" / f"cmb_unlensed_{sim:03d}.npz"

    def cmb_lensed(self, sim: int, r: float) -> Path:
        return self.dirs["cmb_alms"] / f"r_{r:.4f}" / f"cmb_lensed_{sim:03d}.npz"

    def hilc_map(self, sim: int, r: float) -> Path:
        return self.dirs["hilc"] / f"r_{r:.4f}" / f"hilc_{sim:03d}.npz"

    # def wiener_map(self, sim_id: int, r: float) -> Path:
    #     return self.base / f"r_{r:.3f}" / "wf" / f"wf_{sim_id:03d}.npy"

