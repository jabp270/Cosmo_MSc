# La idea es ir guardando los plots y no los mapas de cada paso asi que este archivo se encarga de realizar y guardar los plot correctamente

# plots.py
from curvedsky import  utils

from pathlib import Path
import matplotlib.pyplot as plt
import healpy as hp

import plottools as pl
from matplotlib.pyplot import *


def save_figure(
    output_dir,
    name,
    facecolor,
    dpi = 150,
    transparent = True,
):
    """  
    Guarda la figura y la cierra.

  
    Parametros:
    ----------
        - output_dir: carpeta donde se guardara la figura.
        - name: nombre del archivo, debe incluir el .png ó .pdf (PDF mejor)
        - dpi: indica la resolucion de la imagen.

        La cantidad de pixeles será:

        fig = plt.figure(figsize=(8,5)) 8 por 5 pulgadas

        pixeles = 8*dpi * 5*dpi

        - facecolor: color del fondo
        - transparent: Nos da el fondo transparente de las imagenes.

    """
    #Ruta
    output_dir = Path(output_dir)

    #crear carpeta
    output_dir.mkdir(parents=True, exist_ok=True)

    # La figura creada anteriormente ahora toma la variable fig
    fig = plt.gcf() 

    #guardar
    fig.savefig(fname= output_dir / f"{name}", transparent=transparent,facecolor=facecolor, dpi=dpi, bbox_inches="tight")

    plt.close()

        

def plot_spectrum(
    cls: list[np.ndarray], 
    lmax: int,
    label: list[str],
    ymin: float,
    ymax: float,
    xlabel = r"$\ell$",
    ylabel = r"$C_\ell$",
    xlog = False,
    ylog = False,
    figsize = (7,5),
) -> figure:
    """ 
    Grafica varios espectros en un mismo eje.
    """

    #crear figura
    fig, ax = plt.subplots(figsize=figsize)

    #ells
    ells = np.arange(lmax + 1)

    for index, cl in enumerate(cls):

        ax.plot(ells, cl, label=label[index])

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(left=10)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()

    if xlog:
        ax.set_xscale("log")
    if ylog:
        ax.set_yscale("log")

    fig.tight_layout()

    return fig, ax

###########################################################
# LISTO

def plot_tqu(
    maps,
    output_dir,
    name,
    freq=None,
    unit=r"$\mu K$",
):
    """
    Guarda plots T, Q, U de mapas HEALPix.

    Parameters
    ----------
    maps : tuple[np.ndarray, np.ndarray, np.ndarray]
        Mapas T, Q, U.

    output_dir : str | Path
        Directorio donde guardar.

    name : str
        Nombre base del archivo.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    T, Q, U = maps

    for field, m , val in zip(("T", "Q", "U"), (T, Q, U), (100, 10, 10)):

        if freq!=None:
            hp.mollview(
                m,
                title=f"{name} - {field} - {freq}",
                unit=unit,
                min=-val,
                max=val,
                cmap="jet",
            )

            plt.savefig(
                output_dir / f"{name}_{field}_{freq}.png",
                dpi=150,
                bbox_inches="tight",
            )
        else:
            hp.mollview(
                m,
                title=f"{name} - {field}",
                unit=unit,
                min=-val,
                max=val,
                cmap="jet",
            )

            plt.savefig(
                output_dir / f"{name}_{field}.png",
                dpi=150,
                bbox_inches="tight",
            )


        plt.close()

def plot_teb(
    maps,
    output_dir,
    name,
    freq=None,
    unit=r"$\mu K$",
):
    """
    Guarda plots T, E, B de mapas HEALPix.

    Parameters
    ----------
    maps : tuple[np.ndarray, np.ndarray, np.ndarray]
        Mapas T, E, B.

    output_dir : str | Path
        Directorio donde guardar.

    name : str
        Nombre base del archivo.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    T, E, B = maps

    for field, m , val in zip(("T", "E", "B"), (T, E, B), (100, 10, 1)):

        if freq!=None:
            hp.mollview(
                m,
                title=f"{name} - {field} - {freq}",
                unit=unit,
                min=-val,
                max=val,
                cmap="jet",
            )

            plt.savefig(
                output_dir / f"{name}_{field}_{freq}.png",
                dpi=150,
                bbox_inches="tight",
            )
        else:
            hp.mollview(
                m,
                title=f"{name} - {field}",
                unit=unit,
                min=-val,
                max=val,
                cmap="jet",
            )

            plt.savefig(
                output_dir / f"{name}_{field}.png",
                dpi=150,
                bbox_inches="tight",
            )

        plt.close()


def plot_teb_alm(
    alm,
    output_dir,
    name,
    nside,
    lmax,
    freq=None,
    unit=r"$\mu K$",
):
    """
    Guarda plots T, E, B de mapas HEALPix.

    Parameters
    ----------
    alm : tuple[np.ndarray, np.ndarray, np.ndarray]
        Alms T, E, B.

    output_dir : str | Path
        Directorio donde guardar.

    name : str
        Nombre base del archivo.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

       # alm debe tener shape (3, Nalm)
    alm_T = alm[0]
    alm_E = alm[1]
    alm_B = alm[2]
    del alm
    
    # Cada alm es un campo escalar independiente
    map_T = hp.alm2map(
        alm_T,
        nside=nside,
        lmax=lmax,
        pol=False,
    )
    del alm_T

    map_E = hp.alm2map(
        alm_E,
        nside=nside,
        lmax=lmax,
        pol=False,
    )
    del alm_E

    map_B = hp.alm2map(
        alm_B,
        nside=nside,
        lmax=lmax,
        pol=False,
    )
    del alm_B

    maps = (map_T, map_E, map_B)
    del map_T, map_E, map_B

    for field, m , val in zip(("T", "E", "B"), maps, (100, 10, 1)):

        if freq!=None:
            hp.mollview(
                m,
                title=f"{name} - {field} - {freq}",
                unit=unit,
                min=-val,
                max=val,
                cmap="jet",
            )

            plt.savefig(
                output_dir / f"{name}_{field}_{freq}.png",
                dpi=150,
                bbox_inches="tight",
            )
        else:
            hp.mollview(
                m,
                title=f"{name} - {field}",
                unit=unit,
                min=-val,
                max=val,
                cmap="jet",
            )

            plt.savefig(
                output_dir / f"{name}_{field}.png",
                dpi=150,
                bbox_inches="tight",
            )

        plt.close()