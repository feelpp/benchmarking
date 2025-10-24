#!/bin/bash -l

# module load env/staging/2023.1
module load Apptainer/1.3.6-GCCcore-13.3.0

export GIRDER_API_KEY=$GIRDER_API_KEY

module load Python
python -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

while getopts "m:b:p:" opt; do
  case $opt in
    m) MACHINE_CONFIG=$OPTARG ;;
    b) BENCHMARK_CONFIG=$OPTARG ;;
    p) PLOTS_CONFIG=$OPTARG ;;
    *) echo "Usage: $0 [-m machine_config] [-b benchmark_config] [-p plots_config]" ;;
  esac
done

apptainer registry login --username ${GHCRIO_USER} --password ${GHCRIO_TOKEN} docker://ghcr.io

feelpp-benchmarking-exec \
    -mc $MACHINE_CONFIG \
    -bc $BENCHMARK_CONFIG \
    -pc $PLOTS_CONFIG \
    -rfm="-v"