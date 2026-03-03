# Database Schema

## Entity Relationship Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│     School      │     │      User        │     │     Student     │
├─────────────────┤     ├──────────────────┤     ├─────────────────┤
│ id (PK)         │◀────┤ school_id (FK)   │     │ id (PK)         │
│ name            │     │ id (PK)          │     │ user_id (FK)    │──┐
│ identifier      │     │ email            │     │ student_id      │  │
│ region          │     │ password_hash    │     │ date_of_birth   │  │
│ created_at      │     │ role             │     │ year_group      │  │
└─────────────────┘     │ first_name       │     │ age_band        │  │
                        │ last_name        │     │ eal             │  │
                        │ is_active        │     │ first_language  │  │
                        └──────────────────┘     │ accommodations  │  │
                              │                  │ created_at      │  │
                              │                  └─────────────────┘  │
                              │                         │             │
                              │                         │             │
                              ▼                         ▼             │
                       ┌──────────────────┐     ┌─────────────────┐  │
                       │     Cohort       │     │   Enrollment    │  │
                       ├──────────────────┤     ├─────────────────┤  │
                       │ id (PK)          │◀────┤ cohort_id (FK)  │  │
                       │ teacher_id (FK)  │     │ student_id (FK) │──┘
                       │ name             │     │ enrolled_at     │
                       │ year_group       │     └─────────────────┘
                       │ academic_year    │
                       └──────────────────┘
                              │
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            Assessment                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK, UUID)                                                           │
│ student_id (FK) ◀─────────────────────────────────────────────────────┐  │
│ cohort_id (FK)                                                        │  │
│ mode (presenting|explaining|persuading)                               │  │
│ prompt (TEXT)                                                         │  │
│ time_limit_seconds                                                    │  │
│ status                                                                │  │
│ status_message                                                        │  │
│ consent_obtained                                                      │  │
│ consent_date                                                          │  │
│ created_at                                                            │  │
│ uploaded_at                                                           │  │
│ completed_at                                                          │  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Recording   │     │  Transcript   │     │FeatureSignals │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ id (PK)       │     │ id (PK)       │     │ id (PK)       │
│ assessment_id │     │ assessment_id │     │ assessment_id │
│ s3_bucket     │     │ segments(JSON)│     │ wpm           │
│ s3_key        │     │ full_text     │     │ pause_ratio   │
│ file_size     │     │ language      │     │ filler_freq   │
│ duration_sec  │     │ confidence    │     │ ...features   │
│ audio_s3_key  │     │ provider      │     │ quality_flag  │
│ video_quality │     │ model_version │     │ extracted_at  │
│ audio_quality │     │ created_at    │     └───────────────┘
└───────────────┘     └───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EvidenceCandidate                               │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)                                                                 │
│ assessment_id (FK)                                                      │
│ candidate_id (clip_0, clip_1, etc.)                                     │
│ start_time (seconds)                                                    │
│ end_time (seconds)                                                      │
│ type (transcript_boundary, reason_dense, etc.)                          │
│ summary                                                                 │
│ features (JSON)                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           DraftReport                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)                                                                 │
│ assessment_id (FK)                                                      │
│ physical_score (JSON: band, confidence, evidence_clips, justification)  │
│ linguistic_score (JSON)                                                 │
│ cognitive_score (JSON)                                                  │
│ social_emotional_score (JSON)                                           │
│ feedback (JSON: strengths[], next_steps[], goals[])                     │
│ ai_model                                                                │
│ generated_at                                                            │
│ is_reviewed                                                             │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          SignedReport                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)                                                                 │
│ assessment_id (FK)                                                      │
│ draft_id (FK)                                                           │
│ physical_score (JSON)                                                   │
│ linguistic_score (JSON)                                                 │
│ cognitive_score (JSON)                                                  │
│ social_emotional_score (JSON)                                           │
│ feedback (JSON)                                                         │
│ teacher_notes                                                           │
│ signed_by (FK → User)                                                   │
│ signed_at                                                               │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            AuditLog                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)                                                                 │
│ report_id (FK)                                                          │
│ user_id (FK)                                                            │
│ action (score_changed, clip_changed, feedback_edited, signed)           │
│ field                                                                   │
│ old_value (JSON)                                                        │
│ new_value (JSON)                                                        │
│ timestamp                                                               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        BenchmarkVersion                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ version (PK)                                                            │
│ age_band                                                                │
│ mode                                                                    │
│ definition (JSON - full BDL)                                            │
│ is_active                                                               │
│ created_at                                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Table Definitions

