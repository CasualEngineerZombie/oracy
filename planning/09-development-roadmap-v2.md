# Development Roadmap V2 (Cost-Optimized MVP)

## Overview

This roadmap adjusts the original 3-month MVP plan to accommodate the cost-optimized V2 architecture. Key changes:

1. **Week 6** now includes RunPod integration instead of OpenAI Whisper API
2. **Week 9** uses OpenRouter for LLM scoring instead of direct OpenAI API
3. Additional **Week 13** for cost optimization and monitoring setup
4. Parallel validation track to ensure V2 quality matches V1

---

## 3-Month MVP Timeline (Revised)

### Month 1: Foundation & Core Infrastructure (Weeks 1-4)

**Unchanged from V1** - Focus on core platform features.

#### Week 1: Project Setup & Infrastructure
- [ ] Initialize Django project with apps structure
- [ ] Initialize React project with Vite + TypeScript
- [ ] Docker Compose for local development
- [ ] Git repository setup with branch protection
- [ ] CI/CD pipeline skeleton (GitHub Actions)
- [ ] Development environment documentation

**AWS Infrastructure (V2 specs):**
- [ ] VPC, subnets, security groups
- [ ] RDS PostgreSQL instance (db.t3.small)
- [ ] S3 bucket with intelligent tiering
- [ ] ECS cluster with Fargate Spot enabled
- [ ] ElastiCache Redis for Celery

#### Week 2: Authentication & User Management
- [ ] User authentication (JWT) - backend
- [ ] User registration and login flows
- [ ] User model with roles (admin, teacher, student)
- [ ] School model and multi-tenancy structure
- [ ] Password reset functionality
- [ ] Email service integration

#### Week 3: Student & Cohort Management
- [ ] Student model and CRUD APIs
- [ ] Cohort model and enrollment system
- [ ] CSV import for bulk student upload
- [ ] Student profile management
- [ ] Age band calculation logic

#### Week 4: Assessment Framework & UI
- [ ] Assessment model and lifecycle
- [ ] Prompt template system
- [ ] Assessment creation flow (teacher)
- [ ] Assessment assignment to students
- [ ] Assessment scheduling

---

### Month 2: AI Pipeline & Media Processing (Weeks 5-9)

**Modified for V2 cost optimization**

#### Week 5: Video Upload & Storage
- [ ] S3 bucket configuration with lifecycle policies
- [ ] Presigned URL generation service
- [ ] Chunked video upload with resumable support
- [ ] Video upload progress tracking
- [ ] Recording model and metadata storage
- [ ] Video format validation and preprocessing

#### Week 6: Speech-to-Text Pipeline (V2 - WhisperX) ⚡

**Major change from V1: Replace OpenAI Whisper API with WhisperX on RunPod**

**Day 1-2: RunPod + WhisperX Setup**
- [ ] Create RunPod account and configure billing
- [ ] Build Docker image for WhisperX worker with distil-large-v3
- [ ] Pre-download model during build for faster cold starts
- [ ] Deploy serverless GPU endpoint (RTX 3090)
- [ ] Configure flashboot for 2-second cold starts
- [ ] Test endpoint with sample audio (batch_size=4)

**Day 3-4: WhisperX Integration**
- [ ] Implement `RunPodWhisperXService` class
- [ ] Configure int8 quantization (40% VRAM reduction)
- [ ] Implement batch processing (4 files simultaneously)
- [ ] Add forced word alignment for precise timestamps
- [ ] Add audio extraction from video (ffmpeg)
- [ ] Create transcript model with word-level timestamps
- [ ] Implement retry logic for failed jobs

**Day 5: Validation**
- [ ] Run parallel transcription (OpenAI vs WhisperX)
- [ ] Calculate Word Error Rate (WER) - target < 18%
- [ ] Validate word-level timestamp accuracy
- [ ] Test batch processing throughput
- [ ] Document quality metrics

**Celery Tasks:**
- `extract_audio_task`
- `transcribe_whisperx_task` (replaces `transcribe_task`)
- `process_transcript_task`

**Storage:**
- Transcript JSON in PostgreSQL with GIN indexing
- Word-level timestamps with confidence scores
- Audio files in S3 (temporary, 7-day lifecycle)

**Frontend:**
- Transcript viewer component with word highlighting
- Click-to-play from any word
- Confidence indicators per word

**Cost Target:** < $0.0005 per minute (vs $0.006 OpenAI = 92% savings)
**Throughput Target:** 4-8 assessments per GPU minute (batch processing)

---

#### Week 7: Feature Extraction Engine

**Unchanged from V1** - Already uses open source libraries.

