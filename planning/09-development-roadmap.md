# Development Roadmap

## 3-Month MVP Timeline

### Month 1: Foundation & Core Infrastructure (Weeks 1-4)

#### Week 1: Project Setup & Infrastructure
**Deliverables:**
- [ ] Initialize Django project with apps structure
- [ ] Initialize React project with Vite + TypeScript
- [ ] Docker Compose for local development
- [ ] Git repository setup with branch protection
- [ ] CI/CD pipeline skeleton (GitHub Actions)
- [ ] Development environment documentation

**AWS Infrastructure:**
- [ ] VPC, subnets, security groups
- [ ] RDS PostgreSQL instance (dev)
- [ ] S3 bucket with encryption
- [ ] ECS cluster setup
- [ ] ElastiCache Redis for Celery

**Key Decisions:**
- Django project structure finalized
- AWS region selected (ap-southeast-1 for initial dev)
- Code review and deployment process established

---

#### Week 2: Authentication & User Management
**Deliverables:**
- [ ] User authentication (JWT) - backend
- [ ] User registration and login flows
- [ ] User model with roles (admin, teacher, student)
- [ ] School model and multi-tenancy structure
- [ ] Password reset functionality
- [ ] Email service integration

**APIs:**
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `POST /api/auth/reset-password/`
- `GET /api/users/me/`
- `GET/POST /api/schools/`

**Frontend:**
- Login page with validation
- Registration flow
- Auth context/store with JWT handling
- Protected routes and role-based access
- Password reset UI

---

#### Week 3: Student & Cohort Management
**Deliverables:**
- [ ] Student model and CRUD APIs
- [ ] Cohort model and enrollment system
- [ ] CSV import for bulk student upload
- [ ] Student profile management
- [ ] Age band calculation logic

**APIs:**
- `GET/POST /api/students/`
- `GET/PUT/DELETE /api/students/{id}/`
- `GET/POST /api/cohorts/`
- `GET/PUT/DELETE /api/cohorts/{id}/`
- `POST /api/cohorts/{id}/enroll/`
- `POST /api/students/import/`

**Frontend:**
- Students list with search/filter
- Student detail page with history
- Student creation/editing forms
- Cohort management interface
- CSV import wizard

---

#### Week 4: Assessment Framework & UI
**Deliverables:**
- [ ] Assessment model and lifecycle
- [ ] Prompt template system
- [ ] Assessment creation flow (teacher)
- [ ] Assessment assignment to students
- [ ] Assessment scheduling

**APIs:**
- `GET/POST /api/assessments/`
- `GET/PUT/DELETE /api/assessments/{id}/`
- `POST /api/assessments/{id}/assign/`
- `GET /api/prompts/`
- `GET /api/prompt-templates/`

**Frontend:**
- Assessment creation form with mode selection
- Mode selector (explaining, presenting, persuading)
- Age-appropriate prompt display
- Assessment list with status tracking
- Assignment workflow

---

### Month 2: AI Pipeline & Media Processing (Weeks 5-8)

#### Week 5: Video Upload & Storage
**Deliverables:**
- [ ] S3 bucket configuration with lifecycle policies
- [ ] Presigned URL generation service
- [ ] Chunked video upload with resumable support
- [ ] Video upload progress tracking
- [ ] Recording model and metadata storage
- [ ] Video format validation and preprocessing

**APIs:**
- `POST /api/assessments/{id}/upload-url/`
- `POST /api/assessments/{id}/upload-chunk/`
- `POST /api/assessments/{id}/complete-upload/`
- `GET /api/recordings/{id}/status/`

**Frontend:**
- Video recorder component (WebRTC)
- File uploader with drag-and-drop
- Upload progress indicator with retry
- Recording preview before submission

---

#### Week 6: Speech-to-Text Pipeline
**Deliverables:**
- [ ] STT service integration (OpenAI Whisper)
- [ ] Audio extraction from video
- [ ] Transcript model and storage
- [ ] Speaker diarization (if applicable)
- [ ] Transcript confidence scoring
- [ ] Fallback for low-confidence transcripts

**Celery Tasks:**
- `extract_audio_task`
- `transcribe_task` (with retry logic)
- `process_transcript_task`

**Storage:**
- Transcript JSON in PostgreSQL with GIN indexing
- Audio files in S3 (temporary)

**Frontend:**
- Transcript viewer component
- Highlight transcript segments
- Confidence indicators

---

#### Week 7: Feature Extraction Engine
**Deliverables:**
- [ ] Physical features extraction (eye contact, posture, gestures)
- [ ] Linguistic features extraction (vocabulary, structure, clarity)
- [ ] Cognitive features extraction (argument quality, evidence use)
- [ ] Social features extraction (audience engagement, tone)
- [ ] FeatureSignals model and storage
- [ ] Feature extraction orchestration

