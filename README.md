# Billy-in

Billy-in is a premium, multi-business invoicing and lightweight financial operations platform for a single administrator. It helps manage several businesses from one workspace while keeping financial records, customer relationships, and document workflows organized and auditable.

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: Django, Django REST Framework
- Database: SQLite for local development, PostgreSQL-ready configuration for production
- PDF generation: server-side document rendering via Django views or a PDF library

## Project structure

```
.
├── backend/
│   ├── billyin/
│   ├── accounts/
│   ├── businesses/
│   ├── customers/
│   ├── documents/
│   ├── payments/
│   ├── reporting/
│   ├── requirements.txt
│   ├── manage.py
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   └── DEVELOPMENT_ROADMAP.md
├── .env.example
├── .gitignore
├── README.md
└── ...
```

## Local setup

### 1. Backend

```bash
cd backend
python -m venv .venv
. .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://localhost:8000`.

## Environment

Create a local environment file from the root `.env.example` and set values such as:

```bash
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=sqlite3
DATABASE_NAME=db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000
```

## Database setup

- Local development defaults to SQLite.
- Production can be configured for PostgreSQL by setting the proper environment values.

```bash
python manage.py makemigrations
python manage.py migrate
```

## Tests

```bash
python manage.py test
```

## Notes

This is an initial working foundation for business and customer management, document architecture, and dashboard reporting. Additional features can be layered in as the product matures.
