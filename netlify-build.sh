#!/usr/bin/env bash

python3 -m venv .venv
source .venv/bin/activate

pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 wheel --no-deps --wheel-dir dist .
pip3 install dist/*.whl
npm i
if [[ $BRANCH != *"new-benchmark"* ]]; then
    config_id=6752f0734c9ccbdde21a48ca
    girder-download --girder_id=$config_id --output_dir=./tmp/ --filename=website_config.json
fi
render-benchmarks --config_file=./tmp/website_config.json
npx antora --stacktrace generate --cache-dir cache --clean --html-url-extension-style=indexify site.yml
