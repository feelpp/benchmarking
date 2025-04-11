#!/bin/bash -l

echo "================================================"
saldo --dcgp -b
echo "================================================"


module load python/3.11.6--gcc--8.5.0

python3 -m venv .venv
source .venc/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -I -r requirements.txt
