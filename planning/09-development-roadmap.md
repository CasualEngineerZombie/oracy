# Development Roadmap

## MVP Timeline (2 Weeks)

### Week 1: Foundation & AI Pipeline

#### Day 1-2: Project Setup & Infrastructure
**Deliverables:**
- [ ] Initialize Django project with apps structure
- [ ] Initialize React project with Vite + TypeScript
- [ ] Docker Compose for local development
- [ ] AWS dev environment setup (VPC, ECS cluster, RDS)
- [ ] CI/CD pipeline skeleton (GitHub Actions)

**Key Decisions:**
- Django project structure finalized
- Database schema v1 implemented
- AWS region selected (ap-southeast-1 for initial dev)

---

#### Day 3-4: Authentication & Core Models
**Deliverables:**
- [ ] User authentication (JWT) - backend
- [ ] User login/logout - frontend
- [ ] User model with roles (admin, teacher)
- [ ] School model
- [ ] Database migrations

**APIs:**
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/users/me/`

**Frontend:**
- Login page
- Auth context/store
- Protected routes

---

#### Day 5-6: Student Management & Assessment Creation
**Deliverables:**
- [ ] Student model and CRUD APIs
- [ ] Cohort model and enrollment
- [ ] Assessment creation flow
- [ ] Prompt templates

**APIs:**
- `GET/POST /api/students/`
- `GET/POST /api/cohorts/`
- `GET/POST /api/assessments/`
- `GET /api/prompts/`

**Frontend:**
- Students list page
- Student detail page
- Assessment creation form
- Cohort selector

---

#### Day 7: Video Upload & Storage
**Deliverables:**
- [ ] S3 bucket configuration with encryption
- [ ] Presigned URL generation
- [ ] Video upload with progress (frontend)
- [ ] Recording model and storage

**APIs:**
- `POST /api/assessments/{id}/upload-url/`
- `POST /api/assessments/{id}/complete-upload/`

**Frontend:**
- Video uploader component
- Progress indicator
- Upload completion handling

---

### Week 2: AI Pipeline & Review UI

#### Day 8-9: Speech-to-Text & Feature Extraction
**Deliverables:**
- [ ] STT service integration (OpenAI Whisper)
- [ ] Transcript model and storage
- [ ] Feature extraction pipeline (Physical, Linguistic, Cognitive, Social)
- [ ] FeatureSignals model

**Celery Tasks:**
- `extract_audio_task`
- `transcribe_task`
- `extract_features_task`

**Storage:**
- Transcript JSON in PostgreSQL
- Extracted features in FeatureSignals table

---

#### Day 10: Benchmarking & Evidence Generation
**Deliverables:**
- [ ] BDL v0.1 JSON definitions (3 modes × 3-4 age bands)
- [ ] Benchmark engine (BDL interpreter)
- [ ] Evidence candidate generation
- [ ] EvidenceCandidate model

**Files:**
- `benchmarks/bdl/v1.0.0/11-12_explaining.json`
- `benchmarks/bdl/v1.0.0/11-12_presenting.json`
- `benchmarks/bdl/v1.0.0/11-12_persuading.json`
- (Add more age bands as needed)

---

#### Day 11: LLM Scoring Service
**Deliverables:**
- [ ] LLM scoring integration (OpenAI GPT-4o)
- [ ] Structured JSON output parsing
- [ ] DraftReport generation
- [ ] Evidence clip selection validation

**Prompt Engineering:**
- Rubric-constrained scoring prompt
- Mode-specific feedback generation

**Celery Task:**
- `score_with_llm_task`

---

#### Day 12: Teacher Review UI
**Deliverables:**
- [ ] Draft report display
- [ ] Video player with clip navigation
- [ ] Score editing interface
- [ ] Evidence clip replacement/addition
- [ ] Feedback editing

**Frontend Components:**
- `ReportViewer`
- `ScoreEditor`
- `EvidenceClips`
- `FeedbackSection`

**APIs:**
- `GET /api/reports/draft/{id}/`
- `POST /api/reports/draft/{id}/edit/`

---

#### Day 13: Sign-off, Audit & PDF Export
**Deliverables:**
- [ ] SignedReport model and workflow
- [ ] Audit logging (all changes tracked)
- [ ] PDF report generation
- [ ] Sign-off confirmation

**APIs:**
- `POST /api/reports/{id}/sign/`
- `GET /api/reports/{id}/export/pdf/`

**Frontend:**
- Sign-off modal
- PDF download
- Audit trail view

---

#### Day 14: Dashboard, Polish & Integration
**Deliverables:**
- [ ] Teacher dashboard
- [ ] Assessment status tracking
- [ ] WebSocket real-time updates
- [ ] Error handling and retry logic
- [ ] End-to-end testing

**Dashboard Features:**
- Recent assessments list
- Status indicators
- Processing queue
- Quick actions

**Testing:**
- Full workflow test
- Video upload → AI processing → Review → Sign-off

---

## Post-MVP Phases

### Phase 1: Stabilization (Weeks 3-4)

**Goals:**
- Bug fixes and performance optimization
- Security hardening
- Testing coverage improvement
- Documentation completion

**Tasks:**
- [ ] Unit test coverage > 80%
- [ ] Integration tests for API
- [ ] E2E tests with Playwright
- [ ] Security audit
- [ ] Load testing
- [ ] Error monitoring (Sentry)
- [ ] Performance monitoring

---

### Phase 2: Feature Expansion (Weeks 5-8)

**Student-Facing Features:**
- [ ] Student dashboard (view own progress)
- [ ] Practice mode (self-assessment)
- [ ] Goal tracking

**Teacher Features:**
- [ ] Bulk assessment creation
- [ ] Cohort analytics
- [ ] Progress tracking over time
- [ ] Comparison views

**Administrative:**
- [ ] School admin dashboard
- [ ] User management
- [ ] Benchmark version management UI

**Technical:**
- [ ] Caching layer optimization
- [ ] CDN for video streaming
- [ ] Background job monitoring

---

### Phase 3: Custom Model Training (Months 3-6)

**Prerequisites:**
- Minimum 1000 teacher-reviewed assessments
- Sufficient variation in age bands and modes

**Phase 3.1: Rubric Classifier (Week 9-12)**
- [ ] Feature engineering from teacher edits
- [ ] Train classification model (strand → band)
- [ ] A/B testing against LLM scoring
- [ ] Gradual rollout

**Phase 3.2: Evidence Ranking Model (Week 13-16)**
- [ ] Train model to select best evidence clips
- [ ] Replace deterministic evidence generation
- [ ] Teacher feedback loop

**Phase 3.3: Multimodal Fine-tuning (Week 17-24)**
- [ ] Optional: Fine-tune vision model on labeled video
- [ ] Improved physical strand assessment
- [ ] Gesture and posture analysis

---

### Phase 4: Scale & Enterprise (Months 7-12)

**Scalability:**
- [ ] Read replicas for reporting queries
- [ ] Database sharding (by school)
- [ ] CDN for global video delivery
- [ ] Multi-region deployment

**Enterprise Features:**
- [ ] MIS integration (SIMS, Arbor, etc.)
- [ ] SAML/SSO authentication
- [ ] Custom rubric builder
- [ ] White-label options

**Advanced AI:**
- [ ] Group talk scoring (post-MVP feature)
- [ ] Real-time coaching feedback
- [ ] Predictive analytics

---

## Milestone Summary

| Milestone | Date | Key Deliverables |
|-----------|------|------------------|
| MVP v0.1 | Week 2 | Solo mode, 3 modes, basic pipeline |
| MVP v0.2 | Week 4 | Stable, tested, documented |
| Beta | Week 8 | Student portal, analytics |
| v1.0 | Month 6 | Custom models, enterprise ready |
| v2.0 | Month 12 | Group mode, advanced AI |

---

## Success Metrics (MVP)

### Technical Metrics
- [ ] Video upload success rate > 95%
- [ ] AI processing completion rate > 90%
- [ ] API response time p95 < 500ms
- [ ] Uptime > 99.5%
- [ ] Error rate < 1%

### Quality Metrics
- [ ] Teacher edit rate < 30% (high AI accuracy)
- [ ] Evidence clip relevance (teacher satisfaction > 80%)
- [ ] Score confidence > 0.7 on 80% of assessments
- [ ] Transcription accuracy > 90%

### User Metrics
- [ ] Time to complete assessment (upload → sign-off) < 10 min
- [ ] Teacher satisfaction score > 4/5
- [ ] Feature adoption rate > 80%

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| STT accuracy poor for child voices | Medium | High | Use Whisper fine-tuned on child speech, have fallback |
| LLM API rate limits | Medium | High | Implement queues, caching, request batching |
| Video storage costs | Medium | Medium | Implement lifecycle policies, compression |
| GDPR compliance issues | Low | Critical | Legal review, DPO consultation, encryption |
| Teacher adoption resistance | Medium | High | UX research, training materials, feedback loops |
| AWS region latency | Medium | Medium | CDN, multi-region planning |

---

## Team Structure (MVP)

### Core Team (2-3 people)

**Full-Stack Developer (React + Django)**
- Frontend implementation
- API development
- Database design
- DevOps support

**ML/AI Engineer (Part-time)**
- STT integration
- Feature extraction
- Prompt engineering
- Model evaluation

**Product/UX (Part-time)**
- User research
- UI/UX design
- Requirements refinement
- Testing coordination

---

## Development Workflow

### Branch Strategy

```
main (production)
  ↑
staging (pre-production)
  ↑
feature/xyz (feature branches)
```

### Pull Request Requirements
- [ ] Code review by 1 team member
- [ ] All tests passing
- [ ] No security vulnerabilities (bandit, safety)
- [ ] Linting clean (black, flake8, eslint)
- [ ] Type checking (mypy, TypeScript)

### Deployment Flow

1. Feature branch → PR
2. CI runs tests, linting, security checks
3. Code review
4. Merge to `staging`
5. Auto-deploy to staging environment
6. Manual QA on staging
7. Merge to `main`
8. Auto-deploy to production (blue/green)

---

## Checkpoints & Reviews

### Week 1 Review
- [ ] Infrastructure ready
- [ ] Auth working
- [ ] Basic CRUD complete
- [ ] Video upload functional

### Week 2 Review
- [ ] AI pipeline complete
- [ ] Reports generating
- [ ] Teacher UI functional
- [ ] End-to-end workflow tested

### Pre-Launch Checklist
- [ ] Security audit passed
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Training materials ready
- [ ] Support process defined
- [ ] Rollback plan documented
