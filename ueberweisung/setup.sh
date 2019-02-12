#!/bin/bash
set -euxo pipefail

rm -rf .env
mkdir .env
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt

