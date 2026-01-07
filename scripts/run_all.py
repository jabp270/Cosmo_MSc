import run_camb_fiducial
import Foreground_maps
import lensed_maps
import Noise_maps
import obs_maps
import HILC_maps


if __name__ == "__main__":
    run_camb_fiducial.main()
    print("1")
    lensed_maps.main()
    print("2")
    Foreground_maps.main()
    print("3")
    Noise_maps.main()
    print("4")
    obs_maps.main()
    print("5")
    HILC_maps.main()
    print("6")