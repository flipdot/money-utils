#!/bin/bash
set -euxo pipefail

mkdir -p backups

sqlite3 data/money.sqlite .dump > backups/backup.sql

cd backups
git init
git add -A
git commit --no-verify -am "Backup $(date)"