**Celery Tasks:**
- `extract_features_task` (parent)
- `extract_physical_features_task`
- `extract_linguistic_features_task`
- `extract_cognitive_features_task`
- `extract_social_features_task`

**Storage:**
- FeatureSignals JSONB in PostgreSQL
- Feature metadata and confidence scores

---

#### Week 8: BDL Benchmark System
**Deliverables:**
- [ ] BDL v0.1 JSON schema definitions
- [ ] Benchmark data loader and validator
- [ ] Benchmark engine (BDL interpreter)
- [ ] Evidence candidate generation algorithm
- [ ] EvidenceCandidate model
- [ ] Initial BDL data for 3 modes × 4 age bands (8-9, 9-10, 10-11, 11-12)

**Files:**
- `benchmarks/bdl/v1.0.0/explaining_8-9.json`
- `benchmarks/bdl/v1.0.0/explaining_9-10.json`
- `benchmarks/bdl/v1.0.0/explaining_10-11.json`
- `benchmarks/bdl/v1.0.0/explaining_11-12.json`
- `benchmarks/bdl/v1.0.0/presenting_*.json` (4 files)
- `benchmarks/bdl/v1.0.0/persuading_*.json` (4 files)

**APIs:**
- `GET /api/benchmarks/`
- `GET /api/assessments/{id}/evidence-candidates/`

---

### Month 3: Scoring, Review & Launch (Weeks 9-12)

#### Week 9: LLM Scoring Service
**Deliverables:**
- [ ] LLM scoring integration (OpenAI GPT-4o/Claude)
- [ ] Structured JSON output parsing with validation
- [ ] DraftReport generation with all strands
- [ ] Evidence clip selection and validation
- [ ] Score confidence calculation
- [ ] Fallback scoring for edge cases

**Prompt Engineering:**
- Mode-specific system prompts
- Rubric-constrained scoring prompts
- Band justification prompts
- Feedback generation prompts

**Celery Tasks:**
- `score_with_llm_task`
- `generate_draft_report_task`
- `validate_evidence_task`

**APIs:**
- `GET /api/reports/draft/{id}/`
- `GET /api/reports/{id}/confidence/`

---

#### Week 10: Teacher Review Interface
**Deliverables:**
- [ ] Draft report display with strand breakdown
- [ ] Video player with evidence clip navigation
- [ ] Score editing interface with band selector
- [ ] Evidence clip replacement workflow
- [ ] Evidence clip addition from video
- [ ] Feedback editing with rich text
- [ ] Score comparison (AI vs. Teacher)

**Frontend Components:**
- `ReportViewer` with strand tabs
- `VideoPlayer` with timestamp markers
- `ScoreEditor` with justification
- `EvidenceClips` with drag selection
- `FeedbackEditor` with templates

**APIs:**
- `POST /api/reports/draft/{id}/edit/`
- `POST /api/reports/draft/{id}/replace-evidence/`
- `POST /api/reports/draft/{id}/add-evidence/`
- `POST /api/reports/draft/{id}/save-progress/`

---

#### Week 11: Sign-off, Audit & Export
**Deliverables:**
- [ ] SignedReport model and workflow
- [ ] Comprehensive audit logging (all changes)
- [ ] PDF report generation with styling
- [ ] Sign-off confirmation with digital signature
- [ ] Report sharing (download link)
- [ ] Audit trail viewer

**APIs:**
- `POST /api/reports/{id}/sign/`
- `GET /api/reports/{id}/export/pdf/`
- `GET /api/reports/{id}/audit-trail/`

**Frontend:**
- Sign-off modal with confirmation
- PDF preview before download
- Audit trail timeline view
- Report sharing dialog

---

#### Week 12: Dashboard, Testing & Launch
**Deliverables:**
- [ ] Teacher dashboard with metrics
- [ ] Assessment status tracking (real-time)
- [ ] WebSocket integration for live updates
- [ ] Error handling and retry mechanisms
- [ ] End-to-end testing completion
- [ ] Performance optimization
- [ ] Documentation finalization

**Dashboard Features:**
- Recent assessments with status
- Processing queue visualization
- Quick action buttons
- Analytics summary (assessments per week, etc.)

**Testing:**
- Unit test coverage > 80%
- Integration tests for all APIs
- E2E tests with Playwright (critical paths)
- Load testing for concurrent uploads
- AI pipeline accuracy validation

**APIs:**
- `GET /api/dashboard/stats/`
- `GET /api/dashboard/recent-assessments/`
- `GET /api/dashboard/processing-queue/`
- WebSocket: `/ws/assessments/{id}/status/`

---

## Post-MVP Roadmap

