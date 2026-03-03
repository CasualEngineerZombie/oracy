# AI Pipeline Execution

Guide for running and testing the AI/ML pipeline for oracy assessment processing.

## Table of Contents

1. [Pipeline Overview](#pipeline-overview)
2. [Running the Full Pipeline](#running-the-full-pipeline)
3. [Individual Stage Execution](#individual-stage-execution)
4. [Pipeline Monitoring](#pipeline-monitoring)
5. [Testing with Sample Data](#testing-with-sample-data)
6. [Debugging Pipeline Issues](#debugging-pipeline-issues)

---

## Pipeline Overview

The AI pipeline processes student recordings through 5 stages:

```
Video Upload → STT → Feature Extraction → Benchmarking → Evidence Gen → LLM Scoring
     │            │           │              │              │             │
     ▼            ▼           ▼              ▼              ▼             ▼
  S3 Storage  Transcript  FeatureSignals  Evidence      Evidence      DraftReport
              JSON        JSON            Matches       Candidates
```

### Pipeline Stages

| Stage | Service | Input | Output | Duration |
|-------|---------|-------|--------|----------|
| 1. Speech-to-Text | OpenAI Whisper | Audio/Video | Transcript JSON | 10-30s |
| 2. Feature Extraction | Python/NLP | Transcript | FeatureSignals | 2-5s |
| 3. Benchmarking | BDL Engine | Features + BDL | Evidence Matches | 1-3s |
| 4. Evidence Generation | Deterministic | Matches | EvidenceCandidates | 1-2s |
| 5. LLM Scoring | GPT-4o/Claude | Candidates + Rubric | DraftReport | 15-45s |

---

## Running the Full Pipeline

### Automatic Processing (Production)

When a video is uploaded, the pipeline runs automatically via Celery:

```python
# apps/assessments/tasks.py
from celery import chain

@shared_task
def process_recording(recording_id):
    """Run complete AI pipeline for a recording."""
    chain(
        extract_audio.s(recording_id),
        transcribe.s(),
        extract_features.s(),
        run_benchmark.s(),
        generate_evidence.s(),
        score_with_llm.s()
    ).apply_async()
```

### Manual Trigger (Development)

```bash
cd server
source .venv/bin/activate  # or Windows equivalent

# Trigger via Django shell
python manage.py shell

>>> from apps.assessments.tasks import process_recording
>>> result = process_recording.delay('recording-uuid-here')
>>> result.id  # Get task ID for monitoring
'abc123-def456-...'
>>> result.status  # Check status
'PENDING' / 'SUCCESS' / 'FAILURE'
```

### API Trigger

```bash
# POST to assessment endpoint with video
curl -X POST http://localhost:8000/api/assessments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "video=@sample_video.mp4" \
  -F "student_id=student-uuid" \
  -F "mode=presenting"

# Pipeline starts automatically
```

---

## Individual Stage Execution

### Stage 1: Speech-to-Text (STT)

```bash
# Via Django shell
python manage.py shell

>>> from apps.analysis.services.stt import WhisperSTTService
>>> from apps.analysis.models import Recording

>>> recording = Recording.objects.get(id='recording-uuid')
>>> stt_service = WhisperSTTService()

# Process audio
>>> transcript = stt_service.transcribe(recording.audio_file.path)
>>> print(transcript.full_text)
>>> print(f"Duration: {transcript.duration_seconds}s")
>>> print(f"Word count: {len(transcript.words)}")

# Save to database
>>> recording.transcript = transcript.to_dict()
>>> recording.save()
```

### Stage 2: Feature Extraction

```python
# apps/analysis/pipeline/extract_features.py
from apps.analysis.pipeline.extract_features import FeatureExtractor

# Load transcript
transcript_data = recording.transcript

# Extract features
extractor = FeatureExtractor()
features = extractor.extract(transcript_data)

# Features include:
# - word_count: Total words spoken
# - filler_count: "um", "uh", "like" occurrences
# - pause_patterns: Silent periods
# - speaking_rate: Words per minute
# - vocabulary_diversity: Unique words / total words
# - sentence_complexity: Average sentence length
# - question_frequency: Questions per minute

# Save
FeatureSignals.objects.create(
    recording=recording,
    word_count=features['word_count'],
    filler_count=features['filler_count'],
    avg_word_duration=features['avg_word_duration'],
    speaking_rate=features['speaking_rate'],
    vocabulary_diversity=features['vocabulary_diversity'],
    data=features  # Full JSON
)
```

### Stage 3: Benchmarking (BDL)

```python
from apps.analysis.pipeline.benchmark import BenchmarkEngine

# Load BDL for age band and mode
engine = BenchmarkEngine(
    age_band='11-12',
    mode='presenting'
)

# Compare features against benchmarks
matches = engine.evaluate(features)

# Matches contain:
# - strand: Physical/Linguistic/Cognitive/Social
# - descriptor: Matched benchmark descriptor
# - confidence: Match confidence score
# - evidence_timestamps: Relevant timestamps
```

### Stage 4: Evidence Generation

```python
from apps.analysis.pipeline.generate_evidence import EvidenceGenerator

generator = EvidenceGenerator()
candidates = generator.generate(
    transcript=transcript,
    matches=matches,
    max_clips_per_strand=5
)

# Candidates include:
# - clip_start/end: Timestamp range
# - transcript_segment: Text excerpt
# - strand: Which assessment strand
# - descriptor: What benchmark it demonstrates
```

### Stage 5: LLM Scoring

```python
from apps.analysis.pipeline.score_llm import LLMScorer

scorer = LLMScorer(model='gpt-4o')
report = scorer.score(
    evidence_candidates=candidates,
    mode='presenting',
    age_band='11-12'
)

# Report contains:
# - strand_scores: Emerging/Expected/Exceeding per strand
# - evidence_clips: Selected timestamps with explanations
# - strengths: 3 identified strengths
# - next_steps: 3 improvement areas
# - practice_goals: Student-friendly goals
# - confidence: Confidence score per strand
```

---

## Pipeline Monitoring

### Celery Flower Dashboard

```bash
# Start Flower monitoring
celery -A config flower --port=5555

# Access at http://localhost:5555
# View task progress, retries, failures
```

### Check Task Status

```python
from celery.result import AsyncResult
from celery import current_app

# Get task info
task = AsyncResult('task-uuid-here')
print(f"Status: {task.status}")
print(f"Result: {task.result}")

# Get task metadata
print(f"State: {task.state}")
if task.state == 'FAILURE':
    print(f"Exception: {task.result}")
```

### Pipeline Progress API

```bash
# Check recording processing status
curl http://localhost:8000/api/recordings/{id}/status/ \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "recording_id": "uuid",
  "status": "processing",
  "current_stage": "llm_scoring",
  "progress_percent": 80,
  "stages_completed": ["stt", "feature_extraction", "benchmarking", "evidence_gen"],
  "stages_pending": ["llm_scoring"],
  "estimated_completion": "2024-03-15T10:30:00Z"
}
```

### Database Query Status

```python
# Check all pending recordings
Recording.objects.filter(
    status__in=['pending', 'processing']
).values('id', 'status', 'current_stage', 'updated_at')

# Check failed recordings
Recording.objects.filter(
    status='failed'
).values('id', 'error_message', 'failed_stage')
```

---

## Testing with Sample Data

### Generate Test Recording

```python
# Create test recording with sample transcript
from apps.assessments.models import Recording, Assessment
from apps.students.models import Student

# Get or create test student
student = Student.objects.first()

# Create assessment
assessment = Assessment.objects.create(
    student=student,
    mode='presenting',
    prompt='Explain photosynthesis'
)

# Create recording with sample transcript
recording = Recording.objects.create(
    assessment=assessment,
    status='uploaded',
    transcript={
        "duration_seconds": 45.2,
        "full_text": "Today I'm going to explain photosynthesis...",
        "segments": [
            {
                "start": 0.0,
                "end": 4.5,
                "text": "Today I'm going to explain photosynthesis.",
                "words": [...]
            },
            # ... more segments
        ]
    }
)
```

### Run Pipeline on Test Data

```bash
# Run specific stage
python manage.py run_pipeline_stage \
  --recording-id={uuid} \
  --stage=extract_features

# Run full pipeline
python manage.py run_pipeline \
  --recording-id={uuid} \
  --verbose
```

### Load Sample Benchmarks

```bash
# Import BDL definitions
python manage.py import_benchmarks \
  --directory=apps/benchmarks/bdl/v1.0.0/ \
  --version=1.0.0

# Verify import
python manage.py shell
>>> from apps.benchmarks.models import BenchmarkVersion
>>> BenchmarkVersion.objects.all()
```

---

## Debugging Pipeline Issues

### Enable Debug Logging

```python
# settings/development.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.analysis': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'celery': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Common Issues

#### STT Fails

```python
# Check audio format
import subprocess
result = subprocess.run(
    ['ffprobe', '-v', 'error', '-show_format', '-show_streams', audio_path],
    capture_output=True, text=True
)
print(result.stdout)

# Verify OpenAI API key
from django.conf import settings
print(settings.OPENAI_API_KEY[:10] + '...')
```

#### Feature Extraction Errors

```python
# Debug transcript format
print(json.dumps(recording.transcript, indent=2)[:500])

# Check required fields
required = ['segments', 'words', 'duration_seconds']
transcript = recording.transcript
for field in required:
    print(f"{field}: {field in transcript}")
```

#### LLM Scoring Timeout

```python
# Increase timeout in scorer
scorer = LLMScorer(
    model='gpt-4o',
    timeout=120,  # seconds
    max_retries=3
)

# Or use async with timeout
import asyncio
from asyncio import timeout

async def score_with_timeout():
    async with timeout(60):
        return await scorer.score_async(candidates)
```

### Retry Failed Tasks

```bash
# List failed tasks
celery -A config inspect failed

# Retry specific task
python manage.py shell
>>> from celery.result import AsyncResult
>>> task = AsyncResult('failed-task-id')
>>> task.retry()

# Retry all failed for a recording
Recording.objects.get(id='uuid').retry_pipeline()
```

### Pipeline Performance Profiling

```python
import time
from functools import wraps

def profile_stage(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

# Apply to pipeline stages
@profile_stage
def transcribe(recording_id):
    # ... STT logic
    pass
```

---

## Batch Processing

### Process Multiple Recordings

```python
from celery import group

# Get pending recordings
recording_ids = Recording.objects.filter(
    status='uploaded'
).values_list('id', flat=True)[:10]

# Create group task
job = group(
    process_recording.s(rec_id) for rec_id in recording_ids
)
result = job.apply_async()

# Monitor progress
while not result.ready():
    print(f"Completed: {result.completed_count()}/{len(recording_ids)}")
    time.sleep(1)
```

### Batch Processing Command

```bash
# Process all pending recordings
python manage.py process_recordings \
  --batch-size=10 \
  --max-concurrent=4 \
  --priority=high