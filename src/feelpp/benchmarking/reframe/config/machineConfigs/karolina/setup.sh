#!/bin/bash -l


echo "==========================="
it4ifsusage
echo "==========================="


module load Python/3.10.4-GCCcore-11.3.0
export LD_LIBRARY_PATH=/apps/all/Python/3.10.4-GCCcore-11.3.0/lib:$LD_LIBRARY_PATH
python3.10 -m venv .venv
echo 'export LD_LIBRARY_PATH=/apps/all/Python/3.10.4-GCCcore-11.3.0/lib:$LD_LIBRARY_PATH' >> .venv/bin/activate
source .venv/bin/activate
.venv/bin/python3.10 -m pip install --upgrade pip
.venv/bin/python3.10 -m pip install -r requirements.txt