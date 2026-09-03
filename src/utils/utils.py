import numpy as np
import healpy as hp

def make_seeds(nsim: int, base_seed: int = 268359):
    """
    Devuelve un diccionario con seeds por simulación y por componente (cmb, phi y ruido).

    Entrega: [seeds[i]['cmb'], seeds[i]['phi'], seeds[i]['noise_T'], ...]
    """
    ss = np.random.SeedSequence(base_seed)

    # cada secuencia debe tener nsim numeros aleatorios
    sim_seqs = ss.spawn(nsim)

    seeds = []
    for i in range(nsim):
        # Cada simulacion tiene 5 seed distintos cmb, phi, ruido T, ruido Q , ruido U, fpreground
        comp_seqs = sim_seqs[i].spawn(6)

        # generate_state(1) devuelve array size 1, lo convertimos a int en 32 bit.
        seed_cmb   = int(comp_seqs[0].generate_state(1, dtype=np.uint32)[0])
        seed_phi   = int(comp_seqs[1].generate_state(1, dtype=np.uint32)[0])
        seed_noise_T = int(comp_seqs[2].generate_state(1, dtype=np.uint32)[0])
        seed_noise_E = int(comp_seqs[3].generate_state(1, dtype=np.uint32)[0])
        seed_noise_B = int(comp_seqs[4].generate_state(1, dtype=np.uint32)[0])
        seed_foreground = int(comp_seqs[5].generate_state(1, dtype=np.uint32)[0])

        seeds.append({
            "cmb": seed_cmb,
            "phi": seed_phi,
            "noise_T": seed_noise_T,
            "noise_E": seed_noise_E,
            "noise_B": seed_noise_B,
            "foreground": seed_foreground,
        })

    return seeds
