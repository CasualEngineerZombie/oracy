# Tech Stack

## Overview

| Layer | Technology | Version/Notes |
|-------|------------|---------------|
| Frontend | React + TypeScript | v18+, Vite build |
| Backend | Django + Django REST Framework | v5.0+, Python 3.12 |
| Database | PostgreSQL | 15+ |
| Cache | Redis | 7+ |
| Message Queue | Redis (Celery) or AWS SQS | - |
| AI/ML | OpenAI API, AWS Transcribe, Anthropic | Latest stable |
| Infrastructure | AWS (ECS, RDS, S3, CloudFront) | - |
| DevOps | Docker, GitHub Actions, Terraform | - |

---

## Frontend Stack (React)

### Core Framework
- **React 18+**: Modern React with concurrent features
- **TypeScript 5+**: Type safety throughout
- **Vite**: Fast development builds and optimized production bundles

### State Management
- **Zustand**: Lightweight state management for global state
- **React Query (TanStack Query)**: Server state management, caching, synchronization
- **React Hook Form**: Form state management with validation

### Routing
- **React Router v6**: Client-side routing with lazy loading

### UI Component Library
- **Tailwind CSS**: Utility-first CSS framework
- **Headless UI**: Unstyled, accessible UI primitives
- **Lucide React**: Icon library

### Video & Media
- **MediaRecorder API**: Native browser recording
- **React Player**: Video playback component
- **wavesurfer.js**: Audio waveform visualization

### HTTP Client
- **Axios**: HTTP requests with interceptors for auth

### Authentication
- **JWT (jsonwebtoken)**: Token-based authentication
- **react-jwt**: JWT decoding in React

### Testing
- **Vitest**: Unit testing framework
- **React Testing Library**: Component testing
- **Playwright**: E2E testing

### Build Tools
- **Vite**: Build tool and dev server
- **ESLint**: Code linting
- **Prettier**: Code formatting

---

## Backend Stack (Django)

### Core Framework
- **Django 5.0+**: Web framework
- **Django REST Framework 3.15+**: REST API framework
- **Django Channels**: WebSocket support for real-time updates
- **Python 3.12**: Latest Python with performance improvements

### Database & ORM
- **PostgreSQL 15+**: Primary database
- **psycopg3**: PostgreSQL adapter
- **django-migrations**: Schema versioning

### Background Tasks
- **Celery 5.3+**: Distributed task queue
- **Redis**: Celery message broker and result backend
- **django-celery-beat**: Periodic task scheduler

### Authentication & Security
- **django-cors-headers**: CORS handling
- **PyJWT**: JWT token generation/validation
- **django-ratelimit**: API rate limiting
- **django-guardian**: Object-level permissions
- **argon2-cffi**: Secure password hashing

### API & Documentation
- **drf-spectacular**: OpenAPI 3 schema generation
- **django-filter**: Query parameter filtering

### Media & Storage
- **django-storages**: Storage backends
- **boto3**: AWS SDK for Python (S3 interaction)

### AI/ML Integration
- **openai**: OpenAI Python client
- **anthropic**: Anthropic Python client
- **boto3**: AWS SDK (Transcribe, etc.)

### Audio Processing (Feature Extraction)
- **librosa**: Audio analysis (tempo, rhythm, spectral features)
- **pydub**: Audio manipulation
- **soundfile**: Audio file I/O
- **numpy**: Numerical computing

### Text Processing
- **spaCy**: NLP (sentence parsing, tokenization)
- **NLTK**: Natural language toolkit
- **textstat**: Readability metrics

### Data Validation
- **pydantic**: Data validation using Python type hints
- **marshmallow**: Object serialization

### Testing
- **pytest**: Testing framework
- **pytest-django**: Django pytest integration
- **factory-boy**: Test data factories
- **freezegun**: Time manipulation in tests
- **responses**: Mock HTTP requests
- **coverage.py**: Code coverage

### Monitoring & Logging
- **sentry-sdk**: Error tracking
- **structlog**: Structured logging
- **django-prometheus**: Metrics export

---

## Database Stack

### Primary Database
- **PostgreSQL 15+** (AWS RDS)
- Multi-AZ deployment for high availability
- Automated backups (7-day retention)
- Encryption at rest (KMS)

### Key PostgreSQL Extensions
- **uuid-ossp**: UUID generation
- **pg_trgm**: Trigram similarity (fuzzy search)
- **btree_gist**: GiST index operator

### Cache
- **Redis 7+** (AWS ElastiCache)
- Session storage
- Celery broker
- API response caching
- Real-time pub/sub (WebSocket)

### Search (Future)
- **Elasticsearch 8+** or **OpenSearch**
- Full-text search for transcripts
- Assessment history search

---

## AI/ML Services Stack

### Speech-to-Text (STT)

| Service | Use Case | Pros | Cons |
|---------|----------|------|------|
| **OpenAI Whisper API** | Primary STT | High accuracy, timestamp support, cost-effective | External dependency |
| **AWS Transcribe** | Fallback/Alternative | AWS native, speaker diarization (future) | Higher cost |
| **Whisper (self-hosted)** | Future option | Full control, no external calls | Infrastructure overhead |

