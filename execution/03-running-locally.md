# Running Locally

Complete guide for running the Oracy AI platform in local development mode.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Compose Method](#docker-compose-method-recommended)
3. [Manual Method](#manual-method)
4. [Frontend Development](#frontend-development)
5. [Backend Development](#backend-development)
6. [Background Workers](#background-workers)
7. [Accessing the Application](#accessing-the-application)
8. [Development Workflows](#development-workflows)

---

## Quick Start

```bash
# From project root
docker compose up -d

# Services will be available at:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/api/docs
```

---

## Docker Compose Method (Recommended)

### 1. Start All Services

```bash
# Start infrastructure services
docker compose up -d db redis

# Wait for database to be ready (10-15 seconds)
docker compose logs -f db
# Look for: "database system is ready to accept connections"

# Run migrations
docker compose run --rm backend python manage.py migrate

# Create superuser
docker compose run --rm backend python manage.py createsuperuser

# Start all services
docker compose up -d
```

### 2. Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Frontend   │  │   Backend   │  │   Celery Worker     │  │
│  │   (Vite)    │  │   (Django)  │  │   (Background)      │  │
│  │  :5173      │  │    :8000    │  │                     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                      │             │
│         └────────────────┼──────────────────────┘             │
│                          │                                    │
│         ┌────────────────┼────────────────┐                   │
│         │                │                │                   │
│         ▼                ▼                ▼                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ PostgreSQL  │  │    Redis    │  │   Celery    │           │
│  │    :5432    │  │   :6379     │  │    Beat     │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 3. View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery-worker

# Last 100 lines
docker compose logs --tail=100 backend
```

### 4. Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes database data)
docker compose down -v

# Stop specific service
docker compose stop frontend
```

### 5. Rebuild After Changes

```bash
# Rebuild specific service
docker compose up -d --build backend

# Rebuild all
docker compose up -d --build
```

---

## Manual Method

Use this when you need more control or are debugging specific components.

### Prerequisites

- PostgreSQL running locally or via Docker
- Redis running locally or via Docker
- Python virtual environment activated
- Node.js installed

### 1. Start Infrastructure

```bash
# Terminal 1: Start PostgreSQL and Redis
docker compose up -d db redis
```

### 2. Start Backend

```bash
# Terminal 2: Backend
cd server

# Activate virtual environment
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# Verify environment
echo $DJANGO_SETTINGS_MODULE  # Should be set or use default

# Run migrations (first time or after model changes)
python manage.py migrate

# Create superuser (first time only)
python manage.py createsuperuser
# Enter: admin / admin@oracy.ai / password

# Start development server
python manage.py runserver 0.0.0.0:8000

# Server will be at http://localhost:8000
```

### 3. Start Frontend

```bash
# Terminal 3: Frontend
cd client

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev

# Frontend will be at http://localhost:5173
```

### 4. Start Celery Workers

```bash
# Terminal 4: Celery Worker
cd server
source .venv/bin/activate  # or Windows equivalent

celery -A config worker -l info --pool=solo

# Terminal 5: Celery Beat (for scheduled tasks)
celery -A config beat -l info
```

---

## Frontend Development

### Hot Module Replacement (HMR)

The Vite dev server provides instant updates:

```bash
cd client
npm run dev
```

Changes to React components are reflected immediately without page refresh.

### Common Frontend Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Type check
npm run type-check

# Run tests
npm run test
```

### Frontend Environment Variables

Create `client/.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENVIRONMENT=development
```

### Proxy Configuration

Vite dev server automatically proxies API requests. Configuration in `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

---

## Backend Development

### Django Development Server

```bash
python manage.py runserver 0.0.0.0:8000

# With specific settings
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py runserver
```

### Django Shell

```bash
# Interactive shell with Django context
python manage.py shell

# Enhanced shell with IPython (if installed)
python manage.py shell -i ipython
```

### Common Management Commands

```bash
# Database migrations
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser

# Shell plus (with auto-imported models)
python manage.py shell_plus  # if django-extensions installed

# Run tests
python manage.py test
pytest

# Check for issues
python manage.py check
python manage.py check --deploy

# Collect static files
python manage.py collectstatic

# Generate API schema
python manage.py spectacular --file schema.yml
```

### Django Admin

Access at: http://localhost:8000/admin

```bash
# Create admin user
python manage.py createsuperuser

# Or promote existing user
python manage.py shell
>>> from apps.users.models import User
>>> u = User.objects.get(email='user@example.com')
>>> u.is_staff = True
>>> u.is_superuser = True
>>> u.save()
```

---

## Background Workers

### Celery Worker

Required for AI pipeline processing.

```bash
# Basic worker
celery -A config worker -l info

# Worker with solo pool (Windows-friendly)
celery -A config worker -l info --pool=solo

# Worker with concurrency
celery -A config worker -l info --concurrency=4

# Worker for specific queue
celery -A config worker -l info -Q ai_pipeline
```

### Celery Beat (Scheduler)

```bash
# Run scheduler
celery -A config beat -l info

# Run worker + beat together
celery -A config worker -l info --beat
```

### Monitor Celery

```bash
# Flower - Celery monitoring (if installed)
celery -A config flower --port=5555
# Access at http://localhost:5555

# Check task status in Django shell
python manage.py shell
>>> from celery.result import AsyncResult
>>> result = AsyncResult('task-id-here')
>>> result.status
>>> result.result
```

---

## Accessing the Application

### URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React application |
| Backend API | http://localhost:8000 | Django REST API |
| Admin Panel | http://localhost:8000/admin | Django admin |
| API Docs | http://localhost:8000/api/docs | Swagger/ReDoc |
| Health Check | http://localhost:8000/health | System health |

### Default Credentials

After creating superuser:
- **Username**: (email you entered)
- **Password**: (what you set)

### Testing API Endpoints

```bash
# Using curl - Get token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@oracy.ai","password":"yourpassword"}'

# Use token to access API
curl http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Development Workflows

### Adding a New API Endpoint

```bash
# 1. Add view in apps/your_app/views.py
# 2. Add URL in apps/your_app/urls.py
# 3. Include in config/urls.py
# 4. Test at http://localhost:8000/api/your-endpoint/
```

### Modifying Database Models

```bash
# 1. Edit models.py
# 2. Create migration
python manage.py makemigrations

# 3. Review migration
python manage.py sqlmigrate your_app 0001

# 4. Apply migration
python manage.py migrate

# 5. (Docker) Recreate containers if needed
docker compose up -d --build backend
```

### Testing AI Pipeline

```bash
# 1. Upload a video through frontend or API
# 2. Monitor Celery worker logs
# 3. Check database for results
python manage.py shell
>>> from apps.analysis.models import Recording
>>> r = Recording.objects.latest('created_at')
>>> r.status
>>> r.transcript
```

### Debugging

```bash
# Django debug mode
DJANGO_DEBUG=True python manage.py runserver

# Python debugger in code
import pdb; pdb.set_trace()

# Django logging
python manage.py runserver --verbosity=2

# Celery debug
celery -A config worker -l debug
```

---

## Useful Aliases

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# Oracy AI Development
alias oracy-up='cd /path/to/oracy && docker compose up -d'
alias oracy-down='cd /path/to/oracy && docker compose down'
alias oracy-logs='cd /path/to/oracy && docker compose logs -f'
alias oracy-backend='cd /path/to/oracy/server && source .venv/bin/activate && python manage.py runserver'
alias oracy-frontend='cd /path/to/oracy/client && npm run dev'
alias oracy-shell='cd /path/to/oracy/server && source .venv/bin/activate && python manage.py shell_plus'
alias oracy-migrate='cd /path/to/oracy/server && source .venv/bin/activate && python manage.py migrate'
alias oracy-test='cd /path/to/oracy/server && source .venv/bin/activate && pytest'
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker compose ps

# Restart database
docker compose restart db

# Check logs
docker compose logs db
```

### Celery Tasks Not Running

```bash
# Check Redis is running
redis-cli ping

# Restart worker
docker compose restart celery-worker

# Check worker logs
docker compose logs -f celery-worker