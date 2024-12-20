#!/bin/bash -l

# module load Python/3.12.3-GCCcore-13.3.0


/cvmfs/sling.si/modules/el7/software/Python/3.12.3-GCCcore-13.3.0/bin/python -m venv .venv
source .venv/bin/activate
.venv/bin/python3.12 -m pip install --upgrade pip
.venv/bin/python3.12 -m pip install -r requirements.txt