#!/bin/bash
set -e

rm -f db.sqlite3

python manage.py makemigrations sentinelapi
python manage.py migrate
python manage.py loaddata users
python manage.py loaddata tokens
python manage.py loaddata instructors
python manage.py loaddata students
python manage.py loaddata courses
python manage.py loaddata enrollments
python manage.py loaddata assessment_types
python manage.py loaddata course_assessment_types