**Decision**: Start with OpenAI Whisper API, abstract behind service interface for easy swapping.

### Large Language Models (LLM)

| Model | Use Case | Context Window | Cost |
|-------|----------|----------------|------|
| **OpenAI GPT-4o** | Primary scoring | 128K | Medium |
| **Anthropic Claude 3.5 Sonnet** | Fallback/comparison | 200K | Medium |
| **OpenAI GPT-4o-mini** | Lightweight tasks | 128K | Low |

**Decision**: GPT-4o for main scoring pipeline (structured output), Claude for evaluation/comparison.

### Audio Feature Extraction

| Library | Purpose |
|---------|---------|
| **librosa** | Tempo, rhythm, spectral features, pause detection |
| **pydub** | Audio slicing, format conversion, volume analysis |
| **webrtcvad** | Voice activity detection (silence/pause detection) |

### Text Feature Extraction

| Library | Purpose |
|---------|---------|
| **spaCy** | Sentence segmentation, POS tagging, NER |
| **NLTK** | Tokenization, n-gram analysis |
| **textstat** | Readability scores, complexity metrics |
| **scikit-learn** | TF-IDF, cosine similarity (prompt relevance) |

---

## Infrastructure Stack (AWS)

### Compute
- **Amazon ECS (Fargate)**: Container orchestration (serverless)
- **AWS Lambda**: Optional for lightweight processing tasks
- **Application Load Balancer (ALB)**: Traffic distribution

### Storage
- **Amazon S3**: Video/audio storage, static assets
  - S3 Standard (frequent access)
  - S3 Intelligent-Tiering (cost optimization)
  - S3 Glacier (archival)
- **Amazon EFS**: Shared file system for ECS tasks (if needed)

### Database
- **Amazon RDS (PostgreSQL)**: Managed relational database
- **Amazon ElastiCache (Redis)**: Managed caching

### Networking
- **Amazon VPC**: Isolated network environment
- **CloudFront**: CDN for static assets and video streaming
- **Route 53**: DNS management

### Security
- **AWS WAF**: Web application firewall
- **AWS Secrets Manager**: Credential management
- **AWS KMS**: Encryption key management
- **AWS Certificate Manager**: SSL/TLS certificates

### Monitoring & Logging
- **Amazon CloudWatch**: Metrics, logs, alarms
- **AWS X-Ray**: Distributed tracing
- **AWS CloudTrail**: API audit logging

### CI/CD
- **GitHub Actions**: Build and test automation
- **Amazon ECR**: Container registry
- **AWS CodeDeploy** or **GitHub Actions**: Deployment

---

## DevOps & Tooling

### Containerization
- **Docker**: Application containerization
- **Docker Compose**: Local development environment

### Infrastructure as Code
- **Terraform**: AWS infrastructure provisioning
- **Terragrunt**: Terraform wrapper for DRY configs

### Version Control
- **Git**: Source control
- **GitHub**: Repository hosting, PR reviews
- **GitHub Actions**: CI/CD pipelines

### Local Development
- **Docker Compose**: Full stack locally
- **pre-commit**: Git hooks for code quality
- **Makefile**: Common development tasks

### Code Quality
- **Black**: Python code formatter
- **isort**: Python import sorting
- **flake8**: Python linting
- **mypy**: Python type checking
- **pylint**: Additional Python linting

### API Documentation
- **OpenAPI 3.0**: API specification
- **Swagger UI**: Interactive API docs
- **Redoc**: Alternative API docs

---

## Package Managers

### Frontend
- **npm** or **pnpm**: JavaScript package manager (recommend pnpm)
- **package.json**: Dependency manifest

### Backend
- **uv** or **poetry**: Modern Python package managers (recommend uv)
- **pyproject.toml**: Dependency and project metadata

---

## Browser Support

### Minimum Supported Versions
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Required Features
- MediaRecorder API
- WebRTC (for recording)
- ES2020+ JavaScript
- CSS Grid & Flexbox

---

## Cost Considerations

### Development (Est. Monthly)
| Service | Cost |
|---------|------|
| AWS ECS Fargate (dev) | $50-100 |
| RDS PostgreSQL (db.t3.micro) | $15 |
| ElastiCache Redis | $15 |
| S3 Storage | $5-20 |
| OpenAI API | Usage-based |
| **Total** | **$100-200 + AI usage** |

### Production (Est. Monthly - Small Scale)
| Service | Cost |
|---------|------|
| AWS ECS Fargate | $200-500 |
| RDS PostgreSQL (Multi-AZ) | $100-300 |
| ElastiCache Redis | $50-100 |
| S3 Storage + Transfer | $100-500 |
| CloudFront CDN | $50-200 |
| OpenAI API | $500-2000 (usage-based) |
| **Total** | **$1000-3500 + AI usage** |
