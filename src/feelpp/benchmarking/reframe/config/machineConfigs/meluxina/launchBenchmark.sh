#!/bin/bash -l
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --qos=${QOS}
#SBATCH --ntasks-per-node=8         #reframe can submit 8 jobs at the time, async.
#SBATCH --cpus-per-task=1
#SBATCH --time=02:00:00
#SBATCH --partition=${SUBMIT_PARTITION}
#SBATCH --account=${ACCOUNT}

module load Apptainer/1.2.4-GCCcore-12.3.0

export GIRDER_API_KEY=$GIRDER_API_KEY

module load Python/3.8.6-GCCcore-10.2.0
python3.8 -m venv .venv
source .venv/bin/activate
.venv/bin/python3.8 -m pip install --upgrade pip
.venv/bin/python3.8 -m pip install -r requirements.txt

while getopts "m:b:p:" opt; do
  case $opt in
    m) MACHINE_CONFIG=$OPTARG ;;
    b) BENCHMARK_CONFIG=$OPTARG ;;
    p) PLOTS_CONFIG=$OPTARG ;;
    *) echo "Usage: $0 [-m machine_config] [-b benchmark_config] [-p plots_config]" ;;
  esac
done


execute-benchmark \
    -mc $MACHINE_CONFIG \
    -bc $BENCHMARK_CONFIG \
    -pc $PLOTS_CONFIG \
    -v