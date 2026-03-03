# Database Migrations

Guide for managing database schema changes in Oracy AI using Django migrations.

## Table of Contents

1. [Migration Overview](#migration-overview)
2. [Creating Migrations](#creating-migrations)
3. [Applying Migrations](#applying-migrations)
4. [Migration Best Practices](#migration-best-practices)
5. [Common Migration Scenarios](#common-migration-scenarios)
6. [Troubleshooting Migrations](#troubleshooting-migrations)

---

## Migration Overview

Oracy AI uses Django's migration system to manage PostgreSQL schema changes. Migrations are version-controlled Python files that define database schema evolution.

### Migration Files Location

```
server/
├── apps/
│   ├── users/
│   │   └── migrations/         # User-related migrations
│   │       ├── 0001_initial.py
│   │       └── 0002_add_fields.py
│   ├── students/
│   │   └── migrations/         # Student & cohort migrations
│   ├── assessments/
│   │   └── migrations/         # Assessment migrations
│   ├── analysis/
│   │   └── migrations/         # AI pipeline data migrations
│   └── reports/
│       └── migrations/         # Report migrations
```

### Migration Commands Reference

| Command | Purpose |
|---------|---------|
| `makemigrations` | Create new migrations from model changes |
| `migrate` | Apply migrations to database |
| `showmigrations` | List all migrations and their status |
| `sqlmigrate` | Show SQL for a migration |
| `migrate zero` | Rollback all migrations |

---

## Creating Migrations

### Standard Workflow

```bash
cd server

# 1. Make changes to models.py files
# Example: Add a field to apps/students/models.py

# 2. Create migration
python manage.py makemigrations

# 3. Review generated migration
python manage.py sqlmigrate students 0003

# 4. Apply migration
python manage.py migrate
```

### Example: Adding a Field

```python
# apps/students/models.py
class Student(models.Model):
    # ... existing fields ...
    
    # New field
    preferred_language = models.CharField(
        max_length=10,
        default='en',
        choices=[
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
        ]
    )
```

```bash
# Create migration
python manage.py makemigrations students

# Output:
# Migrations for 'students':
#   apps/students/migrations/0003_student_preferred_language.py
#     - Add field preferred_language to student
```

### Named Migrations

```bash
# Create with descriptive name
python manage.py makemigrations students --name=add_language_preference

# Result: 0003_add_language_preference.py
```

### Empty Migrations

For data migrations or custom SQL:

```bash
python manage.py makemigrations students --empty --name=populate_defaults
```

---

## Applying Migrations

### Development

```bash
# Apply all pending migrations
python manage.py migrate

# Apply specific app migrations
python manage.py migrate students

# Apply to specific migration
python manage.py migrate students 0002
```

### Docker Environment

```bash
# Run migrations in container
docker compose run --rm backend python manage.py migrate

# Or exec into running container
docker compose exec backend python manage.py migrate
```

### Verify Migration Status

```bash
# List all migrations
python manage.py showmigrations

# Sample output:
# admin
#  [X] 0001_initial
#  [X] 0002_logentry_remove_auto_add
# students
#  [X] 0001_initial
#  [X] 0002_add_cohort
#  [ ] 0003_add_language_preference  <- Not applied
```

---

## Migration Best Practices

### 1. Always Review Before Applying

```bash
# View SQL that will be executed
python manage.py sqlmigrate students 0003

# Check for destructive operations
# - DROP TABLE
# - DROP COLUMN
# - ALTER COLUMN (with data loss risk)
```

### 2. One Change Per Migration

Avoid bundling unrelated changes:

```bash
# Good: Separate migrations
python manage.py makemigrations students --name=add_birth_date
python manage.py makemigrations assessments --name=add_duration_field

# Avoid: One giant migration with many changes
```

### 3. Handle Data Carefully

```python
# Migration with data migration
from django.db import migrations, models

def populate_full_name(apps, schema_editor):
    Student = apps.get_model('students', 'Student')
    for student in Student.objects.all():
        student.full_name = f"{student.first_name} {student.last_name}"
        student.save(update_fields=['full_name'])

class Migration(migrations.Migration):
    dependencies = [
        ('students', '0002_auto_20240301'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='student',
            name='full_name',
            field=models.CharField(max_length=200, default=''),
        ),
        migrations.RunPython(populate_full_name),
    ]
```

### 4. Make Fields Nullable First

When adding required fields to existing tables:

```python
# Step 1: Add as nullable
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='recording',
            name='duration_seconds',
            field=models.FloatField(null=True, blank=True),
        ),
    ]

# Step 2: Populate data (separate migration or script)

# Step 3: Make required
class Migration(migrations.Migration):
    operations = [
        migrations.AlterField(
            model_name='recording',
            name='duration_seconds',
            field=models.FloatField(),
        ),
    ]
```

### 5. Index Strategy

```python
# Add indexes for frequently queried fields
class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name='assessment',
            index=models.Index(
                fields=['status', 'created_at'],
                name='assessment_status_created_idx'
            ),
        ),
    ]
```

---

## Common Migration Scenarios

### Adding a New Model

```python
# apps/analysis/models.py
class FeatureSignals(models.Model):
    recording = models.ForeignKey(
        'assessments.Recording',
        on_delete=models.CASCADE,
        related_name='feature_signals'
    )
    word_count = models.IntegerField(default=0)
    filler_count = models.IntegerField(default=0)
    avg_word_duration = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
```

```bash
python manage.py makemigrations analysis
python manage.py migrate
```

### Adding a Foreign Key

```python
# apps/reports/models.py
class DraftReport(models.Model):
    assessment = models.ForeignKey(
        'assessments.Assessment',
        on_delete=models.CASCADE,
        related_name='draft_reports'
    )
    # ... other fields
```

### Renaming a Field

```python
# Django creates RenameField operation
# Safe operation: uses ALTER COLUMN

# Before: transcript_text
# After: full_transcript
```

```bash
python manage.py makemigrations analysis --name=rename_transcript_field
```

### Removing a Field

```bash
# WARNING: Destructive operation
# 1. Remove field from model
# 2. Create migration
python manage.py makemigrations

# 3. Review SQL
python manage.py sqlmigrate app_name 000X

# 4. Backup database before applying
```

### Changing Field Type

```python
# Example: Integer to Float

# BAD: Direct change may lose data
score = models.IntegerField()  # OLD
score = models.FloatField()    # NEW - Risky!

# GOOD: Multi-step migration
# Step 1: Add new field
score_decimal = models.FloatField(null=True)

# Step 2: Migrate data in migration

# Step 3: Remove old field, rename new
```

---

## Troubleshooting Migrations

### Migration Conflicts

```bash
# Multiple branches created migrations
python manage.py migrate
# CommandError: Conflicting migrations detected

# Solution 1: Merge migrations
python manage.py makemigrations --merge

# Solution 2: Rollback and recreate
python manage.py migrate app_name previous_migration
git checkout --theirs app_name/migrations/000X.py
python manage.py makemigrations
```

### Failed Migration

```bash
# Migration partially applied
# 1. Check database state
python manage.py dbshell
\dt  # List tables
\d tablename  # Describe table

# 2. Fake migration if manually fixed
python manage.py migrate --fake app_name migration_name

# 3. Or rollback and reapply
python manage.py migrate app_name previous_migration
# Fix issue
python manage.py migrate
```

### Circular Dependencies

```python
# If apps reference each other in migrations

# Solution: Use string references and lazy imports
# In models:
assessment = models.ForeignKey(
    'assessments.Assessment',  # String reference
    on_delete=models.CASCADE
)

# In migrations:
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('assessments', '0001_initial'),
    ]
```

### Resetting Migrations (Development Only)

```bash
# DANGER: Destroys all data!
# Only for development reset

# 1. Delete migration files
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 2. Drop database
docker compose down -v

# 3. Recreate
docker compose up -d db

# 4. Recreate migrations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Database Lock Issues

```bash
# Check for locks (PostgreSQL)
python manage.py dbshell

# Query:
# SELECT * FROM pg_locks WHERE NOT granted;
# SELECT pid, state, query FROM pg_stat_activity WHERE state = 'active';

# Kill blocking process
# SELECT pg_terminate_backend(pid);
```

### Migration Takes Too Long

```python
# For large tables, add index CONCURRENTLY
from django.contrib.postgres.operations import AddIndexConcurrently

class Migration(migrations.Migration):
    atomic = False  # Allow non-atomic operations
    
    operations = [
        AddIndexConcurrently(
            model_name='recording',
            index=models.Index(
                fields=['created_at'],
                name='recording_created_idx'
            ),
        ),
    ]
```

---

## Migration Checklist

Before committing migrations:

- [ ] Migration files generated: `makemigrations`
- [ ] SQL reviewed: `sqlmigrate app_name 000X`
- [ ] No destructive operations on production data
- [ ] Migrations tested locally: `migrate`
- [ ] Migrations committed with code changes
- [ ] Backward compatibility considered (for zero-downtime deploys)

## Production Deployment

```bash
# Staging first
python manage.py migrate --database=staging

# Then production
python manage.py migrate --database=production

# With monitoring
python manage.py migrate --verbosity=2