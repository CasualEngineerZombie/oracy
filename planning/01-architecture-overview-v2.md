# Architecture Overview V2 (Cost-Optimized)

## System Architecture Diagram (V2)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    CLIENT                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │  React Frontend                                                               │ │
│  │  • Video Recorder (WebRTC)                                                    │ │
│  │  • Assessment Dashboard                                                       │ │
│  │  • Teacher Review Interface                                                   │ │
│  │  • PDF Export                                                                 │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              CLOUDFRONT / ALB                                       │
│  • Static assets caching                                                            │
│  • Video streaming (signed URLs)                                                    │
│  • API routing                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AWS ECS FARGATE                                        │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │  Django API (256 CPU / 512 MB)                                                │ │
│  │  • REST API endpoints                                                         │ │
│  │  • WebSocket connections                                                      │ │
│  │  • Request handling                                                           │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │  Celery Workers (512 CPU / 1024 MB) - Fargate Spot                            │ │
│  │  • AI pipeline orchestration                                                  │ │
│  │  • Async task processing                                                      │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│    RDS PostgreSQL       │ │    ElastiCache Redis    │ │      S3 Buckets         │
│    (db.t3.small)        │ │    (cache.t3.micro)     │ │                         │
│  • Application data     │ │  • Celery broker        │ │  • Video recordings     │
│  • Transcripts          │ │  • Session cache        │ │  • Static assets        │
│  • Reports              │ │  • Result backend       │ │  • Exports              │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL AI SERVICES (V2)                                 │
│                                                                                     │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │   RunPod Serverless GPU         │  │   OpenRouter                            │  │
│  │   (WhisperX + distil-large-v3)  │  │   (Aggregated LLM APIs)                 │  │
│  │                                 │  │                                         │  │
│  │  • WhisperX with batching       │  │  • Google Gemini Flash                  │  │
│  │  • distil-large-v3 (6x speed)   │  │  • Anthropic Claude Haiku               │  │
│  │  • int8 quantization (2.8GB)    │  │  • OpenAI GPT-4o-mini                   │  │
│  │  • ~$0.0003/min vs $0.006/min   │  │  • ~$0.00035/1K vs $0.005/1K            │  │
│  └─────────────────────────────────┘  └─────────────────────────────────────────┘  │
│                                                                                     │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │   Vast.ai (Optional Backup)     │  │   Ollama (Local Fallback)               │  │
│  │   (Dedicated GPU)               │  │   (Self-Hosted LLM)                     │  │
│  │                                 │  │                                         │  │
│  │  • RTX 3090 instances           │  │  • llama3.2:3b model                    │  │
│  │  • Batch size 16 processing     │  │  • Zero API cost                        │  │
│  │  • ~$0.30/hour                  │  │  • Development/testing                  │  │
│  └─────────────────────────────────┘  └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## High-Level Data Flow

### 1. Recording Upload Flow

```
Student/Teacher     React App         S3 (Presigned)         ECS
     │                  │                    │                │
     │ 1. Request URL   │                    │                │
     │─────────────────▶│                    │                │
     │                  │ 2. Get presigned   │                │
     │                  │───────────────────▶│                │
     │                  │ 3. Return URL      │                │
     │                  │◀───────────────────│                │
     │ 4. Upload video  │                    │                │
     │───────────────────────────────────────▶│                │
     │                  │ 5. Confirm upload  │                │
     │                  │─────────────────────────────────────▶│
     │                  │                    │                │ 6. Queue AI pipeline
     │                  │                    │                │──────▶ Redis
```

### 2. AI Processing Pipeline (V2)

```
Celery Worker      RunPod GPU         Feature Extractor      OpenRouter
     │                  │                    │                │
     │ 1. Extract audio │                    │                │
     │──────▶ ffmpeg    │                    │                │
     │                  │                    │                │
     │ 2. Transcribe    │                    │                │
     │─────────────────▶│ WhisperX           │                │
     │                  │ distil-large-v3    │                │
     │                  │ int8 quantized     │                │
     │                  │ batch_size=4       │                │
     │ 3. Return transcript                 │                │
     │◀─────────────────│ (forced alignment) │                │
     │                  │                    │                │
     │ 4. Extract features                  │                │
     │─────────────────────────────────────▶│                │
     │  librosa, spaCy, VADER               │                │
     │                  │                    │                │
     │ 5. Score with LLM                    │                │
     │────────────────────────────────────────────────────────▶│
     │                  │                    │                │ (Gemini/Claude)
     │ 6. Generate report                   │                │
     │◀────────────────────────────────────────────────────────│
     │                  │                    │                │
     │ 7. Store results                     │                │
     │──────▶ PostgreSQL                    │                │
```

### 3. Teacher Review Flow (Unchanged)

```
Teacher Opens ──▶  View AI Draft  ──▶  Edit Scores/  ──▶  Add Private  ──▶  Sign Off
Assessment         Report             Evidence/          Notes             (Audit Trail
                                       Feedback                           Captured)
```

---

## Core Components

