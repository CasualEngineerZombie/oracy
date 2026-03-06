# Oracy AI

> **Private SaaS Platform** — Confidential & Proprietary  
> AI-powered oracy assessment for educational institutions

---

## Overview

Oracy AI is a closed-source SaaS platform that produces teacher-verifiable, inspection-grade evidence of student oracy progression from video/audio recordings. The system uses a multi-stage AI pipeline to analyze recordings and generate structured assessment reports across four strands: Physical, Linguistic, Cognitive, and Social-emotional.

### Key Capabilities

- **Automated Assessment**: AI analyzes student recordings and generates draft scores with timestamped evidence clips
- **Teacher Verification**: Human-in-the-loop workflow allows teachers to review, edit, and sign off on assessments
- **Cohort Analytics**: Track progression over time with strand-by-strand breakdowns and distribution charts
- **Export & Reporting**: Generate inspection-ready PDF reports and CSV exports for school MIS integration
- **Multimodal Analysis**: Processes both audio (speech patterns) and video (physical delivery) signals

---

## Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │◄────►│   Server    │◄────►│  AI/ML      │
│  (React)    │      │  (Django)   │      │  Pipeline   │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                    ┌───────┴───────┐
                    ▼               ▼
              ┌─────────┐     ┌─────────┐
              │PostgreSQL│    │   S3    │
              └─────────┘     └─────────┘
```

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | React 18 + TypeScript + Vite | Teacher dashboard, recording interface, review tools |
| Backend | Django 5 + DRF | API, authentication, orchestration |
| AI Pipeline | Python + OpenAI/Anthropic APIs | STT, feature extraction, scoring |
| Database | PostgreSQL 15 | Primary data store |
| Cache/Queue | Redis 7 | Celery broker, caching |
| Storage | AWS S3 | Video files, exports |
| Infrastructure | AWS ECS Fargate | Containerized deployment |

---

## Quick Start

### Prerequisites

- **OS**: Windows 11, macOS 13+, or Linux (Ubuntu 22.04+)
- **Docker Desktop**: 4.25+ with WSL2 backend (Windows)
- **Node.js**: 20.x LTS
- **Python**: 3.12+
- **uv**: Modern Python package manager
- **AWS CLI**: 2.x configured with credentials
- **Git**: 2.40+

### Installation

```bash
# Clone the repository
git clone <internal-repository-url>
cd oracy

# Run initial setup
# See execution/01-setup-and-installation.md for detailed steps

# Configure environment
# See execution/02-environment-configuration.md

# Start development servers
# See execution/03-running-locally.md
```

### Development Commands

```bash
# Start all services (Docker)
docker-compose up -d

# Run database migrations
cd server && python manage.py migrate

# Start backend (Django)
cd server && python manage.py runserver

# Start frontend (React)
cd client && npm run dev

# Run AI pipeline locally
cd llm && python -m pipeline.worker
```

---

## Project Structure

```
oracy/
├── client/                 # React frontend (TypeScript + Vite)
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Route pages
│   │   ├── hooks/          # Custom React hooks
│   │   ├── stores/         # Zustand state management
│   │   └── api/            # API client
│   └── package.json
│
├── server/                 # Django backend
│   ├── apps/
│   │   ├── users/          # Authentication & authorization
│   │   ├── students/       # Student profiles & cohorts
│   │   ├── assessments/    # Recording metadata & workflow
│   │   ├── analysis/       # AI pipeline orchestration
│   │   ├── reports/        # Draft & signed report management
│   │   └── benchmarks/     # BDL versioning & scoring logic
│   ├── config/             # Django settings
│   └── requirements/
│
├── llm/                    # AI/ML pipeline services
│   ├── extraction/         # Feature extraction
│   ├── scoring/            # LLM scoring engine
│   ├── evidence/           # Evidence candidate generation
│   └── workers/            # Celery task workers
│
├── planning/               # Architecture & planning documentation
│   ├── 01-architecture-overview.md
│   ├── 02-tech-stack.md
│   ├── 03-aws-infrastructure.md
│   ├── 04-ai-ml-pipeline.md
│   └── ...
│
├── execution/              # Developer execution guides
│   ├── 01-setup-and-installation.md
│   ├── 02-environment-configuration.md
│   ├── 03-running-locally.md
│   └── ...
│
└── scripts/                # Utility scripts
    ├── combine_markdown.py
    └── md_to_pdf.py
