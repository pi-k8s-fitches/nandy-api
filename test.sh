#!/usr/bin/env sh

until nc -zw3 mysql 3306; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

echo "All services up"

coverage run -m unittest discover -v test && coverage report -m
