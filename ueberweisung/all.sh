#!/bin/sh

set -euo pipefail

ENV=../env
PYTHON=${ENV}/bin/python
ACTIVATE=${ENV}/bin/activate

if [[ -f ${PYTHON} ]]; then
    python3 -m venv ${ENV}
    source ${ACTIVATE}
    pip3 install -r requirements.txt
else
    source ${ACTIVATE}
fi

${PYTHON} load_transactions.py

${PYTHON} members.py

${PYTHON} report.py