### Core Tables

#### `users` (via Django AbstractUser)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(254) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,  -- Django's hashed password
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
    school_id INTEGER REFERENCES schools(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    date_joined TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_school ON users(school_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);
```

#### `schools`
```sql
CREATE TABLE schools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    identifier VARCHAR(50) UNIQUE NOT NULL,  -- School URN or custom ID
    region VARCHAR(50),  -- For data residency
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_schools_identifier ON schools(identifier);
```

#### `students`
```sql
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    student_id VARCHAR(50) UNIQUE NOT NULL,  -- School's student ID
    date_of_birth DATE,
    year_group VARCHAR(10) NOT NULL,  -- "7", "8", "11", etc.
    age_band VARCHAR(10) NOT NULL,  -- "11-12", "13-14", etc.
    eal BOOLEAN DEFAULT FALSE,  -- English as Additional Language
    first_language VARCHAR(50),
    accommodations JSONB DEFAULT '{}',  -- Extended time, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_students_year_group ON students(year_group);
CREATE INDEX idx_students_age_band ON students(age_band);
CREATE INDEX idx_students_eal ON students(eal);
```

#### `cohorts`
```sql
CREATE TABLE cohorts (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    year_group VARCHAR(10) NOT NULL,
    academic_year VARCHAR(9) NOT NULL,  -- "2025-2026"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cohorts_teacher ON cohorts(teacher_id);
CREATE INDEX idx_cohorts_year ON cohorts(academic_year);
```

#### `enrollments`
```sql
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    cohort_id INTEGER NOT NULL REFERENCES cohorts(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(student_id, cohort_id)
);

CREATE INDEX idx_enrollments_cohort ON enrollments(cohort_id);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
```

### Assessment Tables

#### `assessments`
```sql
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    cohort_id INTEGER NOT NULL REFERENCES cohorts(id) ON DELETE CASCADE,
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('presenting', 'explaining', 'persuading')),
    prompt TEXT NOT NULL,
    time_limit_seconds INTEGER DEFAULT 180,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'uploading', 'processing', 'draft_ready', 
                   'under_review', 'signed_off', 'error')
    ),
    status_message TEXT,
    consent_obtained BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_assessments_student ON assessments(student_id);
CREATE INDEX idx_assessments_cohort ON assessments(cohort_id);
CREATE INDEX idx_assessments_status ON assessments(status);
CREATE INDEX idx_assessments_created ON assessments(created_at DESC);
CREATE INDEX idx_assessments_mode ON assessments(mode);

