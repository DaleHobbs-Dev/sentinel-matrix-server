#!/bin/bash
set -e

rm -f db.sqlite3

python manage.py makemigrations sentinelapi
python manage.py migrate
python manage.py loaddata users
python manage.py loaddata tokens
python manage.py loaddata instructors