### Frontend (React)
**Unchanged from V1**
- **Authentication Module**: JWT-based auth with role-based access
- **Recording Component**: WebRTC-based video/audio capture
- **Dashboard**: Assessment overview, analytics, cohort views
- **Review Interface**: Side-by-side video player with editing tools
- **PDF Export**: Client-side PDF generation for reports

### Backend (Django)
**Unchanged structure, modified AI service integrations**
- **API Layer**: Django REST Framework for all endpoints
- **WebSocket Layer**: Django Channels for real-time updates
- **Task Queue**: Celery + Redis for async AI processing
- **Admin Interface**: Built-in Django admin for data management
- **Core Apps**:
  - `users`: Authentication and authorization
  - `students`: Student profiles and cohort management
  - `assessments`: Recording metadata and workflow
  - `analysis`: AI pipeline orchestration (V2: RunPod + OpenRouter)
  - `reports`: Draft and signed report management
  - `benchmarks`: BDL versioning and scoring logic

### AI Pipeline (V2 Changes)

| Component | V1 (Cloud APIs) | V2 (Cost-Optimized) | Savings |
|-----------|-----------------|---------------------|---------|
| **STT Service** | OpenAI Whisper API / AWS Transcribe | RunPod Serverless GPU (WhisperX + distil-large-v3) | 95% |
| **Feature Extractor** | librosa, NLTK, spaCy (local) | librosa, NLTK, spaCy (local) | No change |
| **Benchmark Engine** | JSON-based BDL interpreter (local) | JSON-based BDL interpreter (local) | No change |
| **Evidence Generator** | Deterministic selection (local) | Deterministic selection (local) | No change |
| **LLM Scorer** | OpenAI GPT-4o / Claude API | OpenRouter (Gemini/Claude Haiku) | 80% |

**WhisperX Key Features:**
- **distil-large-v3**: 6x faster than large-v3, <1% accuracy loss
- **int8 quantization**: 40% VRAM reduction (~2.8GB vs ~10GB)
- **Batch processing**: 4-16 files simultaneously
- **Forced alignment**: Character-level accurate word timestamps
- **Word-level timestamps**: More precise than Whisper alone

### Infrastructure (AWS V2)

| Component | V1 Spec | V2 Spec | Savings |
|-----------|---------|---------|---------|
| **Compute** | ECS Fargate (larger tasks) | ECS Fargate Spot (smaller tasks) | 50% |
| **Database** | RDS PostgreSQL (db.t3.medium) | RDS PostgreSQL (db.t3.small) | 50% |
| **Cache** | ElastiCache (cache.t3.micro) | ElastiCache (cache.t3.micro) | No change |
| **Storage** | S3 Standard | S3 Intelligent-Tiering | 30% |
| **CDN** | CloudFront | CloudFront | No change |

---

## Technology Decisions

### Why React + Django?
**Unchanged from V1**
- **React**: Component reusability, strong ecosystem, excellent video/media handling
- **Django**: Rapid development, robust ORM, built-in admin, excellent Python ecosystem for ML
- **Separation**: Allows independent scaling of frontend and backend

### Why AWS + External GPU Services?

**V2 Rationale:**
- **RunPod Serverless GPU**: 4-5x cheaper than OpenAI Whisper API for transcription
- **OpenRouter**: Aggregates multiple LLM providers for best pricing (80% savings vs direct OpenAI)
- **S3 Intelligent-Tiering**: Automatic cost optimization for video storage
- **Fargate Spot**: 70% discount on compute for fault-tolerant workloads
- **RDS db.t3.small**: Right-sized for MVP, upgradeable for scale

### AI Model Strategy (V2)

| Phase | V1 Strategy | V2 Strategy | Reason |
|-------|-------------|-------------|--------|
| **MVP** | External APIs only | Self-hosted STT + OpenRouter LLM | Cost reduction (70% savings) |
| **Post-MVP** | Train custom models | Train custom models + keep cost-optimized external services | Flexibility |
| **Hybrid** | Deterministic + LLM | Deterministic + LLM (with local fallback) | Reliability |

---

## Scalability Considerations

### Horizontal Scaling

**Unchanged principles:**
- Stateless Django backend - can run multiple containers
- Celery workers scale independently based on queue depth
- S3 handles unlimited video storage

**V2 Additions:**
- RunPod endpoint auto-scales (0-3 workers)
- Vast.ai instances can be spun up for high volume
- Ollama local fallback for zero-cost overflow

### Performance Optimization

**Unchanged:**
- Video upload uses presigned URLs (direct to S3)
- AI processing is fully asynchronous
- Response caching for benchmark definitions
- CDN for video streaming and static assets

**V2 Considerations:**
- RunPod cold start: ~2-5 seconds (use flashboot)
- Vast.ai startup: ~1-2 minutes (plan ahead)
- Ollama inference: Slower but zero cost

### Cost Optimization (New)

