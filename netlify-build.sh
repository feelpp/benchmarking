#!/usr/bin/env bash

python3 -m venv .venv
source .venv/bin/activate

pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 wheel --no-deps --wheel-dir dist .
pip3 install dist/*.whl
npm i
render-benchmarks
npx antora --stacktrace generate --cache-dir cache --clean --html-url-extension-style=indexify site.yml
