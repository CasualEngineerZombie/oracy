# Backend Structure (Django)

## Project Structure

```
server/
├── config/                          # Django project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                 # Shared settings
│   │   ├── development.py          # Local dev settings
│   │   ├── staging.py              # Staging settings
│   │   └── production.py           # Production settings
│   ├── urls.py                     # Root URL configuration
│   ├── wsgi.py                     # WSGI application
│   └── asgi.py                     # ASGI application (WebSocket)
│
├── apps/                           # Django applications
│   ├── __init__.py
│   ├── users/                      # Authentication & user management
│   │   ├── __init__.py
│   │   ├── models.py               # User, Teacher, Student models
│   │   ├── serializers.py          # DRF serializers
│   │   ├── views.py                # API views
│   │   ├── urls.py                 # URL routes
│   │   ├── permissions.py          # Custom permissions
│   │   └── tests/
│   │
│   ├── students/                   # Student & cohort management
│   │   ├── models.py               # Student, Cohort, Enrollment
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── assessments/                # Assessment workflow
│   │   ├── models.py               # Assessment, Recording, Prompt
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tasks.py                # Celery tasks for processing
│   │
│   ├── analysis/                   # AI pipeline orchestration
│   │   ├── models.py               # FeatureSignals, EvidenceCandidate
│   │   ├── services/               # External service integrations
│   │   │   ├── __init__.py
│   │   │   ├── stt.py              # STT service interface
│   │   │   ├── llm.py              # LLM scoring service
│   │   │   └── storage.py          # S3 storage service
│   │   ├── pipeline/               # AI pipeline stages
│   │   │   ├── __init__.py
│   │   │   ├── extract_features.py # Feature extraction
│   │   │   ├── benchmark.py        # BDL interpreter
│   │   │   ├── generate_evidence.py# Evidence candidate generation
│   │   │   └── score_llm.py        # LLM scoring
│   │   ├── tasks.py                # Celery tasks for AI pipeline
│   │   └── views.py                # API for analysis status
│   │
│   ├── reports/                    # Draft & signed reports
│   │   ├── models.py               # DraftReport, SignedReport
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── exporters.py            # PDF/CSV export logic
│   │
│   ├── benchmarks/                 # BDL management
│   │   ├── models.py               # BenchmarkVersion
│   │   ├── bdl/                    # BDL JSON definitions
│   │   │   ├── v1.0.0/
│   │   │   │   ├── 11-12_explaining.json
│   │   │   │   ├── 11-12_presenting.json
│   │   │   │   └── ...
│   │   └── loader.py               # BDL loading utilities
│   │
│   └── audit/                      # Audit logging
│       ├── models.py               # AuditLog
│       └── middleware.py           # Auto-logging middleware
│
├── core/                           # Shared utilities
│   ├── __init__.py
│   ├── models.py                   # Abstract base models
│   ├── permissions.py              # Shared permission classes
│   ├── pagination.py               # Custom pagination
│   ├── filters.py                  # DRF filters
│   └── exceptions.py               # Custom exceptions
│
├── templates/                      # Django templates (admin, emails)
├── static/                         # Static files (admin)
├── media/                          # User uploads (local dev)
├── scripts/                        # Management scripts
│   ├── setup_dev.py
│   └── import_benchmarks.py
├── tests/                          # Integration tests
├── pytest.ini                      # Pytest configuration
├── manage.py                       # Django management
├── Dockerfile                      # Container definition
├── entrypoint.sh                   # Container entrypoint
├── requirements/                   # Dependencies
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
└── pyproject.toml                  # Modern Python packaging
```

---

## Django Apps & Responsibilities

### 1. `users` - Authentication & Authorization

**Responsibilities:**
- User authentication (JWT-based)
- Role management (Admin, Teacher, Student)
- Password management
- User profiles

