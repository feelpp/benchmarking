#!/bin/bash -l


echo "==========================="
myquota
echo "==========================="

python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python3 -m pip install --upgrade pip
.venv/bin/python3 -m pip install -r requirements.txt