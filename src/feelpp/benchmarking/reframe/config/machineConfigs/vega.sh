#!/bin/bash -l

module load Python/3.10.8-GCCcore-12.2.0
export LD_LIBRARY_PATH=/cvmfs/sling.si/modules/el7/software/Python/3.10.8-GCCcore-12.2.0/lib:$LD_LIBRARY_PATH
python3.10 -m venv .venv
echo 'export LD_LIBRARY_PATH=/cvmfs/sling.si/modules/el7/software/Python/3.10.8-GCCcore-12.2.0/lib:$LD_LIBRARY_PATH' >> .venv/bin/activate
source .venv/bin/activate
.venv/bin/python3.10 -m pip install --upgrade pip
.venv/bin/python3.10 -m pip install -r requirements.txt