**Key Models:**
```python
class User(AbstractUser):
    """Extended user model with roles."""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True)
    
    # Teacher-specific
    subject = models.CharField(max_length=100, blank=True)
    
    # Student-specific
    year_group = models.CharField(max_length=10, blank=True)

class School(models.Model):
    """School/Institution."""
    name = models.CharField(max_length=200)
    identifier = models.CharField(max_length=50, unique=True)
    region = models.CharField(max_length=50)  # For data residency
```

**Key Views:**
- `POST /api/auth/login/` - JWT token obtain
- `POST /api/auth/refresh/` - Token refresh
- `POST /api/auth/register/` - User registration (admin only)
- `GET /api/users/me/` - Current user profile
- `PATCH /api/users/me/` - Update profile

---

### 2. `students` - Student Management

**Responsibilities:**
- Student profile management
- Cohort/class organization
- Enrollment tracking

**Key Models:**
```python
class Student(models.Model):
    """Student profile."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField()
    year_group = models.CharField(max_length=10)  # e.g., "7", "11"
    age_band = models.CharField(max_length=10)  # e.g., "11-12"
    
    # Language profile
    EAL = models.BooleanField(default=False)
    first_language = models.CharField(max_length=50, blank=True)
    
    # Accommodations
    accommodations = models.JSONField(default=dict, blank=True)

class Cohort(models.Model):
    """Class/group of students."""
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    year_group = models.CharField(max_length=10)
    academic_year = models.CharField(max_length=9)  # e.g., "2025-2026"
    students = models.ManyToManyField(Student, through='Enrollment')

class Enrollment(models.Model):
    """Student-Cohort relationship."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
```

