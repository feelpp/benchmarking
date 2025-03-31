#!/bin/bash -l

echo "================================================"
sacctmgr show association where account=$PROJECT_ID

sshare -A $PROJECT_ID -u " " -o account,user,GrpTRESRaw%80,GrpTRESMins,RawUsage

lfs quota -g $PROJECT_ID /discofs
lfs quota -g $PROJECT_ID /disco2fs
echo "==============================================="


/opt/software/python/3.9.7/bin/python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python3.9 -m pip install --upgrade pip
.venv/bin/python3.9 -m pip install -I -r requirements.txt
