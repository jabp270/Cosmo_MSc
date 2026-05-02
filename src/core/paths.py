from pathlib import Path


class PathManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.base = Path(cfg.base_output)

    def cmb_cl(self, r: float) -> Path:
        """
        return path of CMB Cl, but you should adds the Cl that you need.

        For example:
        - output_path/cl_unlensed_BB.txt
        - output_path/cl_phiphi.txt
        - output_path/mean_cl_ls_BB.txt
        """
        return self.base / "inputs/CMB" / f"r_{r}" 

    def cmb_convergence(self, sim: int, r: float) -> Path:
        return self.base / "inputs/CMB" / f"r_{r}" / f"cmb_convergence_{sim:03d}.npz"

    def cmb_phi(self, sim: int, r: float) -> Path:
        return self.base / "inputs/CMB" / f"r_{r}" / f"cmb_phi_{sim:03d}.npz"

    def cmb_unlensed(self, sim: int, r: float) -> Path:
        return self.base / "inputs/CMB" / f"r_{r}" / f"cmb_unlensed_{sim:03d}.npz"

    def cmb_lensed(self, sim: int, r: float) -> Path:
        return self.base / "inputs/CMB" / f"r_{r}" / f"cmb_lensed_{sim:03d}.npz"

    def hilc_map(self, sim: int, r: float) -> Path:
        """
        This methode change if you make apodization and mask to the maps

        It will necessary to include conditionals mask == TRUE ...
        """
        return self.base / "outputs/hilc" / f"r_{r}" / f"hilc_{sim:03d}.npz"

    # def wiener_map(self, sim_id: int, r: float) -> Path:
    #     return self.base / f"r_{r:.3f}" / "wf" / f"wf_{sim_id:03d}.npy"