**Key Views:**
- `GET /api/students/` - List students (teacher's cohorts only)
- `POST /api/students/` - Create student
- `GET /api/students/{id}/` - Student detail
- `GET /api/cohorts/` - List cohorts
- `GET /api/cohorts/{id}/students/` - Students in cohort

---

### 3. `assessments` - Assessment Workflow

**Responsibilities:**
- Assessment creation and lifecycle
- Video upload handling
- Prompt management
- Processing status tracking

**Key Models:**
```python
class Assessment(models.Model):
    """An oracy assessment."""
    STATUS_CHOICES = [
        ('pending', 'Pending Upload'),
        ('uploading', 'Uploading'),
        ('processing', 'AI Processing'),
        ('draft_ready', 'Draft Ready'),
        ('under_review', 'Under Review'),
        ('signed_off', 'Signed Off'),
        ('error', 'Error'),
    ]
    
    MODE_CHOICES = [
        ('presenting', 'Presenting'),
        ('explaining', 'Explaining'),
        ('persuading', 'Persuading'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    
    # Assessment config
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    prompt = models.TextField()
    time_limit_seconds = models.IntegerField(default=180)  # 3 min default
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_message = models.TextField(blank=True)
    
    # Consent
    consent_obtained = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

class Recording(models.Model):
    """Video/audio recording for an assessment."""
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE)
    
    # File info
    original_filename = models.CharField(max_length=255)
    s3_key = models.CharField(max_length=500)
    s3_bucket = models.CharField(max_length=100)
    file_size_bytes = models.BigIntegerField()
    duration_seconds = models.FloatField()
    
    # Processing
    audio_extracted = models.BooleanField(default=False)
    audio_s3_key = models.CharField(max_length=500, blank=True)
    
    # Quality
    video_quality_score = models.FloatField(null=True)  # 0-1
    audio_quality_score = models.FloatField(null=True)  # 0-1
    
    created_at = models.DateTimeField(auto_now_add=True)

class PromptTemplate(models.Model):
    """Reusable prompts for assessments."""
    MODE_CHOICES = Assessment.MODE_CHOICES
    
    name = models.CharField(max_length=100)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    text = models.TextField()
    year_groups = models.JSONField(default=list)  # ["7", "8", "9"]
    is_active = models.BooleanField(default=True)
```

**Key Views:**
- `GET /api/assessments/` - List assessments
- `POST /api/assessments/` - Create assessment
- `GET /api/assessments/{id}/` - Assessment detail
- `POST /api/assessments/{id}/upload-url/` - Get S3 presigned URL for upload
- `POST /api/assessments/{id}/complete-upload/` - Trigger processing after upload
- `GET /api/prompts/` - List prompt templates

**Celery Tasks:**
```python
@app.task(bind=True, max_retries=3)
def process_assessment(self, assessment_id: str):
    """Main assessment processing pipeline."""
    assessment = Assessment.objects.get(id=assessment_id)
    
    try:
        # 1. Extract audio from video
        extract_audio_task.delay(assessment_id)
        
        # 2. Transcribe (STT)
        transcribe_task.delay(assessment_id)
        
        # 3. Extract features
        extract_features_task.delay(assessment_id)
        
        # 4. Generate evidence candidates
        generate_evidence_task.delay(assessment_id)
        
        # 5. LLM scoring
        score_with_llm_task.delay(assessment_id)
        
        # 6. Notify completion
        notify_assessment_complete.delay(assessment_id)
        
    except Exception as exc:
        assessment.status = 'error'
        assessment.status_message = str(exc)
        assessment.save()
        raise self.retry(exc=exc, countdown=60)
```

---

### 4. `analysis` - AI Pipeline

**Responsibilities:**
- STT integration
- Feature extraction
- Benchmark application
- Evidence generation
- LLM scoring

**Key Models:**
```python
class Transcript(models.Model):
    """Speech-to-text output."""
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE)
    
    segments = models.JSONField()  # [{start, end, text, words: [...]}]
    full_text = models.TextField()
    language = models.CharField(max_length=10, default='en-GB')
    confidence = models.FloatField()
    
    # Provider info
    provider = models.CharField(max_length=50)  # 'openai', 'aws'
    model_version = models.CharField(max_length=50)
    
    created_at = models.DateTimeField(auto_now_add=True)

class FeatureSignals(models.Model):
    """Extracted features from audio/transcript."""
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE)
    
    # Physical
    wpm = models.FloatField()
    pause_ratio = models.FloatField()
    filler_frequency = models.FloatField()
    volume_variance = models.FloatField()
    rhythm_stability = models.FloatField()
    
    # Linguistic
    sentence_length_variance = models.FloatField()
    vocabulary_diversity = models.FloatField()
    prompt_relevance = models.FloatField()
    clarity_score = models.FloatField()
    register_formality = models.FloatField()
    
    # Cognitive
    reason_density = models.FloatField()
    counterpoint_density = models.FloatField()
    logical_connector_density = models.FloatField()
    structure_completeness = models.FloatField()
    
    # Social-emotional
    audience_reference_frequency = models.FloatField()
    intention_clarity = models.FloatField()
    sentiment_compound = models.FloatField()
    
    # Quality flag
    quality_flag = models.CharField(
        max_length=20,
        choices=[('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')],
        default='good'
    )
    
    extracted_at = models.DateTimeField(auto_now_add=True)

class EvidenceCandidate(models.Model):
    """Potential evidence clips."""
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    
    candidate_id = models.CharField(max_length=20)  # "clip_0", "clip_1", etc.
    start_time = models.FloatField()  # seconds
    end_time = models.FloatField()
    type = models.CharField(max_length=50)  # 'transcript_boundary', 'reason_dense', etc.
    summary = models.TextField()
    features = models.JSONField()
    
    class Meta:
        ordering = ['start_time']
```

**Service Interfaces:**
```python
# apps/analysis/services/stt.py
from typing import Protocol
from dataclasses import dataclass

@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    words: List[Word]

class STTService(Protocol):
    """Abstract STT service interface."""
    
    def transcribe(self, audio_path: str) -> List[TranscriptSegment]:
        ...
    
    def supports_streaming(self) -> bool:
        ...

class WhisperService:
    """OpenAI Whisper implementation."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def transcribe(self, audio_path: str) -> List[TranscriptSegment]:
        # Implementation...
        pass

class AWSTranscribeService:
    """AWS Transcribe implementation."""
    
    def transcribe(self, audio_path: str) -> List[TranscriptSegment]:
        # Implementation...
        pass
```

---

### 5. `reports` - Report Management

**Responsibilities:**
- Draft report storage
- Teacher review workflow
- Signed report archival
- Export generation (PDF/CSV)

**Key Models:**
```python
class DraftReport(models.Model):
    """AI-generated draft report."""
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE)
    
    # Strand scores
    physical_score = models.JSONField()  # {band, confidence, evidence_clips, justification}
    linguistic_score = models.JSONField()
    cognitive_score = models.JSONField()
    social_emotional_score = models.JSONField()
    
    # Feedback
    feedback = models.JSONField()  # {strengths: [], next_steps: [], goals: []}
    
    # Metadata
    ai_model = models.CharField(max_length=50)  # 'gpt-4o'
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # Status
    is_reviewed = models.BooleanField(default=False)

class SignedReport(models.Model):
    """Teacher-signed final report."""
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE)
    draft = models.OneToOneField(DraftReport, on_delete=models.SET_NULL, null=True)
    
    # Final scores (may differ from draft)
    physical_score = models.JSONField()
    linguistic_score = models.JSONField()
    cognitive_score = models.JSONField()
    social_emotional_score = models.JSONField()
    
    # Final feedback
    feedback = models.JSONField()
    teacher_notes = models.TextField(blank=True)
    
    # Signing
    signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    signed_at = models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    """Track all changes to reports."""
    ACTION_CHOICES = [
        ('score_changed', 'Score Changed'),
        ('clip_changed', 'Evidence Clip Changed'),
        ('feedback_edited', 'Feedback Edited'),
        ('signed', 'Report Signed'),
    ]
    
    report = models.ForeignKey(DraftReport, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    field = models.CharField(max_length=50)
    old_value = models.JSONField(null=True)
    new_value = models.JSONField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
```

**Key Views:**
- `GET /api/reports/draft/{assessment_id}/` - Get draft report
- `POST /api/reports/draft/{assessment_id}/edit/` - Edit draft
- `POST /api/reports/{assessment_id}/sign/` - Sign off on report
- `GET /api/reports/{assessment_id}/export/pdf/` - Generate PDF

**PDF Export:**
```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

class PDFExporter:
    """Generate inspection-grade PDF reports."""
    
    def export(self, report: SignedReport) -> bytes:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Header
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 800, "Oracy Assessment Report")
        
        # Student info
        c.setFont("Helvetica", 12)
        student = report.assessment.student
        c.drawString(50, 760, f"Student: {student.user.get_full_name()}")
        c.drawString(50, 740, f"Year Group: {student.year_group}")
        c.drawString(50, 720, f"Date: {report.signed_at.strftime('%d %B %Y')}")
        
        # Scores
        y = 680
        for strand, score_data in [
            ('Physical', report.physical_score),
            ('Linguistic', report.linguistic_score),
            ('Cognitive', report.cognitive_score),
            ('Social-Emotional', report.social_emotional_score),
        ]:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, f"{strand}: {score_data['band'].title()}")
            y -= 20
            
            # Evidence clips
            c.setFont("Helvetica", 10)
            for clip in score_data['evidence_clips'][:3]:  # Top 3 clips
                c.drawString(70, y, f"• [{clip['start']:.1f}s - {clip['end']:.1f}s]")
                y -= 15
            
            y -= 10
        
        c.save()
        return buffer.getvalue()
```

---

### 6. `benchmarks` - BDL Management

**Responsibilities:**
- Benchmark version storage
- BDL loading and validation
- Version management

**Key Models:**
```python
class BenchmarkVersion(models.Model):
    """A versioned benchmark definition."""
    version = models.CharField(max_length=20)
    age_band = models.CharField(max_length=10)  # "11-12"
    mode = models.CharField(max_length=20)  # "explaining"
    
    definition = models.JSONField()  # Full BDL
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['version', 'age_band', 'mode']
        ordering = ['-created_at']

class BenchmarkLoader:
    """Load BDL from JSON files into database."""
    
    def load_from_directory(self, directory: Path):
        """Load all BDL files from a directory."""
        for file_path in directory.glob('**/*.json'):
            with open(file_path) as f:
                definition = json.load(f)
            
            BenchmarkVersion.objects.get_or_create(
                version=definition['version'],
                age_band=definition['age_band'],
                mode=definition['mode'],
                defaults={'definition': definition}
            )
```

---

## API Design

### REST Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login/` | POST | Obtain JWT tokens |
| `/api/auth/refresh/` | POST | Refresh access token |
| `/api/users/me/` | GET/PATCH | Current user profile |
| `/api/students/` | GET/POST | List/create students |
| `/api/students/{id}/` | GET/PUT/DELETE | Student detail |
| `/api/cohorts/` | GET/POST | List/create cohorts |
| `/api/cohorts/{id}/students/` | GET | Students in cohort |
| `/api/assessments/` | GET/POST | List/create assessments |
| `/api/assessments/{id}/` | GET | Assessment detail |
| `/api/assessments/{id}/upload-url/` | POST | Get S3 presigned URL |
| `/api/assessments/{id}/status/` | GET | Processing status |
| `/api/reports/draft/{id}/` | GET | Get draft report |
| `/api/reports/draft/{id}/edit/` | POST | Edit draft |
| `/api/reports/{id}/sign/` | POST | Sign report |
| `/api/reports/{id}/export/pdf/` | GET | Download PDF |
| `/api/benchmarks/` | GET | List active benchmarks |
| `/api/audit/{report_id}/` | GET | Audit trail |

### WebSocket Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/ws/assessments/{id}/` | Real-time processing updates |

```python
# consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class AssessmentConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.assessment_id = self.scope['url_route']['kwargs']['id']
        self.group_name = f"assessment_{self.assessment_id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
    
    async def assessment_update(self, event):
        await self.send_json({
            'type': 'status_update',
            'status': event['status'],
            'message': event.get('message', '')
        })
```

---

## Settings Configuration

### base.py
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'channels',
    
    # Local apps
    'apps.users',
    'apps.students',
    'apps.assessments',
    'apps.analysis',
    'apps.reports',
    'apps.benchmarks',
    'apps.audit',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'oracy'),
        'USER': os.getenv('DB_USER', 'oracy'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'oracy'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Redis/Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    }
}

# Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardResultsSetPagination',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

# Channels (WebSocket)
ASGI_APPLICATION = 'config.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.getenv('REDIS_URL', 'redis://localhost:6379/0')],
        },
    },
}

# File Storage (S3)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_REGION', 'ap-southeast-1')
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = 'private'
AWS_S3_VERIFY = True

# AI Services
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
```

---

## Testing Strategy

### Test Structure
```
tests/
├── conftest.py                 # Pytest fixtures
├── factories.py                # Model factories (factory-boy)
├── unit/
│   ├── test_users.py
│   ├── test_assessments.py
│   └── test_analysis.py
├── integration/
│   ├── test_api.py
│   └── test_pipeline.py
└── e2e/
    └── test_full_workflow.py
```

### Key Fixtures
```python
# conftest.py
import pytest
from apps.users.models import User

@pytest.fixture
def teacher_user(db):
    return User.objects.create_user(
        username='teacher@school.edu',
        email='teacher@school.edu',
        password='testpass123',
        role='teacher'
    )

@pytest.fixture
def api_client(teacher_user):
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=teacher_user)
    return client

@pytest.fixture
def mock_stt_service(monkeypatch):
    """Mock STT service for tests."""
    class MockSTT:
        def transcribe(self, audio_path):
            return [
                TranscriptSegment(
                    start=0.0,
                    end=5.0,
                    text="Test transcript",
                    words=[...]
                )
            ]
    
    monkeypatch.setattr(
        'apps.analysis.services.stt.WhisperService',
        MockSTT
    )
```
