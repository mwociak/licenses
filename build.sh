#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- Starting build script ---"

echo "--- Installing packages ---"
pip install -r requirements.txt

echo "--- Running collectstatic ---"
python manage.py collectstatic --no-input

echo "--- Checking for existing migrations ---"
ls -R myapp/migrations/

echo "--- Running migrate command with verbosity ---"
python manage.py migrate --verbosity 3

echo "--- Build script finished ---"
