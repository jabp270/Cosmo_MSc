import os
import numpy as np
import healpy as hp
from config import NSIDE, LMAX, NSIM

# def inv_filter(fil, lmin=2):
#     """
#     Invierte el filtro para que no explote en los l = 0, 1
#     """
#     inv = np.zeros_like(fil)
#     inv[lmin:] = 1.0 / fil[lmin:]
#     return inv

def inv_filter(fil, lmin=2, eps=1e-8):
    """
    Invierte el filtro para que no explote en los l = 0, 1 ni tampoco en otros l's
    """
    inv = np.zeros_like(fil)
    good = np.abs(fil) > eps
    good[:lmin] = False
    inv[good] = 1.0 / fil[good]
    return inv

def main():

    ruta = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/obs_maps/"

    ruta_n = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/fiducial/Noise_SO"

    out_dir = "/home/jorge/Escritorio/Proy_cosmo/Cosmo_MSc/outputs/Filtered_maps/HILC_maps/Full_sky"

    vect_r = np.array([0,0.01,0.05,0.1])
    freq = np.array([27, 39, 93, 145, 225, 280])
    names = np.array(["T", "E" , "B"])

    nside = NSIDE
    lmax  = LMAX
    nsim  = NSIM

    # ells = np.arange(0, lmax + 1)

    nfreq = len(freq)
    one = np.ones(nfreq, dtype=float )  # vector columna de 1's

    # Filtro por Beam y Window pixel
    pwT, pwP = hp.pixwin(nside, pol=True, lmax=lmax) # window pixel

    vect_fwhm = np.array([7.4, 5.1, 2.2, 1.4, 1.0, 0.9])*np.pi / (180 * 60) #en radianes
    #target_fwhm = np.max(vect_fwhm)
    #target_beam = hp.sphtfunc.gauss_beam(fwhm=target_fwhm, lmax=lmax, pol=True)
    
    list_fil = {}
    for j,f in enumerate(freq):
        list_fil[f] = {}
        
        beam = hp.sphtfunc.gauss_beam(fwhm=vect_fwhm[j], lmax=lmax, pol=True)
        # bT  = beam[:, 0]   # temperatura
        # bE  = beam[:, 1]   # grad/electric (E)
        # bB  = beam[:, 2]   # curl/magnetic (B)

        for i, name in enumerate(names):
            if name == "T":
                fil = beam[:, i] * pwT  #/target_beam[:,i]
            else:
                fil = beam[:, i] * pwP  #/target_beam[:,i]
            
            list_fil[f][name] = fil

    for r in vect_r:
        print(f"> r = {r}")

        out_dir_r = os.path.join(out_dir, f"r_{r}")
        os.makedirs(out_dir_r, exist_ok=True)

        ruta_r = os.path.join(ruta, f"r_{r}")

        for sim in range(nsim):

            Cl_T = np.zeros((nfreq, nfreq, lmax+1))
            Cl_E = np.zeros((nfreq, nfreq, lmax+1))
            Cl_B = np.zeros((nfreq, nfreq, lmax+1))

            ### Calculamos la matriz de covarianza

            dec_almT = {}
            dec_almE = {}
            dec_almB = {}
            for f in freq:
                d = np.load(os.path.join(ruta_r, f"alm_obs_{f}_LAT{sim+1}.npz"))
                dec_almT[f] = hp.almxfl(d["almT"], inv_filter(list_fil[f]["T"]))
                dec_almE[f] = hp.almxfl(d["almE"], inv_filter(list_fil[f]["E"]))
                dec_almB[f] = hp.almxfl(d["almB"], inv_filter(list_fil[f]["B"]))

            # covarianza cross-freq

            for i, fi in enumerate(freq):

                for j, fj in enumerate(freq):

                    Cl_T[i,j,:] = hp.alm2cl(dec_almT[fi], dec_almT[fj], lmax=lmax)
                    Cl_E[i,j,:] = hp.alm2cl(dec_almE[fi], dec_almE[fj], lmax=lmax)
                    Cl_B[i,j,:] = hp.alm2cl(dec_almB[fi], dec_almB[fj], lmax=lmax)

            ### Calculamos pesos

            weights_T = np.zeros((lmax+1, nfreq)) 
            weights_E = np.zeros((lmax+1, nfreq)) 
            weights_B = np.zeros((lmax+1, nfreq)) 

            for ell in range(2, lmax+1):

                C_T = Cl_T[:,:,ell]   #/(2*ell + 1)    # cov matriz nfreq x nfreq 
                C_E = Cl_E[:,:,ell]   #/(2*ell + 1)
                C_B = Cl_B[:,:,ell]   #/(2*ell + 1)

                C_Ti = np.linalg.pinv(C_T)     # invierte la matriz
                num = np.dot(C_Ti, one)
                one_T = one.T
                den = np.dot(one_T, np.dot(C_Ti, one))
                weights_T[ell,:] = num / den    
                

                C_Ei = np.linalg.pinv(C_E)    
                num1 = np.dot(C_Ei, one)
                den1 = np.dot(one_T, np.dot(C_Ei, one))
                weights_E[ell,:] = num1 / den1


                C_Bi = np.linalg.pinv(C_B)     
                num2 = np.dot(C_Bi, one)
                den2 = np.dot(one_T, np.dot(C_Bi, one))
                weights_B[ell,:] = num2 / den2
            
            alm_clean_T = np.zeros_like(dec_almT[280])
            alm_clean_E = np.zeros_like(dec_almT[280])
            alm_clean_B = np.zeros_like(dec_almT[280])
            
            Nl_HILC_T = np.zeros(lmax+1)
            Nl_HILC_E = np.zeros(lmax+1)
            Nl_HILC_B = np.zeros(lmax+1)

            for i,f in enumerate(freq):  

                alm_clean_T += hp.almxfl(dec_almT[f], weights_T[:, i])
                alm_clean_E += hp.almxfl(dec_almE[f], weights_E[:, i])
                alm_clean_B += hp.almxfl(dec_almB[f], weights_B[:, i])

                # ### calcular el residuo del ruido
                 
                # N_T = np.loadtxt(os.path.join(ruta_n, f"Noise_{f}_T{sim + 1}.txt"))
                # N_P = np.loadtxt(os.path.join(ruta_n, f"Noise_{f}_P{sim + 1}.txt"))
                # deconvolved_NT = N_T*(inv_filter(list_fil[f]["T"])**2)
                # deconvolved_NE = N_P*(inv_filter(list_fil[f]["E"])**2)
                # deconvolved_NB = N_P*(inv_filter(list_fil[f]["B"])**2)

                # Nl_HILC_T += (weights_T[:, i]**2)*deconvolved_NT
                # Nl_HILC_E += (weights_E[:, i]**2)*deconvolved_NE
                # Nl_HILC_B += (weights_B[:, i]**2)*deconvolved_NB

            ### Guardar mapa

            np.savez_compressed(
                os.path.join(out_dir_r, f"alms_{sim+1}.npz"),
                almT=alm_clean_T,  
                almE=alm_clean_E,  
                almB=alm_clean_B     
                )
            
            # np.savez_compressed(
            #     os.path.join(out_dir_r, f"Nl_HILC{sim+1}.npz"),
            #     NT=Nl_HILC_T,  
            #     NE=Nl_HILC_E,  
            #     NB=Nl_HILC_B     
            #     )

if __name__ == "__main__":
    main()

