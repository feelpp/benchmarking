# Cleaning for avoiding interactions
rm -rf ~/feelppdb
rm -rf ./build/reframe/output/ ./build/reframe/stage/ ./build/reframe/perflogs


# Hostname must be provided as argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <hostname>"
    exit 1
fi
hostname=$1             # Arguments handling to be improved


# Reframe environment variables
export RFM_CONFIG_FILES=$(pwd)/src/feelpp/benchmarking/reframe/cluster-config/${hostname}.py
export RFM_PREFIX=$(pwd)/build/reframe/

disk_path="/home"
#disk_path="/data/home"
#disk_path="/data/scratch/"
#disk_path="/nvme0/"
toolbox="heat"


export RFM_TEST_DIR=$(pwd)/src/feelpp/benchmarking/reframe/regression-tests/
export FEELPP_TOOLBOXES_CASES=/usr/share/feelpp/data/testcases/toolboxes/${toolbox}/cases/
export FEELPP_OUTPUT_PREFIX="${disk_path}/${USER}/feelppdbTANGUYYYY"


columns=$(tput cols)
current_date=$(date +%Y%m%d)

find $FEELPP_TOOLBOXES_CASES -type f -name "*.cfg" | while read cfgPath
do
    yes '-' | head -n "$columns" | tr -d '\n'

    relative_path=${cfgPath#"$FEELPP_TOOLBOXES_CASES"}
    relative_dir=$(dirname "$relative_path")
    base_name=$(basename "${relative_path%.cfg}")

    report_path=$(pwd)/docs/modules/${hostname}/pages/reports/${toolbox}/${relative_dir}/${current_date}-${base_name}.json

    echo "[Launching $relative_path on $hostname]"
    reframe -c $RFM_TEST_DIR/${toolbox}Test.py -S case=$cfgPath -r --system=$hostname --report-file=$report_path
done