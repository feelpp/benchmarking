#!/bin/bash -l

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/hpc.env"

source /etc/profile.d/modules.sh
export MODULEPATH=/opt/software/modulefiles

echo "================================================"
sacctmgr show association where account=$discoverer_project_id

sshare -A $discoverer_project_id -u " " -o account,user,GrpTRESRaw%80,GrpTRESMins,RawUsage

lfs quota -g $discoverer_project_id /discofs
lfs quota -g $discoverer_project_id /disco2fs
echo "==============================================="


/opt/software/python/3.9.7/bin/python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python3.9 -m pip install --upgrade pip
.venv/bin/python3.9 -m pip install -I -r requirements.txt
