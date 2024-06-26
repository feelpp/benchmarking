# Cleaning for avoiding interactions
rm -rf ~/feelppdb
rm -rf ./build/reframe/output/ ./build/reframe/stage/ ./build/reframe/perflogs


# Variable TO BE SET to the actual HPC
hostname=gaya

current_date=$(date +%Y%m%d)
mkdir -p $(pwd)/docs/modules/${hostname}/pages/reports

export BENCH_CASES_CFG=$(pwd)/src/feelpp/benchmarking/cases/


# Reframe environment variables
export RFM_CONFIG_FILES=$(pwd)/src/feelpp/benchmarking/reframe/cluster-config/${hostname}.py
export RFM_REPORT_FILE=$(pwd)/docs/modules/${hostname}/pages/reports/${hostname}-${current_date}-{sessionid}.json
export RFM_PREFIX=$(pwd)/build/reframe/



reframe -c ./src/feelpp/benchmarking/reframe/regression-tests/heatTest.py -r --system=${hostname} --exec-policy=serial