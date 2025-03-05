#!/usr/bin/env bash

python3 -m venv .venv
source .venv/bin/activate

pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 wheel --no-deps --wheel-dir dist .
pip3 install dist/*.whl
npm i
source ./girder_deploy_config.sh
if [[ $HEAD == *"new-benchmark"* ]]; then
    echo "Downloading Staging benchmarks"
    feelpp-girder download -gid $staging_folder_id -o ./tmp/ -d
    merge-json-configs -fp "./tmp/**/website_config.json" -o ./tmp/website_config.json -u
else
    echo "Downloading Production benchmarks"
    feelpp-girder download -gid $production_website_config_id -o ./tmp/ -fn website_config.json
fi
feelpp-benchmarking-render --config-file=./tmp/website_config.json
npx antora --stacktrace generate --cache-dir cache --clean --html-url-extension-style=indexify site.yml
