# Cleaning for avoiding interactions
rm -rf ~/feelppdb
rm -rf ./build/reframe/output/ ./build/reframe/stage/ ./build/reframe/perflogs


# Hostname must be provided as argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <hostname>"
    exit 1
fi
hostname=$1


# Reframe environment variables
export RFM_CONFIG_FILES=$(pwd)/src/feelpp/benchmarking/reframe/cluster-config/${hostname}.py
export RFM_PREFIX=$(pwd)/build/reframe/


export BENCH_CASES_CFG=$(pwd)/src/feelpp/benchmarking/cases/
columns=$(tput cols)
current_date=$(date +%Y%m%d)


find $BENCH_CASES_CFG -type f -name "*.cfg" | while read cfgPath
do
    echo
    yes '-' | head -n "$columns" | tr -d '\n'
    casename=$(basename $cfgPath)
    echo "[Launching ReFrame with $casename]"
    casename=${casename%-bench.cfg}
    export RFM_REPORT_FILE=$(pwd)/docs/modules/${hostname}/pages/reports/${casename}-${current_date}.json.json
    reframe -c ./regression-tests/heatTest.py -S case=$cfgPath -r --system=$hostname --exec-policy=serial
done