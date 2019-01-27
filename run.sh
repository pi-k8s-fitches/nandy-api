#!/usr/bin/env sh

until nc -zw3 mysql 3306; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

nandy-data/mysql/load.py
bin/api.py