```
Cost per Assessment Breakdown (V2):
├── STT (RunPod):           $0.04  (2 min @ $0.0005/min)  [was $0.12]
├── LLM (OpenRouter):       $0.10  (~100K tokens)         [was $0.50]
├── Compute (ECS):          $0.05  (Fargate Spot)         [was $0.10]
├── Storage (S3):           $0.01  (Intelligent-Tiering) [was $0.02]
└── Total:                  $0.20                          [was $0.74]
                            
Savings: 73% vs V1 architecture
```

---

## Data Retention

**Unchanged from V1:**
- Video files: 7-year retention (educational records)
- Audit logs: Permanent
- AI processing artifacts: 1 year
- Soft deletes for all records (compliance)

**V2 Addition:**
- Temporary audio files: 7 days (S3 lifecycle)
- RunPod job logs: 30 days

---

## Security Architecture

### Data Protection
**Unchanged:**
- All data encrypted at rest (S3, RDS)
- TLS 1.3 for all communications
- Video access via time-limited presigned URLs only
- No public video URLs ever

**V2 Addition:**
- RunPod API keys stored in AWS Secrets Manager
- OpenRouter API keys rotated monthly
- Vast.ai instance access restricted by IP

### Access Control
**Unchanged:**
- Role-based: Admin, Teacher, Student, Parent (future)
- Row-level permissions (teachers only see their students)
- API key management for external services

### External Service Security

```python
# Secure API key handling for RunPod/OpenRouter
import boto3
from botocore.exceptions import ClientError

def get_ai_service_credentials(service: str) -> dict:
    """Retrieve credentials from AWS Secrets Manager."""
    secret_name = f"oracy/{service}-credentials"
    region_name = "ap-southeast-1"
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        logger.error(f"Failed to retrieve {service} credentials")
        raise

# Usage
runpod_creds = get_ai_service_credentials('runpod')
openrouter_creds = get_ai_service_credentials('openrouter')
```

### Compliance
**Unchanged:**
- GDPR-compliant data handling
- Audit trail for all modifications
- Right to erasure support
- Data residency controls (future)

---

## Migration from V1 to V2

### Step 1: Infrastructure Setup
1. Create RunPod account and deploy Whisper endpoint
2. Create OpenRouter account
3. Update ECS task definitions with new environment variables
4. Add Secrets Manager entries for new API keys

### Step 2: Service Implementation
1. Implement `RunPodWhisperService`
2. Implement `OpenRouterService`
3. Add fallback chains (Vast.ai, Ollama)
4. Update Celery tasks to use new services

### Step 3: Validation
1. Run parallel V1/V2 transcription (measure WER)
2. Run parallel V1/V2 scoring (measure correlation)
3. Load test with 50 assessments
4. Calculate actual cost savings

### Step 4: Cutover
1. Switch production to V2 services
2. Monitor error rates and latency
3. Keep V1 as emergency fallback for 2 weeks
4. Decommission V1 after validation

---

## Success Metrics

### Cost Targets
| Metric | V1 | V2 Target | V2 Actual |
|--------|-----|-----------|-----------|
| Cost per assessment | $0.74 | $0.20 | TBD |
| Monthly infra (1K assessments) | $1,750 | $700 | TBD |
| STT cost per minute | $0.006 | $0.0005 | TBD |
| LLM cost per 1K tokens | $0.005 | $0.001 | TBD |

### Quality Targets
| Metric | Target |
|--------|--------|
| STT Word Error Rate | < 5% vs OpenAI |
| LLM Score Correlation | > 0.95 vs GPT-4o |
| End-to-end Latency | < 3 min (95th percentile) |
| System Availability | > 99.5% |

---

## Appendix: Service Comparison

### STT Services

| Service | Cost/min | WER | VRAM | Latency | Best For |
|---------|----------|-----|------|---------|----------|
| OpenAI Whisper API | $0.006 | 16.7% | N/A | Fast | Baseline |
| AWS Transcribe | $0.024 | 18.2% | N/A | Medium | AWS native |
| **RunPod (WhisperX)** | **$0.0003** | **17.2%** | **~2.8GB** | Medium | **Production** |
| Vast.ai (WhisperX) | $0.001 | 17.2% | ~2.8GB | Fast | High volume |
| Local CPU (WhisperX) | Free | 20%+ | N/A | Slow | Development |

**WhisperX Advantages:**
- **distil-large-v3**: 6x faster than large-v3, only 0.5% WER loss
- **int8 quantization**: 40% VRAM reduction (2.8GB vs 10GB)
- **Batch processing**: 4-16 files simultaneously
- **Forced alignment**: Character-level accurate word timestamps

### LLM Services

| Service | Cost/1K input | Cost/1K output | Quality | Best For |
|---------|---------------|----------------|---------|----------|
| OpenAI GPT-4o | $0.005 | $0.015 | 98% | Baseline |
| OpenRouter Gemini Flash | $0.00035 | $0.00105 | 92% | **Production** |
| OpenRouter Claude Haiku | $0.0008 | $0.004 | 94% | Balanced |
| Ollama (local) | Free | Free | 85% | Development |
