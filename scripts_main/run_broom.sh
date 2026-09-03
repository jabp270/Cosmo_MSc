#!/bin/bash

# ==============================
# LIMITAR PARA AHORRAR MEMORIA
# ==============================

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export BLIS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

# Algunos paquetes respetan también esto
export OMP_DYNAMIC=FALSE

echo "=============================="
echo " Ejecutando BROOM"
echo " Threads = 1"
echo "=============================="

