#!/bin/bash -l

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/hpc.env"

echo "================================================"
sacctmgr show association where account=$discoverer_project_id

sshare -A $discoverer_project_id -u " " -o account,user,GrpTRESRaw%80,GrpTRESMins,RawUsage

lfs quota -g $discoverer_project_id /discofs
lfs quota -g $discoverer_project_id /disco2fs
echo "==============================================="

matrix_config=""
benchmark_config=""
plots_config=""

while true; do
    case "$1" in
        --matrix-config ) matrix_config="$2"; shift 2 ;;
        --benchmark-config ) benchmark_config="$2"; shift 2 ;;
        --plots-config ) plots_config="$2"; shift 2 ;;
        -- ) shift; break ;;
        * ) break ;;
    esac
done



/opt/software/python/3.9.7/bin/python3 -m venv .venv
source .venv/bin/activate


.venv/bin/python3.9 -m pip install --upgrade pip
.venv/bin/python3.9 -m pip install -I -r requirements.txt

execute-benchmark           \
    -mc $matrix_config      \
    -bc $benchmark_config   \
    -pc $plots_config       \
    -v