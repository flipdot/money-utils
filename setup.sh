#!/bin/bash
set -euxo pipefail

SERVICE_PATH=$HOME/.config/systemd/user/
SERVICE=money.service
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

ENV=.env
PIP=$ENV/bin/pip

make_venv() {
    [[ -x $PIP ]] || python3 -m venv $ENV
    $PIP install wheel # is needed for uWSGI
    $PIP install -r requirements.txt
}

install_service() {
    mkdir -p "$SERVICE_PATH"

    sed "s#DIR#${DIR}#g" "$SERVICE" > "$SERVICE_PATH/$SERVICE"
    systemctl --user daemon-reload
    #systemctl --user enable --now "$SERVICE"
}

make_venv
install_service
