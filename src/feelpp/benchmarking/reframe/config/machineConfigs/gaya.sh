#!/bin/bash -l

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


python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

execute-benchmark           \
    -mc $matrix_config      \
    -bc $benchmark_config   \
    -pc $plots_config       \
    -v