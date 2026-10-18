#!/bin/bash

# Aumentar stack, se utiliza para variables temporales. El limite normal es de 8 Mib (Esto explica el segmentation fault)
ulimit -s unlimited


/usr/bin/time -v python -u -X faulthandler scripts_main/simulations_broom.py 2> time.log

status=$?

# Peak RAM
peak_kb=$(grep "Maximum resident set size" time.log | awk '{print $6}')
peak_gb=$(awk "BEGIN {printf \"%.2f\", $peak_kb/1024/1024}")
# Tiempo total
elapsed=$(grep "Elapsed (wall clock) time" time.log | awk -F': ' '{print $2}')

echo
echo "================================="
echo "Peak RAM: ${peak_gb} GB"
echo "Tiempo total: $elapsed"
echo "Python terminó con código: $status"
echo "================================="

exit $status
