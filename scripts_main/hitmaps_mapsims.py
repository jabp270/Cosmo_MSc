
import gc
import numpy as np
import healpy as hp
from mapsims import noise
import os
import mapsims

from pathlib import Path


NSIDE = 2048
SENSITIVITY_MODE = "goal"
OUTPUT_DIR = Path("SO_maps") / "Hitmaps"

SAT_TUBES = ["ST0", "ST1", "ST2", "ST3"]
LAT_TUBES = ["LT4", "LT5", "LT6"] # "LT0", "LT1", "LT2", "LT3", 

# Se busca ruta de intrument parameter
def find_instrument_file():
    data_dir = Path(mapsims.__file__).parent / "data"

    for f in data_dir.rglob("*.tbl"):
        try:
            if "ST0" in f.read_text(errors="ignore"):
                return f
        except Exception:
            pass

    raise FileNotFoundError(
        "No se encontró una tabla instrumental de mapsims que contenga ST0."
    )


def get_tube_hitmaps(noise_sim, tube):
    hitmaps, fsky = noise_sim.get_hitmaps(tube)
    hitmaps = np.asarray(hitmaps)

    if hitmaps.ndim == 1:
        hitmaps = hitmaps[np.newaxis, :]

    print(f"{tube}: shape={hitmaps.shape}, fsky={np.asarray(fsky)}")
    return hitmaps, fsky


def save_tube_hitmaps(hitmaps, telescope, tube):
    telescope_dir = OUTPUT_DIR / telescope
    telescope_dir.mkdir(parents=True, exist_ok=True)

    filename = telescope_dir / f"{tube}_hitmap_nside{NSIDE}.fits"

    nband = hitmaps.shape[0]
    column_names = [f"BAND_{i}" for i in range(nband)]

    hp.write_map(
        filename,
        hitmaps.astype(np.float32),
        overwrite=True,
        dtype=np.float32,
        column_names=column_names,
    )

    print(f"  -> guardado: {filename}")
    return filename


def process_tubes(noise_sim, telescope, tubes, summary_lines):
    print()
    print("=" * 70)
    print(f"Procesando {telescope}")
    print("=" * 70)

    for tube in tubes:
        hitmaps, fsky = get_tube_hitmaps(noise_sim, tube)

        filename = save_tube_hitmaps(
            hitmaps=hitmaps,
            telescope=telescope,
            tube=tube,
        )

        summary_lines.append(
            f"{telescope}  {tube}  "
            f"shape={tuple(hitmaps.shape)}  "
            f"fsky={np.asarray(fsky).tolist()}  "
            f"file={filename}"
        )

        del hitmaps
        gc.collect()



def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    instrument_file = find_instrument_file()

    print("mapsims:", mapsims.__version__)
    print("Tabla instrumental:")
    print(instrument_file)
    print()
    print(f"NSIDE = {NSIDE}")
    print(f"Sensitivity mode = {SENSITIVITY_MODE}")
    print(f"Output = {OUTPUT_DIR.resolve()}")

    noise_sim = noise.SONoiseSimulator(
        nside=NSIDE,
        sensitivity_mode=SENSITIVITY_MODE,
        instrument_parameters=str(instrument_file),
    )

    summary_lines = [
        "Simons Observatory hitmaps",
        f"mapsims_version={mapsims.__version__}",
        f"nside={NSIDE}",
        f"sensitivity_mode={SENSITIVITY_MODE}",
        f"instrument_parameters={instrument_file}",
        "",
    ]

    # process_tubes(
    #     noise_sim=noise_sim,
    #     telescope="SAT",
    #     tubes=SAT_TUBES,
    #     summary_lines=summary_lines,
    # )

    process_tubes(
        noise_sim=noise_sim,
        telescope="LAT",
        tubes=LAT_TUBES,
        summary_lines=summary_lines,
    )

    summary_file = OUTPUT_DIR / "hitmaps_summary.txt"
    summary_file.write_text("\n".join(summary_lines) + "\n")

    print()
    print("=" * 70)
    print("Proceso terminado")
    print("=" * 70)
    print(f"Resumen guardado en: {summary_file}")


if __name__ == "__main__":
    main()