### Phase 1: Stabilization & Polish (Months 4-5)

**Goals:**
- Production hardening
- Security audit and penetration testing
- Performance optimization
- User feedback integration

**Tasks:**
- [ ] Security audit with external firm
- [ ] GDPR compliance certification
- [ ] Penetration testing
- [ ] Performance monitoring (Datadog/New Relic)
- [ ] Error tracking (Sentry integration)
- [ ] Automated alerting
- [ ] User onboarding improvements
- [ ] Help documentation and tutorials
- [ ] In-app feedback system

---

### Phase 2: Feature Expansion (Months 6-8)

**Student-Facing Features:**
- [ ] Student dashboard (view progress, history)
- [ ] Practice mode (self-assessment without teacher)
- [ ] Goal setting and tracking
- [ ] Achievement badges
- [ ] Peer comparison (anonymized)

**Teacher Features:**
- [ ] Bulk assessment creation wizard
- [ ] Cohort analytics and insights
- [ ] Progress tracking over time (charts)
- [ ] Student comparison tools
- [ ] Comment templates
- [ ] Gradebook integration preparation

**Administrative:**
- [ ] School admin dashboard
- [ ] User management (invite, deactivate)
- [ ] Billing and usage analytics
- [ ] Benchmark version management UI
- [ ] Custom rubric builder (basic)

**Technical:**
- [ ] CDN implementation for video streaming
- [ ] Caching layer (Redis) for frequent queries
- [ ] Background job monitoring dashboard
- [ ] Database query optimization
- [ ] API rate limiting and throttling

---

### Phase 3: AI Enhancement (Months 9-12)

**Prerequisites:**
- Minimum 500 teacher-reviewed assessments
- Sufficient variation in age bands and modes

**Phase 3.1: Scoring Model Training (Months 9-10)**
- [ ] Collect teacher edit data
- [ ] Feature engineering from corrections
- [ ] Train classification model (strand → band)
- [ ] A/B testing: LLM vs. Custom model
- [ ] Gradual rollout with fallback

**Phase 3.2: Evidence Ranking Model (Months 10-11)**
- [ ] Train model to select best evidence clips
- [ ] Teacher preference learning
- [ ] Replace deterministic selection
- [ ] Confidence scoring for evidence

**Phase 3.3: Advanced AI Features (Months 11-12)**
- [ ] Real-time coaching feedback (optional toggle)
- [ ] Predictive analytics (at-risk students)
- [ ] Personalized improvement suggestions
- [ ] Automated progress reports

---

### Phase 4: Scale & Enterprise (Year 2)

**Scalability:**
- [ ] Read replicas for reporting queries
- [ ] Database partitioning by school
- [ ] Multi-region deployment (EU, US)
- [ ] CDN for global video delivery
- [ ] Auto-scaling policies refinement

**Enterprise Features:**
- [ ] MIS integration (SIMS, Arbor, PowerSchool)
- [ ] SAML/SSO authentication (Google, Microsoft)
- [ ] Custom branding/white-label
- [ ] Advanced analytics and insights
- [ ] API access for schools
- [ ] Data export tools

**Advanced Features:**
- [ ] Group talk scoring (multi-speaker)
- [ ] Presentation slide analysis
- [ ] Parent portal access
- [ ] Curriculum alignment tools

---

## Milestone Summary

| Milestone | Timeline | Key Deliverables |
|-----------|----------|------------------|
| **MVP v1.0** | Month 3 | Solo mode, 3 modes, 4 age bands, full AI pipeline, teacher review, PDF export |
| **Stabilized v1.0** | Month 5 | Security certified, performance optimized, production hardened |
| **v1.5 Beta** | Month 8 | Student portal, analytics, admin tools, CDN |
| **v2.0** | Month 12 | Custom AI models, real-time feedback, predictive analytics |
| **Enterprise v2.5** | Year 2 | MIS integrations, SSO, white-label, group mode |

---

## 3-Month MVP Success Metrics

### Technical Metrics
- [ ] Video upload success rate > 95%
- [ ] AI processing completion rate > 90%
- [ ] API response time p95 < 500ms
- [ ] Uptime > 99.5%
- [ ] Error rate < 1%
- [ ] Test coverage > 80%
- [ ] Zero critical security vulnerabilities

### Quality Metrics
- [ ] Teacher edit rate < 30% (high AI accuracy)
- [ ] Evidence clip relevance (teacher satisfaction > 80%)
- [ ] Score confidence > 0.7 on 80% of assessments
- [ ] Transcription accuracy > 90%
- [ ] Report generation time < 5 minutes

