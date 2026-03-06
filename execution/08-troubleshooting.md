# Troubleshooting Guide

Common issues and solutions for Oracy AI development and deployment.

## Table of Contents

1. [Development Issues](#development-issues)
2. [Database Issues](#database-issues)
3. [AI Pipeline Issues](#ai-pipeline-issues)
4. [Deployment Issues](#deployment-issues)
5. [Performance Issues](#performance-issues)
6. [Quick Diagnostic Commands](#quick-diagnostic-commands)

---

## Development Issues

### Python Virtual Environment Problems

**Issue**: `ModuleNotFoundError` after activating venv

```bash
# Solution 1: Verify activation
which python  # Should show .venv path

# Solution 2: Reinstall dependencies
cd server
rm -rf .venv
uv venv .venv
source .venv/bin/activate  # or Windows equivalent
uv pip install -e ".[dev]"

# Solution 3: Check Python version
python --version  # Should be 3.12.x
```

**Issue**: `uv` command not found

```bash
# Reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"
```

### Node.js / Frontend Issues

**Issue**: `npm install` fails with EACCES

```bash
# Fix permissions (Linux/macOS)
sudo chown -R $(whoami) ~/.npm

# Or use npx without install
npx --yes create-vite@latest
```

**Issue**: Port 5173 already in use

```bash
# Find and kill process
# macOS/Linux
lsof -ti:5173 | xargs kill -9

# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Or use different port
npm run dev -- --port=5174
```

**Issue**: Vite HMR not working

```bash
# Clear cache
rm -rf node_modules/.vite

# Restart dev server
npm run dev

# Check browser console for WebSocket errors
```

### Docker Issues

**Issue**: `Cannot connect to the Docker daemon`

```bash
# Start Docker Desktop (Windows/macOS)
# Or on Linux:
sudo systemctl start docker

# Check Docker status
docker info
```

**Issue**: Container fails to start with port conflict

```bash
# Check what's using the port
docker ps  # List running containers

# Stop conflicting container
docker stop <container_id>

# Or change ports in docker-compose.yml
```

**Issue**: Permission denied when accessing mounted volumes

```bash
# Fix volume permissions
# Linux/macOS:
sudo chown -R $USER:$USER .

# Or in docker-compose.yml, add:
services:
  backend:
    user: "${UID}:${GID}"
```

---

## Database Issues

### Connection Issues

**Issue**: `psycopg2.OperationalError: connection refused`

```bash
# Check if PostgreSQL is running
docker compose ps db

# Check logs
docker compose logs db | tail -50

# Restart database
docker compose restart db

# Verify connection settings in .env
cat server/config/.env | grep DATABASE
```

**Issue**: `FATAL: database "oracy_db" does not exist`

```bash
# Create database
docker compose exec db psql -U postgres -c "CREATE DATABASE oracy_db;"

# Or reset and recreate
docker compose down -v
docker compose up -d db
```

### Migration Issues

**Issue**: `django.db.migrations.exceptions.InconsistentMigrationHistory`

```bash
# Solution 1: Fake if migration was already applied
python manage.py migrate --fake app_name migration_name

# Solution 2: Reset migrations (DEVELOPMENT ONLY)
python manage.py migrate app_name zero
python manage.py migrate

# Solution 3: Manual database fix
python manage.py dbshell
# DELETE FROM django_migrations WHERE app='app_name';
# Then re-run migrations
```

**Issue**: Migration stuck / hanging

```bash
# Check for locks
python manage.py dbshell
# SELECT * FROM pg_locks WHERE NOT granted;

# Terminate blocking queries
# SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query LIKE '%migrations%';
```

### Data Issues

**Issue**: Need to reset database to fresh state

```bash
# Development reset
docker compose down -v
docker compose up -d db
python manage.py migrate
python manage.py createsuperuser
```

**Issue**: Slow queries

```bash
# Enable query logging in settings.py
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}

# Or use Django Debug Toolbar
# Check for N+1 queries
```

---

## AI Pipeline Issues

### Speech-to-Text Issues

**Issue**: `openai.error.RateLimitError`

```python
# Add rate limiting and retries
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3)
)
def transcribe_with_retry(audio_path):
    return stt_service.transcribe(audio_path)
```

**Issue**: Transcript quality is poor

```bash
# Check audio quality
ffprobe -v error -show_format -show_streams input.mp4

# Verify audio is clear, not corrupted
# Re-encode if necessary:
ffmpeg -i input.mp4 -ar 16000 -ac 1 -c:a pcm_s16le output.wav
```

**Issue**: AWS Transcribe job fails

```bash
# Check job status
aws transcribe get-transcription-job \
  --transcription-job-name job-name

# Common causes:
# - S3 permissions
# - Audio format not supported
# - File too large (> 2GB for async)
```

### Celery Worker Issues

**Issue**: Tasks not being processed

```bash
# Check worker is running
docker compose ps celery-worker
docker compose logs celery-worker

# Verify Redis connection
redis-cli ping  # Should return PONG

# Check task queue
redis-cli llen celery

# Restart worker
docker compose restart celery-worker
```

**Issue**: `WorkerLostError` or worker crashes

```python
# Check memory usage - may need to limit concurrency
# In docker-compose.yml or celery command:
celery -A config worker -l info --concurrency=2 --max-tasks-per-child=1000

# Or use solo pool for stability
celery -A config worker -l info --pool=solo
```

**Issue**: Task stuck in `PENDING`

```bash
# Check broker URL
celery -A config inspect active

# Purge queue and restart (WARNING: loses pending tasks)
celery -A config purge

# Verify task routing
celery -A config inspect scheduled
```

### LLM Scoring Issues

**Issue**: OpenAI API timeout

```python
# Increase timeout
import openai
client = openai.OpenAI(timeout=120.0)

# Or use streaming for long requests
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    stream=True
)
```

**Issue**: JSON parsing errors from LLM output

```python
# Add JSON schema validation
from pydantic import BaseModel, ValidationError

class ScoreOutput(BaseModel):
    strand_scores: dict
    evidence_clips: list
    strengths: list
    next_steps: list

try:
    output = ScoreOutput.parse_raw(llm_response)
except ValidationError as e:
    # Retry with clearer prompt
    pass
```

---

## Deployment Issues

### ECS Deployment Issues

**Issue**: Service fails to start, `Task failed ELB health checks`

```bash
# Check task logs
aws logs get-log-events \
  --log-group-name /ecs/oracy-production/backend \
  --log-stream-name <stream-name>

# Common causes:
# - Migration not run
# - Environment variables missing
# - Health check endpoint returning error
```

**Issue**: Deployment stuck, tasks not draining

```bash
# Force new deployment
aws ecs update-service \
  --cluster oracy-production \
  --service backend \
  --force-new-deployment

# Check for deployment circuit breaker
aws ecs describe-services \
  --cluster oracy-production \
  --services backend
```

### Database Migration Issues in Production

**Issue**: Migration fails during deployment

```bash
# Run migration manually before deployment
aws ecs run-task \
  --cluster oracy-production \
  --task-definition oracy-migrate \
  --launch-type FARGATE \
  --network-configuration "..."

# Or rollback migration
aws ecs run-task \
  --cluster oracy-production \
  --task-definition oracy-migrate \
  --overrides '{"containerOverrides": [{"name": "migrate", "command": ["python", "manage.py", "migrate", "app_name", "previous_migration"]}]}'
```

### S3 / Storage Issues

**Issue**: Upload fails with 403 Forbidden

```bash
# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:role/oracy-task-role \
  --action-names s3:PutObject \
  --resource-arns arn:aws:s3:::oracy-bucket/*

# Verify CORS configuration
aws s3api get-bucket-cors --bucket oracy-bucket
```

**Issue**: Presigned URL not working

```python
# Verify URL generation
url = s3.generate_presigned_url(
    'put_object',
    Params={
        'Bucket': bucket,
        'Key': key,
        'ContentType': content_type  # Must match client
    },
    ExpiresIn=3600
)

# Client must use same Content-Type header
```

---

## Performance Issues

### Slow API Responses

**Issue**: API requests taking > 1 second

```bash
# Enable Django profiling
# Add middleware: django-cprofile-middleware
python manage.py runserver --noreload
# Access: http://localhost:8000/api/endpoint/?prof

# Check for N+1 queries
# Use select_related / prefetch_related
Assessment.objects.select_related('student', 'student__cohort').all()
```

**Issue**: High memory usage

```python
# Check for memory leaks in Celery
# Add to settings:
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Use streaming for large file processing
# Process in chunks instead of loading all into memory
```

### Slow AI Pipeline

**Issue**: Pipeline taking too long

```python
# Profile each stage
import time

@profile_stage
def transcribe(recording_id):
    # ...

# Parallel processing for independent tasks
from celery import group

group(
    extract_audio.s(rec_id),
    validate_video.s(rec_id)
).apply_async()
```

**Issue**: Database bottleneck

```bash
# Check slow query log
aws rds describe-db-log-files \
  --db-instance-identifier oracy-production

# Add indexes
python manage.py dbshell
# CREATE INDEX CONCURRENTLY idx_assessment_status ON assessments(status);
```

---

## Quick Diagnostic Commands

### System Health Check

```bash
#!/bin/bash
# health-check.sh

echo "=== Docker Status ==="
docker compose ps

echo "=== Database ==="
docker compose exec db pg_isready -U postgres

echo "=== Redis ==="
docker compose exec redis redis-cli ping

echo "=== Backend Health ==="
curl -s http://localhost:8000/health | jq .

echo "=== Celery Workers ==="
cd server && celery -A config inspect active

echo "=== Recent Errors ==="
docker compose logs --tail=50 backend 2>&1 | grep -i error
```

### Database Diagnostics

```bash
# Connection count
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Long-running queries
psql $DATABASE_URL -c "
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 seconds';
"

# Table sizes
psql $DATABASE_URL -c "
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
"
```

### API Diagnostics

```bash
# Test all endpoints
curl -s http://localhost:8000/api/health | jq

# Check response times
for endpoint in /api/assessments/ /api/students/ /api/users/me/; do
  echo -n "$endpoint: "
  curl -s -o /dev/null -w "%{time_total}s\n" http://localhost:8000$endpoint
done

# Load test quick check
ab -n 100 -c 10 http://localhost:8000/api/health
```

---

## Getting Help

### Log Collection

```bash
# Collect all relevant logs for debugging
mkdir -p debug-logs/$(date +%Y%m%d)

# Application logs
docker compose logs backend > debug-logs/$(date +%Y%m%d)/backend.log
docker compose logs celery-worker > debug-logs/$(date +%Y%m%d)/celery.log

# Database logs
docker compose logs db > debug-logs/$(date +%Y%m%d)/db.log

# System info
python --version > debug-logs/$(date +%Y%m%d)/system.txt
node --version >> debug-logs/$(date +%Y%m%d)/system.txt
docker --version >> debug-logs/$(date +%Y%m%d)/system.txt
```

### Debug Mode

```python
# Enable detailed error pages
DJANGO_DEBUG=True python manage.py runserver

# Enable SQL logging
# In settings:
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
}
```

### Support Resources

| Resource | Link | Use For |
|----------|------|---------|
| Django Docs | https://docs.djangoproject.com | Backend issues |
| Celery Docs | https://docs.celeryq.dev | Task queue issues |
| AWS ECS Docs | https://docs.aws.amazon.com/ecs | Deployment issues |
| OpenAI API | https://platform.openai.com/docs | AI integration |
| Project Issues | GitHub Issues | Bug reports |