```

---

## Documentation

### Planning Documents

| Document | Description |
|----------|-------------|
| [Planning Index](planning/index.md) | Executive summary & navigation |
| [Architecture](planning/01-architecture-overview.md) | System architecture & data flow |
| [Tech Stack](planning/02-tech-stack.md) | Technology choices & rationale |
| [AWS Infrastructure](planning/03-aws-infrastructure.md) | VPC, ECS, RDS, S3 configuration |
| [AI/ML Pipeline](planning/04-ai-ml-pipeline.md) | Speech-to-text, scoring, evidence generation |
| [Backend Structure](planning/05-backend-structure.md) | Django apps, API design, background jobs |
| [Frontend Structure](planning/06-frontend-structure.md) | React components, state management |
| [Database Schema](planning/07-database-schema.md) | Entity relationships & migrations |
| [Security & Compliance](planning/08-security-compliance.md) | GDPR, data protection, audit trails |
| [Development Roadmap](planning/09-development-roadmap.md) | Timeline & milestones |
| [Deployment Strategy](planning/10-deployment-strategy.md) | CI/CD, environments, rollback |

### Execution Guides

| Document | Purpose |
|----------|---------|
| [Setup & Installation](execution/01-setup-and-installation.md) | Initial setup & dependencies |
| [Environment Configuration](execution/02-environment-configuration.md) | Environment variables & secrets |
| [Running Locally](execution/03-running-locally.md) | Daily development workflow |
| [Database Migrations](execution/04-database-migrations.md) | Schema changes |
| [AI Pipeline Execution](execution/05-ai-pipeline-execution.md) | Testing AI features |
| [Testing Procedures](execution/06-testing-procedures.md) | Test execution |
| [Deployment](execution/07-deployment-execution.md) | Release procedures |
| [Troubleshooting](execution/08-troubleshooting.md) | Common issues |

---

## Development Workflow

### Branching Strategy

- `main` — Production-ready code
- `staging` — Pre-production testing
- `develop` — Integration branch
- `feature/*` — Feature development
- `hotfix/*` — Production fixes

### Commit Standards

Follow conventional commits:
```
feat: add teacher sign-off workflow
fix: resolve video upload timeout
refactor: simplify assessment scoring logic
docs: update API documentation
test: add integration tests for AI pipeline
```

### Testing

```bash
# Run backend tests
cd server && pytest

# Run frontend tests
cd client && npm test

# Run E2E tests
cd client && npx playwright test

# Run AI pipeline tests
cd llm && pytest tests/
```

---

## Environment Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/oracy

# AWS
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=eu-west-2
S3_BUCKET=oracy-uploads-prod

# AI Services
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Security
SECRET_KEY=xxx
JWT_SECRET=xxx

# Redis
REDIS_URL=redis://localhost:6379/0
```

See [execution/02-environment-configuration.md](execution/02-environment-configuration.md) for complete configuration details.

---

## Deployment

### Environments

| Environment | Purpose | URL |
|-------------|---------|-----|
| Development | Local development | http://localhost:3000 / http://localhost:8000 |
| Staging | Pre-production testing | https://staging.oracy.ai |
| Production | Live SaaS platform | https://app.oracy.ai |

### Deployment Process

1. Merge feature branch to `develop`
2. CI/CD runs tests and builds
3. Deploy to staging for QA
4. Create PR from `develop` to `main`
5. After approval, deploy to production

See [execution/07-deployment-execution.md](execution/07-deployment-execution.md) for detailed deployment procedures.

---

## Security & Compliance

### Data Protection

- **Encryption at Rest**: All data encrypted (AES-256)
- **Encryption in Transit**: TLS 1.3 for all connections
- **PII Handling**: GDPR-compliant data retention policies
- **Access Control**: Role-based permissions with audit logging
- **Video Retention**: 7-year retention for educational records

### Compliance Standards

- GDPR (UK/EU data protection)
- UK Data Protection Act 2018
- School data handling policies
- Ofsted inspection requirements

See [planning/08-security-compliance.md](planning/08-security-compliance.md) for full security documentation.

---

## Support & Contact

### Internal Resources

- **Technical Documentation**: See `/planning` and `/execution` directories
- **API Documentation**: Available at `/api/docs/` (when server running)
- **Issue Tracker**: Internal project management system

### Team Contacts

| Role | Contact |
|------|---------|
| Product Owner | [Internal contact] |
| Tech Lead | [Internal contact] |
| DevOps | [Internal contact] |
| AI/ML Lead | [Internal contact] |

---

## Legal Notice

**© 2026 Oracy AI. All Rights Reserved.**

This software is proprietary and confidential. Unauthorized copying, distribution, modification, or use of this software, via any medium, is strictly prohibited without prior written consent from Oracy AI.

This repository and its contents are the exclusive property of Oracy AI. Access is restricted to authorized personnel only.

---

## Changelog

See internal release notes for version history and change details.
