# 🎓 ILIAS Portal

A full-stack industry-grade web application that provides a modern Angular frontend + Django REST Framework backend for managing courses on the **Ovidius ILIAS** system at the University of Tübingen.

## What it does

Users can:
1. **Register & Login** to the portal with their own account
2. **Save ILIAS credentials** (Tübingen university `zx...` login)
3. **Refresh and view all their ILIAS courses** with a single click
4. **Browse course contents** — see all sections, files, exercises, etc.
5. **Download files** directly from the portal
6. **Publish assignments** (Übungen) to any course they moderate
7. **Find and safely edit existing exercises** (content, title, and deadline)
8. **Upload lecture slides** (creates a folder and uploads files)
9. **Post announcements** (news items) to the course timeline

## Architecture

```
ilias_portal/
├── backend/        # Django REST Framework API
│   ├── config/     # Django settings, urls, wsgi
│   └── apps/
│       ├── accounts/  # User auth + ILIAS credential storage
│       └── ilias/     # Course data + ILIAS operations
└── frontend/       # Angular 17 SPA
    └── src/
        └── app/
            ├── core/       # Services, guards, models
            ├── features/   # Pages (login, courses, course-detail, etc.)
            └── shared/     # Navbar and other shared components
```

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Angular 17 (standalone components) |
| Backend | Django 4.2 + Django REST Framework 3.15 |
| Auth | JWT (SimpleJWT) — 24h access / 7d refresh |
| Database | PostgreSQL |
| ILIAS scraping | `requests` + `BeautifulSoup4` (headless Shibboleth SSO) |

## Quick Start

### Backend

```bash
cd backend

# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials + SECRET_KEY

# 4. Create database (PostgreSQL must be running)
createdb ilias_portal

# 5. Run migrations
python manage.py migrate

# 6. Create superuser (optional)
python manage.py createsuperuser

# 7. Start server
python manage.py runserver
# → http://localhost:8000
```

### Frontend

```bash
cd frontend

# 1. Install Node dependencies
npm install

# 2. Start dev server
npm start
# → http://localhost:4200
```

## API Endpoints

### Auth
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/login/` | Get JWT tokens |
| POST | `/api/auth/refresh/` | Refresh access token |
| POST | `/api/auth/register/` | Create account |
| GET/PATCH | `/api/auth/profile/` | View/update profile |
| GET/POST/PUT | `/api/auth/ilias-credentials/` | Manage ILIAS credentials |

### ILIAS
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/ilias/courses/` | List cached courses |
| POST | `/api/ilias/courses/refresh/` | Login to ILIAS, fetch fresh course list |
| GET | `/api/ilias/courses/<id>/contents/` | Get course sections + items |
| GET | `/api/ilias/courses/<id>/items/search/?q=<query>` | Find live course items and exact URLs |
| PATCH | `/api/ilias/courses/<id>/items/exercise/` | Edit and verify an exact exercise |
| GET | `/api/ilias/courses/<id>/grades/target/` | Resolve one exact participant's current assignment grade |
| POST | `/api/ilias/courses/<id>/grades/` | Post and verify instructor-supplied grade fields |
| POST | `/api/ilias/courses/<id>/publish/assignment/` | Create exercise + assignment |
| POST | `/api/ilias/courses/<id>/publish/slides/` | Create folder + upload files |
| POST | `/api/ilias/courses/<id>/publish/announcement/` | Post news item |
| GET | `/api/ilias/download/?url=<encoded>` | Proxy file download from ILIAS |

## Environment Variables

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DB_NAME=ilias_portal
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

## Security Notes

- ILIAS credentials are stored plaintext in PostgreSQL — for production, add field-level encryption (e.g., `django-encrypted-fields`)
- CORS is wide-open for development — restrict `CORS_ALLOWED_ORIGINS` in production
- Use HTTPS in production and set `DEBUG=False`
- Grade posting requires exact target discovery, current-value guards, explicit
  instructor confirmation, a single write, and post-write verification. Agents
  must never calculate, recommend, infer, or choose a student's grade.
