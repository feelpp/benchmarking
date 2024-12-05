#!/bin/bash -l
#SBATCH --nodes=1                         # number of nodes
#SBATCH --ntasks=1                       # number of tasks
##SBATCH --qos=default                      # SLURM qos
#SBATCH --ntasks-per-node=8              # number of tasks per node
#SBATCH --cpus-per-task=1                  # number of cores per task
#SBATCH --time=02:00:00                    # time (HH:MM:SS)
#SBATCH --partition=public

matrix_config=""
benchmark_config=""
plots_config=""
move_results=""

while true; do
    case "$1" in
        --matrix-config ) matrix_config="$2"; shift 2 ;;
        --benchmark-config ) benchmark_config="$2"; shift 2 ;;
        --plots-config ) plots_config="$2"; shift 2 ;;
        --move-results ) move_results="$2"; shift 2 ;;
        -- ) shift; break ;;
        * ) break ;;
    esac
done


source .venv/bin/activate
execute-benchmark           \
    -mc $matrix_config      \
    -bc $benchmark_config   \
    -pc $plots_config       \
    --move-results $move_results \
    -v