- [ ] Physical features extraction (librosa, webrtcvad)
- [ ] Linguistic features extraction (spaCy, textstat)
- [ ] Cognitive features extraction (keyword matching)
- [ ] Social features extraction (VADER sentiment)
- [ ] FeatureSignals model and storage
- [ ] Feature extraction orchestration

**Libraries (all open source):**
- librosa (audio processing)
- webrtcvad (voice activity detection)
- spaCy (NLP)
- VADER (sentiment analysis)
- textstat (readability metrics)

---

#### Week 8: BDL Benchmark System

**Unchanged from V1** - Internal IP, no external dependencies.

- [ ] BDL v0.1 JSON schema definitions
- [ ] Benchmark data loader and validator
- [ ] Benchmark engine (BDL interpreter)
- [ ] Evidence candidate generation algorithm
- [ ] EvidenceCandidate model
- [ ] Initial BDL data for 3 modes × 4 age bands

---

#### Week 9: LLM Scoring Service (V2 - OpenRouter) ⚡

**Major change from V1: Use OpenRouter instead of direct OpenAI API**

**Day 1-2: OpenRouter Integration**
- [ ] Create OpenRouter account
- [ ] Implement `OpenRouterService` class
- [ ] Configure model selection (Gemini Flash, Claude Haiku)
- [ ] Test structured JSON output parsing
- [ ] Add fallback to alternative models

**Day 3-4: Scoring Implementation**
- [ ] Mode-specific system prompts
- [ ] Rubric-constrained scoring prompts
- [ ] DraftReport generation with all strands
- [ ] Evidence clip selection and validation
- [ ] Score confidence calculation

**Day 5: Local Fallback (Optional)**
- [ ] Set up Ollama for local LLM testing
- [ ] Implement `OllamaService` class
- [ ] Test with llama3.2:3b model
- [ ] Document quality trade-offs

**Prompt Engineering:**
- Mode-specific system prompts
- Rubric-constrained scoring prompts
- Band justification prompts
- Feedback generation prompts

**Celery Tasks:**
- `score_with_openrouter_task` (replaces `score_with_llm_task`)
- `generate_draft_report_task`
- `validate_evidence_task`

**Cost Target:** < $0.001 per 1K tokens (vs $0.005 OpenAI GPT-4o)

---

### Month 3: Scoring, Review, Launch & Optimization (Weeks 10-13)

#### Week 10: Teacher Review Interface

**Unchanged from V1.**

- [ ] Draft report display with strand breakdown
- [ ] Video player with evidence clip navigation
- [ ] Score editing interface with band selector
- [ ] Evidence clip replacement workflow
- [ ] Evidence clip addition from video
- [ ] Feedback editing with rich text
- [ ] Score comparison (AI vs. Teacher)

#### Week 11: Sign-off, Audit & Export

**Unchanged from V1.**

- [ ] SignedReport model and workflow
- [ ] Comprehensive audit logging (all changes)
- [ ] PDF report generation with styling
- [ ] Sign-off confirmation with digital signature
- [ ] Report sharing (download link)
- [ ] Audit trail viewer

#### Week 12: Dashboard, Testing & Launch

**Unchanged from V1.**

- [ ] Teacher dashboard with metrics
- [ ] Assessment status tracking (real-time)
- [ ] WebSocket integration for live updates
- [ ] Error handling and retry mechanisms
- [ ] End-to-end testing completion
- [ ] Performance optimization
- [ ] Documentation finalization

#### Week 13: Cost Optimization & Monitoring (NEW) ⚡

**New week dedicated to V2 cost optimization**

**Day 1-2: Cost Infrastructure**
- [ ] Set up AWS Cost Anomaly Detection
- [ ] Configure budget alerts ($1000/month threshold)
- [ ] Implement cost tracking dashboard
- [ ] Add cost allocation tags to all resources
- [ ] Set up weekly cost reports

**Day 3-4: Fargate Spot Migration**
- [ ] Enable Fargate Spot for Celery workers
- [ ] Test spot interruption handling
- [ ] Configure task retry policies
- [ ] Monitor spot instance availability
- [ ] Document fallback strategies

**Day 5: S3 Optimization**
- [ ] Apply Intelligent-Tiering to media bucket
- [ ] Configure lifecycle policies for uploads/exports
- [ ] Set up cross-region replication (if needed)
- [ ] Review and optimize data transfer costs
- [ ] Archive old logs and temp files

**Validation Tasks:**
- [ ] Run full pipeline with 50 test assessments
- [ ] Calculate actual cost per assessment
- [ ] Compare V2 costs vs V1 projections
- [ ] Document actual savings achieved

---

## Post-MVP Roadmap (V2)

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

**V2 Specific:**
- [ ] RunPod endpoint monitoring
- [ ] OpenRouter usage analytics
- [ ] Fallback service health checks
- [ ] Cost per assessment tracking

