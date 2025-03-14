#!/bin/bash -l


echo "==========================="
it4ifsusage
echo "==========================="


/apps/all/Python/3.10.4-GCCcore-11.3.0/bin/python -m venv .venv
source .venv/bin/activate
.venv/bin/python3.10 -m pip install --upgrade pip
.venv/bin/python3.10 -m pip install -r requirements.txt