-- Composite index for teacher dashboard queries
CREATE INDEX idx_assessments_cohort_status ON assessments(cohort_id, status, created_at DESC);
```

#### `recordings`
```sql
CREATE TABLE recordings (
    id SERIAL PRIMARY KEY,
    assessment_id UUID UNIQUE REFERENCES assessments(id) ON DELETE CASCADE,
    original_filename VARCHAR(255),
    s3_bucket VARCHAR(100) NOT NULL,
    s3_key VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    duration_seconds FLOAT,
    audio_extracted BOOLEAN DEFAULT FALSE,
    audio_s3_key VARCHAR(500),
    video_quality_score FLOAT CHECK (video_quality_score BETWEEN 0 AND 1),
    audio_quality_score FLOAT CHECK (audio_quality_score BETWEEN 0 AND 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_recordings_assessment ON recordings(assessment_id);
```

### Analysis Tables

#### `transcripts`
```sql
CREATE TABLE transcripts (
    id SERIAL PRIMARY KEY,
    assessment_id UUID UNIQUE REFERENCES assessments(id) ON DELETE CASCADE,
    segments JSONB NOT NULL,  -- [{start, end, text, words: [{word, start, end, confidence}]}]
    full_text TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en-GB',
    confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'aws'
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_transcripts_assessment ON transcripts(assessment_id);

-- Full-text search index
CREATE INDEX idx_transcripts_fts ON transcripts USING GIN (to_tsvector('english', full_text));
```

#### `feature_signals`
```sql
CREATE TABLE feature_signals (
    id SERIAL PRIMARY KEY,
    assessment_id UUID UNIQUE REFERENCES assessments(id) ON DELETE CASCADE,
    
    -- Physical features
    wpm FLOAT,
    pause_ratio FLOAT,
    filler_frequency FLOAT,
    volume_variance FLOAT,
    rhythm_stability FLOAT,
    
    -- Linguistic features
    sentence_length_variance FLOAT,
    vocabulary_diversity FLOAT,
    prompt_relevance FLOAT,
    clarity_score FLOAT,
    register_formality FLOAT,
    
    -- Cognitive features
    reason_density FLOAT,
    counterpoint_density FLOAT,
    logical_connector_density FLOAT,
    structure_completeness FLOAT,
    
    -- Social-emotional features
    audience_reference_frequency FLOAT,
    intention_clarity FLOAT,
    sentiment_compound FLOAT,
    
    -- Metadata
    quality_flag VARCHAR(20) CHECK (quality_flag IN ('good', 'fair', 'poor')),
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_features_assessment ON feature_signals(assessment_id);
```

#### `evidence_candidates`
```sql
CREATE TABLE evidence_candidates (
    id SERIAL PRIMARY KEY,
    assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
    candidate_id VARCHAR(20) NOT NULL,  -- "clip_0", "clip_1", etc.
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    type VARCHAR(50) NOT NULL,
    summary TEXT,
    features JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(assessment_id, candidate_id)
);

CREATE INDEX idx_candidates_assessment ON evidence_candidates(assessment_id);
CREATE INDEX idx_candidates_type ON evidence_candidates(type);
```

### Report Tables

#### `draft_reports`
```sql
CREATE TABLE draft_reports (
    id SERIAL PRIMARY KEY,
    assessment_id UUID UNIQUE REFERENCES assessments(id) ON DELETE CASCADE,
    
    -- Strand scores (JSON structure)
    physical_score JSONB NOT NULL,  -- {band, confidence, evidence_clips: [], justification}
    linguistic_score JSONB NOT NULL,
    cognitive_score JSONB NOT NULL,
    social_emotional_score JSONB NOT NULL,
    
    -- Feedback
    feedback JSONB NOT NULL,  -- {strengths: [], next_steps: [], goals: []}
    
    -- Metadata
    ai_model VARCHAR(50) NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_reviewed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_draft_reports_assessment ON draft_reports(assessment_id);
CREATE INDEX idx_draft_reports_generated ON draft_reports(generated_at DESC);
```

#### `signed_reports`
```sql
CREATE TABLE signed_reports (
    id SERIAL PRIMARY KEY,
    assessment_id UUID UNIQUE REFERENCES assessments(id) ON DELETE CASCADE,
    draft_id INTEGER REFERENCES draft_reports(id) ON DELETE SET NULL,
    
    -- Final scores (may differ from draft)
    physical_score JSONB NOT NULL,
    linguistic_score JSONB NOT NULL,
    cognitive_score JSONB NOT NULL,
    social_emotional_score JSONB NOT NULL,
    
    -- Final feedback
    feedback JSONB NOT NULL,
    teacher_notes TEXT,
    
    -- Signing
    signed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    signed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_signed_reports_assessment ON signed_reports(assessment_id);
CREATE INDEX idx_signed_reports_signed_by ON signed_reports(signed_by);
CREATE INDEX idx_signed_reports_signed_at ON signed_reports(signed_at DESC);
```

#### `audit_logs`
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES draft_reports(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(20) NOT NULL CHECK (
        action IN ('score_changed', 'clip_changed', 'feedback_edited', 'signed')
    ),
    field VARCHAR(50),
    old_value JSONB,
    new_value JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_report ON audit_logs(report_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);

-- Partition by month for large scale (future optimization)
-- CREATE TABLE audit_logs_y2026m03 PARTITION OF audit_logs...
```

### Benchmark Tables

#### `benchmark_versions`
```sql
CREATE TABLE benchmark_versions (
    version VARCHAR(20) NOT NULL,
    age_band VARCHAR(10) NOT NULL,
    mode VARCHAR(20) NOT NULL,
    definition JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (version, age_band, mode)
);

CREATE INDEX idx_benchmarks_active ON benchmark_versions(is_active);
CREATE INDEX idx_benchmarks_age_mode ON benchmark_versions(age_band, mode);
```

---

## Indexes Summary

### Performance-Critical Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| assessments | `idx_assessments_cohort_status` | Teacher dashboard queries |
| assessments | `idx_assessments_student` | Student history queries |
| assessments | `idx_assessments_status` | Processing queue queries |
| draft_reports | `idx_draft_reports_generated` | Recent reports listing |
| audit_logs | `idx_audit_logs_timestamp` | Audit trail queries |
| transcripts | `idx_transcripts_fts` | Full-text search on transcripts |

### Foreign Key Indexes (Auto-created, but explicit for documentation)

| Table | Column | References |
|-------|--------|------------|
| users | school_id | schools(id) |
| students | user_id | users(id) |
| cohorts | teacher_id | users(id) |
| enrollments | student_id | students(id) |
| enrollments | cohort_id | cohorts(id) |
| assessments | student_id | students(id) |
| assessments | cohort_id | cohorts(id) |
| recordings | assessment_id | assessments(id) |
| transcripts | assessment_id | assessments(id) |
| feature_signals | assessment_id | assessments(id) |
| evidence_candidates | assessment_id | assessments(id) |
| draft_reports | assessment_id | assessments(id) |
| signed_reports | assessment_id | assessments(id) |
| signed_reports | draft_id | draft_reports(id) |
| signed_reports | signed_by | users(id) |
| audit_logs | report_id | draft_reports(id) |
| audit_logs | user_id | users(id) |

---

## Constraints & Validation

### Check Constraints

```sql
-- Band values must be valid
ALTER TABLE draft_reports 
ADD CONSTRAINT chk_physical_band 
CHECK (physical_score->>'band' IN ('emerging', 'expected', 'exceeding', 'insufficient_evidence'));

-- Confidence values between 0 and 1
ALTER TABLE draft_reports 
ADD CONSTRAINT chk_physical_confidence 
CHECK ((physical_score->>'confidence')::float BETWEEN 0 AND 1);

-- Time values must be positive
ALTER TABLE evidence_candidates 
ADD CONSTRAINT chk_positive_times 
CHECK (start_time >= 0 AND end_time > start_time);

-- File sizes must be positive
ALTER TABLE recordings 
ADD CONSTRAINT chk_positive_file_size 
CHECK (file_size_bytes > 0);
```

---

## Data Retention & Archival

### Retention Policies

| Data Type | Retention Period | Action |
|-----------|-----------------|--------|
| Video recordings | 7 years | S3 Glacier after 90 days |
| Transcripts | 7 years | Keep in DB |
| Feature signals | 1 year | Archive to S3 after 1 year |
| Draft reports | 7 years | Soft delete only |
| Signed reports | Permanent | Never delete |
| Audit logs | 7 years | Partition and archive |

### Soft Delete Implementation

```sql
-- Add soft delete columns to key tables
ALTER TABLE assessments ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE students ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;

-- Create view for active records
CREATE VIEW active_assessments AS
SELECT * FROM assessments WHERE deleted_at IS NULL;

-- Create partial index for active records
CREATE INDEX idx_assessments_active ON assessments(id) WHERE deleted_at IS NULL;
```

---

## Migration Strategy

### Initial Migration Order

1. `0001_initial.py` - Schools, Users (auth tables)
2. `0002_students.py` - Students
3. `0003_cohorts.py` - Cohorts and Enrollments
4. `0004_assessments.py` - Assessments and Recordings
5. `0005_analysis.py` - Transcripts, Features, Evidence
6. `0006_reports.py` - Draft, Signed Reports
7. `0007_audit.py` - Audit Logs
8. `0008_benchmarks.py` - Benchmark Versions

### Data Migration for BDL

```python
# migrations/0008_load_benchmarks.py
from django.db import migrations

def load_benchmarks(apps, schema_editor):
    BenchmarkVersion = apps.get_model('benchmarks', 'BenchmarkVersion')
    
    # Load from JSON files
    import json
    from pathlib import Path
    
    bdl_dir = Path(__file__).parent / 'bdl'
    for file_path in bdl_dir.glob('**/*.json'):
        with open(file_path) as f:
            definition = json.load(f)
        
        BenchmarkVersion.objects.get_or_create(
            version=definition['version'],
            age_band=definition['age_band'],
            mode=definition['mode'],
            defaults={'definition': definition}
        )

class Migration(migrations.Migration):
    dependencies = [
        ('benchmarks', '0007_benchmarkversion'),
    ]
    
    operations = [
        migrations.RunPython(load_benchmarks),
    ]
```
