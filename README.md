# Sentinel Matrix Server

Django REST API backend for Sentinel Matrix, a student risk dashboard application.

## Setup

Activate the virtual environment:

```bash
source sentinel-env/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Start server:

```bash
python manage.py runserver
```

Seed database:

```bash
./seed_data.sh
```
