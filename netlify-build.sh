#!/usr/bin/env bash

python3 -m venv .venv
source .venv/bin/activate

pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 wheel --no-deps --wheel-dir dist .
pip3 install dist/*.whl
npm i
if [[ $BRANCH == *"new-benchmark"* ]]; then
    config_id=6752f0734c9ccbdde21a48ca
    girder-download -gid $config_id -o ./tmp/ -d
    merge-json-configs -fp ./tmp/**/website_config.json -o ./tmp/website_config.json -u
else
    config_id=6752f0734c9ccbdde21a48ca
    girder-download -gid $config_id -o ./tmp/ -fn website_config.json
fi
render-benchmarks --config_file=./tmp/website_config.json
npx antora --stacktrace generate --cache-dir cache --clean --html-url-extension-style=indexify site.yml
