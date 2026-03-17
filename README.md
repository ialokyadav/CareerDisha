# Resume Parser AI

Resume Parser AI is a full-stack career intelligence platform that parses resumes, extracts skills, predicts job roles, identifies skill gaps, generates adaptive assessments, and builds role-based learning roadmaps.

## Overview

The project combines a Django REST backend, a React frontend, MongoDB for document data, SQLite for Django auth/admin data, and machine learning models stored locally under `backend/ml_engine/models/`.

Core workflows:

- User registration, login, profile, and password reset with OTP
- Resume upload for `.pdf`, `.docx`, and `.txt` files
- Resume text parsing for keywords, contact details, and education signals
- Skill extraction and job role prediction using trained ML artifacts
- Skill-gap analysis against a selected target role
- Adaptive assessment generation and submission tracking
- Personalized roadmap generation with phase-based progress
- Analytics snapshots for current skills and learning progress
- Admin utilities for question bank management, retraining, and data operations

## Architecture

### Frontend

- React 18 with Vite
- React Router for page-level navigation
- JWT stored in `localStorage`
- API client in `frontend/src/api/client.js`

Main pages include dashboard, resume upload, role prediction, skill gap analysis, roadmap, analytics, test center, login, register, and admin dashboard.

### Backend

- Django 4 + Django REST Framework
- JWT authentication via `djangorestframework-simplejwt`
- SQLite for Django-managed data
- MongoDB for resumes, extractions, tests, analytics, roadmaps, and related app data
- WhiteNoise + Gunicorn for production serving

Backend apps:

- `users`: registration, profile, forgot-password OTP flow
- `resumes`: resume ingestion, parsing, extraction, manual inputs, admin data actions
- `assessments`: question bank, adaptive test generation, submission evaluation
- `analytics`: dashboard snapshot, history, skill accuracy summary
- `roadmap`: role roadmap generation and progress tracking
- `ml_engine`: model training, prediction, retraining, and skill-gap logic

### Data Flow

1. A user uploads a resume or submits manual text/skills.
2. The backend extracts raw text, normalizes it, and derives keywords, education, and contact info.
3. The ML layer predicts skills and optionally predicts a likely role.
4. Skill-gap analysis compares current skills against a selected role.
5. The platform can generate assessments and learning roadmaps from those results.
6. Assessment outcomes feed analytics and roadmap progress updates.

## Repository Structure

```text
.
|-- backend/
|   |-- analytics/
|   |-- assessments/
|   |-- common/
|   |-- config/
|   |-- ml_engine/
|   |-- resumes/
|   |-- roadmap/
|   `-- users/
|-- frontend/
|   |-- public/
|   `-- src/
|-- docker-compose.yml
|-- render.yaml
`-- run_app.sh
```

## Prerequisites

- Python 3.11 or newer recommended
- Node.js 20 or newer recommended
- npm
- MongoDB running locally or a hosted MongoDB URI

## Environment Variables

Create a `.env` file from `.env.example` or export the variables manually.

Backend variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `ALLOWED_HOSTS`
- `MONGODB_URI`
- `MONGODB_DB`
- `CORS_ALLOWED_ORIGINS`
- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `DEFAULT_FROM_EMAIL`

Frontend variable:

- `VITE_API_BASE_URL`

Example backend values are provided in `.env.example`.

## Local Setup

### 1. Clone and enter the project

```bash
git clone <your-repository-url>
cd "Resume parser AI"
```

### 2. Create a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Start MongoDB

Make sure `mongod` is running locally, or point `MONGODB_URI` to your hosted database.

### 6. Apply Django migrations

```bash
cd backend
../.venv/bin/python manage.py migrate
cd ..
```

## Running the Project

### Option 1: Unified startup script

The repository includes `run_app.sh`, which starts the backend on port `8000` and then runs the Vite frontend.

```bash
chmod +x run_app.sh
./run_app.sh
```

### Option 2: Start services manually

Backend:

```bash
cd backend
source ../.venv/bin/activate
export DJANGO_DEBUG=1
python manage.py runserver 127.0.0.1:8000
```

Frontend:

```bash
cd frontend
npm run dev
```

Default local URLs:

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/`
- Django admin: `http://127.0.0.1:8000/admin/`

## Machine Learning Assets

The ML layer depends on model files already stored in the repository:

- `backend/ml_engine/models/skill_model.joblib`
- `backend/ml_engine/models/skill_vectorizer.joblib`
- `backend/ml_engine/models/role_model.joblib`
- `backend/ml_engine/models/role_vectorizer.joblib`
- `backend/ml_engine/models/skill_mlb.joblib`
- `backend/ml_engine/models/role_mlb.joblib`

Supporting datasets and configuration live under `backend/ml_engine/datasets/`.

## API Summary

### Authentication

- `POST /api/auth/register/`
- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `GET /api/auth/profile/`
- `POST /api/auth/forgot-password/request-otp/`
- `POST /api/auth/forgot-password/verify-otp/`

### Resume and ML Features

- `POST /api/resumes/upload/`
- `POST /api/resumes/manual-text/`
- `POST /api/resumes/manual-skills/`
- `POST /api/resumes/predict-role/`
- `POST /api/resumes/skill-gap/`
- `GET /api/resumes/latest-extraction/`
- `GET /api/resumes/training-status/`
- `GET /api/resumes/engine-config/`
- `POST /api/resumes/engine-config/`

### Assessments

- `POST /api/assessments/generate/`
- `POST /api/assessments/submit/`
- `GET /api/assessments/roles/`
- `POST /api/assessments/questions/seed/`
- `GET /api/assessments/questions/`

### Analytics

- `GET /api/analytics/`
- `GET /api/analytics/dashboard/`
- `GET /api/analytics/history/`
- `GET /api/analytics/summary/`

### Roadmaps

- `POST /api/roadmap/generate/`
- `GET /api/roadmap/progress/`

### Admin-Oriented Operations

- `GET /api/resumes/admin-user-contacts/`
- `POST /api/resumes/add-manual-data/`
- `POST /api/resumes/admin-retrain/`

Most API routes require a Bearer token except registration, token issuance, and password-reset endpoints.

## Supported Resume Formats

The upload pipeline currently accepts:

- `.pdf`
- `.docx`
- `.txt`

## Storage Model

### SQLite

Used by Django for:

- authentication
- admin access
- core relational framework data

### MongoDB

Used for application documents such as:

- resumes
- skill extractions
- role predictions
- skill gaps
- tests and attempts
- question bank
- roadmap and roadmap progress
- user profile snapshots
- OTP records

## Deployment

### Docker Compose

The repository includes `docker-compose.yml` with three services:

- `mongodb`
- `backend`
- `frontend`

Run:

```bash
docker compose up --build
```

### Render

The repository includes `render.yaml` for deploying the backend as a Python web service with Gunicorn and static collection.

### Frontend Hosting

The frontend is configured with Vite and includes `frontend/vercel.json`, making it suitable for Vercel-style static deployment after build output generation.

## Operational Notes

- The backend root path returns a health response.
- Static files are served with WhiteNoise in production.
- CORS defaults include local frontend origins and can be overridden with `CORS_ALLOWED_ORIGINS`.
- Password reset emails use Django email settings and default to console email output unless configured otherwise.
- Resume upload can trigger background retraining checks when new role-labeled data is collected.

## Admin Access

Create a superuser for Django admin:

```bash
cd backend
../.venv/bin/python manage.py createsuperuser
```

Then sign in at `/admin/`.

## License

Add your preferred license information here if this repository is intended for distribution.
