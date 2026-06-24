# Sentinel Matrix Server

Sentinel Matrix is a student-risk dashboard for instructors. The goal is to help instructors manage courses, students, enrollments, assessments, and risk indicators from one focused interface.

This repository is the **Django + Django REST Framework backend API** for the project. It powers authentication, domain data, and risk-related endpoints consumed by the frontend client.

---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/DRF-A30000?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

---

## Related Repository

| Repo | Description |
| --- | --- |
| [Sentinel Matrix Client](https://github.com/DaleHobbs-Dev/sentinel-matrix-client) | Vite + React frontend |

---

## Current Project Structure

```txt
sentinel-matrix-server/
├── sentinelapi/
│   ├── fixtures/                  # Seed JSON for instructors, courses, students, and related data
│   ├── migrations/                # Django migrations
│   ├── models/                    # Domain models
│   ├── tests/                     # API and auth test modules
│   └── views/                     # Endpoint view modules
├── sentinelproject/               # Django project settings and URL config
├── apidoc.json                    # API documentation metadata
├── manage.py                      # Django management entry point
├── requirements.txt               # Python dependencies
├── seed_data.sh                   # Local seed script
└── pull_request_template.md       # Pull request template
```

---

## Documentation

Project documentation currently lives in root-level backend files:

| File | Description |
| --- | --- |
| [apidoc.json](apidoc.json) | API documentation metadata for the backend service |
| [seed_data.sh](seed_data.sh) | Local script for loading fixture data |

As the project grows, additional planning docs can live under a dedicated `dev-docs/` folder.

---

## MVP Goals

The planned MVP focuses on instructor workflows:

- **Authentication** - register, log in, issue auth credentials, and secure endpoints
- **Courses** - create and manage instructor-owned courses
- **Students** - add and manage students
- **Enrollments** - connect students to courses
- **Assessments** - record assessment data for enrolled students
- **Risk Scoring** - calculate and expose student risk scores and risk bands
- **API Foundation** - provide stable endpoints for the Sentinel Matrix client

---

## Setup & Installation

### Prerequisites

- [Python](https://www.python.org/) 3.10+
- `pip`
- Ubuntu package support for virtual environments (`python3-venv`)

### First-Time Ubuntu Setup

If this machine has not been used for Python virtual environments yet, run:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip
```

### Steps

1. Clone the repository:

	```bash
	git clone git@github.com:DaleHobbs-Dev/sentinel-matrix-server.git
	cd sentinel-matrix-server
	```

2. Create the virtual environment:

	```bash
	python3 -m venv sentinel-env
	```

3. Activate the virtual environment:

	```bash
	source sentinel-env/bin/activate
	```

4. Upgrade packaging tools (recommended):

	```bash
	python -m pip install --upgrade pip setuptools wheel
	```

5. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

6. Apply migrations:

	```bash
	python manage.py migrate
	```

7. Seed the database:

	```bash
	./seed_data.sh
	```

8. Start the development server:

	```bash
	python manage.py runserver
	```

The API is available locally at:

```txt
http://localhost:8000
```

---

## Available Scripts

```bash
python manage.py runserver      # Start the Django dev server
python manage.py migrate        # Apply database migrations
python manage.py test           # Run test suite
./seed_data.sh                  # Load fixture seed data
```

---

## Development Notes

- Active endpoint work should live in `sentinelapi/views/`.
- Authentication routes should live in `sentinelapi/views/auth.py`.
- Model-specific endpoint logic should stay in matching modules under `sentinelapi/views/`.
- Tests should live in `sentinelapi/tests/` and grow alongside endpoint work.
- Fixtures in `sentinelapi/fixtures/` should remain the source for local seed data.

---

## Contributor

| Name | GitHub |
| --- | --- |
| Dale Hobbs | [@DaleHobbs-Dev](https://github.com/DaleHobbs-Dev) |