---

### Phase 2: Feature Expansion (Months 6-8)

**Unchanged from V1.**

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

---

### Phase 3: AI Enhancement (Months 9-12)

**Modified to include cost considerations**

**Prerequisites:**
- Minimum 500 teacher-reviewed assessments
- Sufficient variation in age bands and modes
- Cost per assessment < $0.50 confirmed

**Phase 3.1: Scoring Model Training (Months 9-10)**
- [ ] Collect teacher edit data
- [ ] Feature engineering from corrections
- [ ] Train classification model (strand → band)
- [ ] A/B testing: LLM vs. Custom model
- [ ] Gradual rollout with fallback

**V2 Specific - Cost Analysis:**
- [ ] Calculate training costs (SageMaker vs. RunPod)
- [ ] Compare inference costs: Custom model vs. OpenRouter
- [ ] Decision point: Continue with LLM or switch to custom model

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

**Modified with cost optimization focus**

**Scalability:**
- [ ] Read replicas for reporting queries
- [ ] Database partitioning by school
- [ ] Multi-region deployment (EU, US)
- [ ] CDN for global video delivery
- [ ] Auto-scaling policies refinement

**V2 Specific - Cost Optimization:**
- [ ] Evaluate RunPod vs. Vast.ai at scale
- [ ] Consider dedicated GPU server purchase
- [ ] Implement hybrid cloud/on-premise option
- [ ] Optimize model quantization for faster inference

**Enterprise Features:**
- [ ] MIS integration (SIMS, Arbor, PowerSchool)
- [ ] SAML/SSO authentication (Google, Microsoft)
- [ ] Custom data retention policies
- [ ] On-premise deployment option
- [ ] Advanced analytics and reporting
- [ ] API access for integrations

---

## V1 vs V2 Cost Comparison Timeline

| Month | V1 Projected | V2 Projected | Cumulative Savings |
|-------|--------------|--------------|-------------------|
| Month 1 | $1,500 | $800 | $700 |
| Month 2 | $2,000 | $900 | $1,800 |
| Month 3 | $2,500 | $1,000 | $3,300 |
| **Total (3 months)** | **$6,000** | **$2,700** | **$3,300 (55%)** |

---

## Key V2 Deliverables Checklist

### Infrastructure (Week 1)
- [ ] RunPod account configured
- [ ] Serverless GPU endpoint deployed (RTX 3090)
- [ ] Docker image for WhisperX worker built with distil-large-v3
- [ ] Model pre-downloaded in Docker image (faster cold start)
- [ ] Flashboot enabled (2s cold start target)
- [ ] OpenRouter account created
- [ ] Ollama installed (local development)

### STT Pipeline (Week 6)
- [ ] `RunPodWhisperXService` implemented
- [ ] WhisperX with distil-large-v3 configured
- [ ] int8 quantization enabled (2.8GB VRAM)
- [ ] Batch processing (4 files) working
- [ ] Forced word alignment implemented
- [ ] Audio extraction working
- [ ] Transcript model with word timestamps created
- [ ] Parallel validation complete (WER < 18% vs OpenAI 16.7%)
- [ ] Retry logic implemented

### LLM Scoring (Week 9)
- [ ] `OpenRouterService` implemented
- [ ] Multiple model support configured
- [ ] Structured JSON output validated
- [ ] Fallback to alternative models working
- [ ] Cost per assessment < $0.50 achieved

### Cost Optimization (Week 13)
- [ ] AWS Cost Anomaly Detection enabled
- [ ] Budget alerts configured
- [ ] Fargate Spot enabled for workers
- [ ] S3 Intelligent-Tiering applied
- [ ] Cost tracking dashboard deployed

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| RunPod service outage | High | Implement Vast.ai and CPU fallback |
| OpenRouter rate limits | Medium | Implement local Ollama fallback |
| Cold start latency | Medium | Configure flashboot; cache warm workers |
| V2 accuracy lower than V1 | High | Parallel validation; keep V1 as backup |
| Cost savings not achieved | Medium | Weekly cost reviews; adjust resource sizes |

---

## Success Metrics

### Technical Metrics
- [ ] STT Word Error Rate < 5% (vs OpenAI Whisper)
- [ ] LLM scoring correlation > 0.95 (vs GPT-4o)
- [ ] End-to-end latency < 3 minutes (95th percentile)
- [ ] System availability > 99.5%

### Cost Metrics
- [ ] Cost per assessment < $0.50 (full pipeline)
- [ ] Monthly infrastructure < $700
- [ ] 60% savings vs V1 architecture achieved

### Business Metrics
- [ ] 50 assessments processed in testing
- [ ] Teacher satisfaction with report quality
- [ ] Zero data quality complaints
