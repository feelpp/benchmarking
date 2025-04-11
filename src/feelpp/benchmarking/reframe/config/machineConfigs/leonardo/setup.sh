#!/bin/bash -l

echo "================================================"
saldo --dcgp -b
echo "================================================"


# !!!!LOAD PYTHON MODULE

python3 -m venv .venv
source .venc/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -I -r requirements.txt
