#!/bin/bash -l
#SBATCH --nodes=1                                                       # number of nodes
#SBATCH --ntasks=1                                                      # number of tasks
#SBATCH --qos=default                                                   # SLURM qos
#SBATCH --ntasks-per-node=8                                             # number of tasks per node
#SBATCH --cpus-per-task=1                                               # number of cores per task
#SBATCH --time=02:00:00                                                 # time (HH:MM:SS)
#SBATCH --partition=cn                                                  # partition
#SBATCH --account=ehpc-dev-2024d05-047 --qos=ehpc-dev-2024d05-047     # project account


source /etc/profile.d/modules.sh
export MODULEPATH=/opt/software/modulefiles

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



/opt/software/python/3.9.7/bin/python3 -m venv .venv
source .venv/bin/activate


.venv/bin/python3.9 -m pip install --upgrade pip

echo "Python executable: $(which python3.9)"
echo "Pip executable: $(which pip)"

.venv/bin/python3.9 -m pip install -I -r requirements.txt

execute-benchmark           \
    -mc $matrix_config      \
    -bc $benchmark_config   \
    -pc $plots_config       \
    --move-results $move_results \
    -v