#!/bin/bash -l


echo "==========================="
myquota
echo "==========================="

module load Python/3.8.6-GCCcore-10.2.0
python3.8 -m venv .venv
source .venv/bin/activate
.venv/bin/python3.8 -m pip install --upgrade pip
.venv/bin/python3.8 -m pip install -r requirements.txt