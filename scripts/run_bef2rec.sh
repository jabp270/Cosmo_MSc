#!/usr/bin/env bash
set -e

# Aumentar stack
ulimit -s unlimited

# Limitar hilos (modo estable)
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OMP_STACKSIZE=512M

# Ejecutar RAM usado en la reconstruccion
# /usr/bin/time -v python mi_script_reconstruccion.py
