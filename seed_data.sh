#!/bin/bash
set -e

rm -rf sentinelapi/migrations
rm -f db.sqlite3

python manage.py makemigrations sentinelapi
python manage.py migrate
python manage.py loaddata users
python manage.py loaddata tokens