### User Experience Metrics
- [ ] Time to complete assessment (upload → sign-off) < 10 min
- [ ] Teacher satisfaction score > 4/5
- [ ] Feature adoption rate > 80%
- [ ] NPS score > 40
- [ ] Support ticket volume < 5% of active users

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| STT accuracy poor for child voices | Medium | High | Use Whisper fine-tuned on child speech, have manual fallback, confidence scoring |
| LLM API rate limits/costs | Medium | High | Implement queues, caching, request batching, usage monitoring |
| Video storage costs | Medium | Medium | Lifecycle policies, compression, intelligent archival |
| GDPR compliance issues | Low | Critical | Legal review, DPO consultation, encryption, data residency |
| Teacher adoption resistance | Medium | High | UX research, training webinars, feedback loops, iterative improvements |
| AWS region latency | Medium | Medium | CDN planning, multi-region roadmap, edge optimization |
| AI pipeline failure | Low | High | Comprehensive retry logic, fallback to manual review, alerting |
| Scope creep | High | Medium | Strict MVP definition, feature prioritization framework, regular reviews |

---

## Team Structure (3-Month MVP)

### Core Team (3-4 people)

**Tech Lead / Full-Stack Developer (1 FTE)**
- Architecture decisions
- Backend API development (Django)
- Database design and optimization
- DevOps and AWS infrastructure
- Code review and quality

**Frontend Developer (1 FTE)**
- React/TypeScript implementation
- UI/UX component development
- Video player and upload components
- State management and API integration
- Responsive design

**ML/AI Engineer (0.5-0.75 FTE)**
- STT integration and optimization
- Feature extraction pipeline
- Prompt engineering
- BDL benchmark development
- LLM scoring service
- Model evaluation

**Product/QA Lead (0.5 FTE)**
- User research and requirements
- UI/UX design
- Test planning and execution
- Documentation
- Training material creation
- Stakeholder communication

---

## Development Workflow

### Branch Strategy

```
main (production)
  ↑
release/v1.0 (release candidate)
  ↑
develop (integration)
  ↑
feature/xyz (feature branches)
```

### Pull Request Requirements
- [ ] Code review by 1+ team member
- [ ] All tests passing (unit, integration)
- [ ] No security vulnerabilities (bandit, safety, npm audit)
- [ ] Linting clean (black, flake8, prettier, eslint)
- [ ] Type checking (mypy, TypeScript strict)
- [ ] PR description with context

### Deployment Flow

1. Feature branch → PR to `develop`
2. CI runs tests, linting, security checks
3. Code review and approval
4. Merge to `develop`
5. Auto-deploy to development environment
6. QA testing on dev environment
7. PR from `develop` to `release/vX.X`
8. Staging deployment and UAT
9. Merge to `main`
10. Production deployment with blue/green

### Sprint Cadence
- **2-week sprints** aligned with weekly milestones
- Sprint planning every 2 weeks
- Daily standups (15 min)
- Sprint review and demo
- Retrospective for process improvement

---

## Monthly Checkpoints & Reviews

### Month 1 Review (End of Week 4)
- [ ] Infrastructure ready and stable
- [ ] Authentication and user management working
- [ ] Student and cohort CRUD complete
- [ ] Assessment creation flow functional
- [ ] Code coverage > 60%
- [ ] Documentation up to date

### Month 2 Review (End of Week 8)
- [ ] Video upload and storage working
- [ ] STT pipeline processing videos
- [ ] Feature extraction running
- [ ] BDL benchmarks loaded
- [ ] AI pipeline end-to-end functional
- [ ] Code coverage > 70%

### Pre-Launch Review (End of Week 12)
- [ ] Full end-to-end workflow tested
- [ ] Security audit passed
- [ ] Performance targets met
- [ ] Test coverage > 80%
- [ ] Documentation complete
- [ ] Training materials ready
- [ ] Support process defined
- [ ] Rollback plan documented
- [ ] Monitoring and alerting configured

### Launch Day Checklist
- [ ] Production environment verified
- [ ] Database backups configured
- [ ] SSL certificates valid
- [ ] Error tracking active
- [ ] Support team briefed
- [ ] Rollback procedure tested
- [ ] Communication plan executed

---

## Budget Considerations (3-Month MVP)

### Infrastructure Costs (Estimated)
- AWS RDS (db.t3.medium): ~$50/month
- AWS ECS (2 services): ~$100/month
- AWS S3 (storage + transfer): ~$50-200/month
- AWS ElastiCache: ~$30/month
- OpenAI API (usage-based): ~$200-500/month
- Total: ~$500-1000/month

### Development Tools
- GitHub Teams: ~$20/month
- Sentry (error tracking): ~$26/month
- Figma (design): ~$45/month
- Notion/Linear (project management): ~$20/month

### Buffer
- 20% contingency for unexpected costs
- Scale costs with user growth post-MVP

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
