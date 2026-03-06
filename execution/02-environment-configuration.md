# Environment Configuration

Guide for configuring environment variables, secrets, and AWS services for Oracy AI.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Environment Files](#environment-files)
3. [Required Variables](#required-variables)
4. [AWS Configuration](#aws-configuration)
5. [AI/ML Service Keys](#aiml-service-keys)
6. [Database Configuration](#database-configuration)
7. [Security Settings](#security-settings)
8. [Environment-Specific Configs](#environment-specific-configs)

---

## Configuration Overview

Oracy AI uses environment-specific configuration files and `.env` files for secrets. Never commit secrets to version control.

```
config/
├── settings/
│   ├── base.py          # Shared settings
│   ├── development.py   # Local development
│   ├── staging.py       # Staging environment
│   └── production.py    # Production environment
└── .env                 # Secrets (gitignored)
```

---

## Environment Files

### 1. Create `.env` File

Create `server/config/.env`:

```bash
cd server/config

# Copy template
copy .env.example .env        # Windows
# OR
cp .env.example .env          # macOS/Linux
```

### 2. `.env` Template

```env
# ============================================
# Oracy AI - Environment Configuration
# ============================================

# --------------------------------------------
# Django Core
# --------------------------------------------
DJANGO_SECRET_KEY=your-super-secret-key-here-min-50-chars-long-dev-only
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# --------------------------------------------
# Database (PostgreSQL)
# --------------------------------------------
DATABASE_URL=postgres://oracy:oracy_dev@localhost:5432/oracy_db
# OR individual vars:
DB_NAME=oracy_db
DB_USER=oracy
DB_PASSWORD=oracy_dev
DB_HOST=localhost
DB_PORT=5432

# --------------------------------------------
# Redis / Cache
# --------------------------------------------
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# --------------------------------------------
# AWS Configuration
# --------------------------------------------
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-southeast-1
AWS_S3_BUCKET_NAME=oracy-dev-uploads
AWS_S3_REGION_NAME=ap-southeast-1

# --------------------------------------------
# AI/ML Services (V2 - Cost-Optimized)
# --------------------------------------------

# STT Provider: RunPod Serverless GPU (WhisperX)
RUNPOD_API_KEY=your-runpod-api-key
RUNPOD_ENDPOINT_ID=your-endpoint-id

# Alternative STT: Local WhisperX (development)
WHISPER_MODEL=distil-large-v3  # or 'base' for CPU
WHISPER_DEVICE=cuda  # or 'cpu' for local dev
WHISPER_COMPUTE_TYPE=int8  # int8 for VRAM reduction

# LLM Provider: OpenRouter (aggregates multiple providers)
OPENROUTER_API_KEY=sk-or-v1-...

# LiteLLM Configuration
LITELLM_MODEL=openrouter/google/gemini-flash-1.5
LITELLM_FALLBACK_MODELS=openrouter/anthropic/claude-3.5-haiku,openrouter/openai/gpt-4o-mini

# Optional: Local Ollama (zero-cost fallback)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# --------------------------------------------
# Email (SMTP)
# --------------------------------------------
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@oracy.ai

# --------------------------------------------
# Frontend URL (for CORS)
# --------------------------------------------
FRONTEND_URL=http://localhost:5173
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# --------------------------------------------
# JWT Settings
# --------------------------------------------
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# --------------------------------------------
# Logging
# --------------------------------------------
LOG_LEVEL=DEBUG
LOG_FORMAT=console

# --------------------------------------------
# Feature Flags
# --------------------------------------------
ENABLE_AI_PIPELINE=True
ENABLE_WEBSOCKET=True
ENABLE_ANALYTICS=False
```

---

## Required Variables

### Minimum Required for Development

| Variable | Purpose | Example |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | Django security | Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DATABASE_URL` | Database connection | `postgres://user:pass@host:5432/db` |
| `REDIS_URL` | Cache & Celery broker | `redis://localhost:6379/0` |
| `RUNPOD_API_KEY` | STT service (WhisperX) | Get from runpod.io |
| `RUNPOD_ENDPOINT_ID` | RunPod serverless endpoint | `abc123-def456-...` |
| `OPENROUTER_API_KEY` | LLM service (multi-provider) | Get from openrouter.ai |

**V2 Changes:**
- ❌ Removed: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- ✅ Added: `RUNPOD_API_KEY`, `OPENROUTER_API_KEY`
- 💰 Savings: ~80% reduction in AI costs
| `AWS_ACCESS_KEY_ID` | S3 & Transcribe | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS auth | `...` |

### Generate Django Secret Key

```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Output example:
# x9v2KjLmN8pQr5sTu7vWx3yZa4Bc6De9Fg1Hi3Jk5Mn7Pq9Rs2Tu4Vw6Xy8Za3Bc
```

---

## AWS Configuration

### 1. AWS CLI Setup

```bash
# Configure AWS CLI
aws configure

# Enter:
# AWS Access Key ID: [your key]
# AWS Secret Access Key: [your secret]
# Default region: ap-southeast-1
# Default output: json

# Verify
aws sts get-caller-identity
```

### 2. Required AWS Services

| Service | Purpose | Setup Required |
|---------|---------|----------------|
| S3 | Video/audio storage | Bucket + IAM policy |
| RDS | PostgreSQL database | Instance or use local |
| ElastiCache | Redis cache | Cluster or use local |
| Transcribe | Speech-to-text | Service enabled |
| ECS | Container deployment | Cluster + Task definitions |
| CloudWatch | Logging & monitoring | Enabled by default |

### 3. S3 Bucket Policy

Create bucket `oracy-dev-uploads` with this CORS policy:

```json
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST"],
            "AllowedOrigins": ["http://localhost:5173", "https://staging.oracy.ai"],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3000
        }
    ]
}
```

### 4. IAM Policy for Application

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::oracy-dev-uploads",
                "arn:aws:s3:::oracy-dev-uploads/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "transcribe:StartTranscriptionJob",
                "transcribe:GetTranscriptionJob",
                "transcribe:ListTranscriptionJobs"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

---

## AI/ML Service Keys

### OpenAI

1. Visit https://platform.openai.com/api-keys
2. Create new API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

**Models Used:**
- `gpt-4o-transcribe` - Speech-to-text
- `gpt-4o` - LLM scoring

### Anthropic Claude (Optional)

1. Visit https://console.anthropic.com/
2. Generate API key
3. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

**Model Used:**
- `claude-3-5-sonnet-20241022` - Alternative LLM scoring

### AWS Transcribe (Optional)

Uses AWS credentials. Enable with `USE_AWS_TRANSCRIBE=True`.

---

## Database Configuration

### Local Development (Docker)

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: oracy_db
      POSTGRES_USER: oracy
      POSTGRES_PASSWORD: oracy_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### Connection URL Format

```
postgres://USER:PASSWORD@HOST:PORT/DB_NAME

# Examples:
# Local Docker
postgres://oracy:oracy_dev@localhost:5432/oracy_db

# AWS RDS
postgres://oracy_user:secure_pass@oracy-db.abc123.ap-southeast-1.rds.amazonaws.com:5432/oracy_prod
```

### Verify Connection

```bash
# Using psql
psql $DATABASE_URL

# Or test from Django
cd server
python manage.py dbshell
```

---

## Security Settings

### Development

```env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=[development-key-only]
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Staging

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=[strong-random-key]
DJANGO_ALLOWED_HOSTS=staging.oracy.ai
CORS_ALLOWED_ORIGINS=https://staging.oracy.ai
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Production

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=[strong-random-key-min-50-chars]
DJANGO_ALLOWED_HOSTS=app.oracy.ai,oracy.ai
CORS_ALLOWED_ORIGINS=https://app.oracy.ai
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY
```

---

## Environment-Specific Configs

### Development (`config/settings/development.py`)

```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='oracy_db'),
        'USER': env('DB_USER', default='oracy'),
        'PASSWORD': env('DB_PASSWORD', default='oracy_dev'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Use console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### Production (`config/settings/production.py`)

```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS')

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Database via URL
DATABASES = {
    'default': env.db()
}

# S3 Storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# Logging to CloudWatch
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'cloudwatch': {
            'class': 'watchtower.CloudWatchLogHandler',
            'log_group': 'oracy-production',
            'stream_name': 'django',
        },
    },
    'root': {
        'handlers': ['cloudwatch'],
        'level': 'INFO',
    },
}
```

---

## Verification

### Test Configuration

```bash
cd server

# Check settings load
python manage.py check

# Verify database
python manage.py dbshell
\conninfo  # Shows connection info
\q         # Quit

# Verify environment variables
python manage.py shell
>>> from django.conf import settings
>>> print(settings.DATABASES)
>>> print(settings.ALLOWED_HOSTS)
>>> exit()
```

### Test External Services

```bash
# Test OpenAI
python -c "import openai; print(openai.__version__)"

# Test AWS
aws s3 ls s3://oracy-dev-uploads

# Test Redis
redis-cli ping  # Should return PONG
```

---

## Secrets Management (Production)

For production, use AWS Secrets Manager or Parameter Store:

```bash
# Store secret in AWS Secrets Manager
aws secretsmanager create-secret \
    --name oracy/production/django \
    --secret-string file://secrets.json

# Reference in ECS task definition
"secrets": [
    {
        "name": "DJANGO_SECRET_KEY",
        "valueFrom": "arn:aws:secretsmanager:...:secret:oracy/production/django:DJANGO_SECRET_KEY::"
    }
]