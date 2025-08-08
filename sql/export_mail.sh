#!/bin/sh

sqlite3 data/money.sqlite <sql/members.sql | awk -F '|' 'NR != 1 {print $4}' | sort
