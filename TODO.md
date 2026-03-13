# Oracy Project - Detailed Work Items

> Generated from planning docs and project-docs
> Last Updated: 2026-03-13

---

## MVP Phase (Months 1-3)

### Month 1: Foundation & Core Infrastructure (Weeks 1-4)

#### Week 1: Project Setup & Infrastructure

- [x] **Initialize Django project with apps structure** - Create Django project with separate apps for users, students, assessments, analysis, reports, and benchmarks. Use Django 5.x with Python 3.12+. Configure apps.py with proper AppConfigs.

- [x] **Initialize React project with Vite + TypeScript** - Set up React 18+ with Vite as the build tool. Configure TypeScript strict mode, add TailwindCSS for styling, and set up shadcn/ui components library.

- [x] **Docker Compose for local development** - Create docker-compose.yml with services for: Django (web), Celery worker, PostgreSQL (db), Redis (cache), and MinIO (S3 local). Configure volume mounts for hot reloading.

- [x] **Git repository setup with branch protection** - Configure GitHub repository with protected main branch, require PR reviews, and set up conventional commits workflow.

- [x] **CI/CD pipeline skeleton (GitHub Actions)** - Create .github/workflows with: lint.yml (ESLint, Flake8), test.yml (Vitest, Django tests), and build.yml (Docker build and push).

- [x] **Development environment documentation** - Write README.md with local setup instructions, environment variables reference, and troubleshooting guide.

- [ ] **VPC, subnets, security groups (AWS)** - Create VPC with public/private subnets across 3 availability zones. Configure security groups for: ALB (80/443), ECS (from ALB), RDS (from ECS), ElastiCache (from ECS).

- [ ] **RDS PostgreSQL instance (db.t3.small)** - Launch PostgreSQL 15 on db.t3.small with multi-AZ enabled. Configure parameter groups for JSON support and set up read replicas for future scaling.

- [ ] **S3 bucket with intelligent tiering** - Create S3 bucket with Intelligent-Tiering configuration for automatic cost optimization. Set up lifecycle policies for transition to Glacier after 1 year.

- [ ] **ECS cluster with Fargate Spot enabled** - Create ECS cluster with Fargate capacity providers. Configure Spot capacity strategy for fault-tolerant workloads (Celery workers).

- [ ] **ElastiCache Redis for Celery** - Launch Redis 7 on cache.t3.micro with cluster mode disabled. Configure Redis for both Celery broker and result backend.

---

#### Week 2: Authentication & User Management

- [x] **User authentication (JWT) - backend** - Implement JWT-based authentication using SimpleJWT library. Configure access token lifetime (15 min) and refresh token lifetime (1 day). Add custom claims for user role and school_id.

- [x] **User registration and login flows** - Create Django REST Framework views for registration, login, and token refresh. Implement email verification flow with time-limited tokens.

- [x] **User model with roles (admin, teacher, student)** - Extend Django AbstractUser with: role (choices: admin, teacher, student), school (FK to School), and custom manager methods.

- [x] **School model and multi-tenancy structure** - Create School model with: name, identifier (URN), region, and settings (JSONB for tenant-specific config). Implement row-level security for multi-tenancy.

- [x] **Password reset functionality** - Implement password reset via email with secure token generation. Use Django's built-in password reset views with custom email template.

- [ ] **Email service integration** - Configure AWS SES for production email sending. Use environment variables for SMTP configuration in development (use Mailhog or similar).

- [x] **Frontend login/register pages** - Build LoginPage.tsx with form validation using React Hook Form + Zod. Create RegistrationPage with role selection and school code input.

---

#### Week 3: Student & Cohort Management

- [x] **Student model and CRUD APIs** - Create Student model linked to User with: student_id (school's ID), date_of_birth, year_group, age_band (computed), EAL status, first_language, and accommodations.

- [x] **Cohort model and enrollment system** - Create Cohort model with: teacher (FK), name, year_group, and academic_year. Implement Enrollment model for many-to-many student-cohort relationship.

- [x] **CSV import for bulk student upload** - Build upload endpoint accepting CSV with columns: student_id, first_name, last_name, date_of_birth, year_group, email. Validate and create users/students in batch.

- [x] **Student profile management** - Create API endpoints and frontend pages for viewing/editing student profiles. Include age band auto-calculation based on date_of_birth and academic year.

- [x] **Age band calculation logic** - Implement utility function to calculate age bands (e.g., "11-12", "13-14") based on date of birth and academic year cutoff (September 1).

- [x] **Frontend student management UI** - Build cohort list view, student list with filtering, and CSV upload interface using TanStack Table for data display.

---

#### Week 4: Assessment Framework & UI

- [x] **Assessment model and lifecycle** - Create Assessment model with status enum: pending, uploading, processing, draft_ready, under_review, signed_off, error. Include status_message for error details.

- [x] **Prompt template system** - Create PromptTemplate model with: name, mode (presenting/explaining/persuading), age_band, template_text (with {{variable}} placeholders), and time_limit_seconds.

- [x] **Assessment creation flow (teacher)** - Build API endpoint to create assessment from template + cohort selection. Generate unique recording prompts for each student.

- [x] **Assessment scheduling** - Add scheduled_date field to Assessment model. Create Celery task to activate assessments at scheduled time.

- [x] **Frontend assessment creation interface** - Build wizard-style form with: template selection, cohort selection, scheduling options, and confirmation step.

---

### Month 2: AI Pipeline & Media Processing (Weeks 5-9)

#### Week 5: Video Upload & Storage

- [x] **S3 bucket configuration with lifecycle policies** - Configure S3 bucket with: lifecycle rules for temporary audio (7 days), transition to IA after 30 days, and Glacier after 1 year. Enable versioning.

- [x] **Presigned URL generation service** - Create Django service to generate presigned URLs for direct-to-S3 uploads. Support both PUT (upload) and GET (streaming) operations.

- [x] **Recording model and metadata storage** - Create Recording model with: s3_bucket, s3_key, file_size_bytes, duration_seconds, video_quality_score, audio_quality_score.

- [x] **Frontend video upload component** - Build DragDropUploader with chunked upload, progress bar, and retry on failure. Integrate with WebSocket for live progress.

---

#### Week 6: Speech-to-Text Pipeline (WhisperX on RunPod)
**V2 Cost-Optimized Implementation**

- **[ ] Create RunPod account and configure billing** - Sign up at runpod.com, add payment method, and create API key. Set up billing alerts for $100/month.

- **[ ] Build Docker image for WhisperX worker with distil-large-v3** - Create Dockerfile based on nvidia/cuda:12.1-ubuntu22.04. Install WhisperX, ffmpeg, and pre-download distil-large-v3 model.

- **[ ] Pre-download model during build for faster cold starts** - Add model download step in Dockerfile to cache ~3GB model files. Verify model files exist before container startup.

- **[ ] Deploy serverless GPU endpoint (RTX 3090)** - Use RunPod console or API to deploy serverless endpoint. Select RTX 3090 GPU, configure 0-3 workers scaling.

- **[ ] Configure flashboot for 2-second cold starts** - Enable flashboot in RunPod settings. Pre-warm endpoint with dummy request on startup.

- **[ ] Test endpoint with sample audio (batch_size=4)** - Send 4 audio files simultaneously to test batch processing. Measure latency and throughput.

- **[ ] Implement `RunPodWhisperXService` class** - Create Python service in server/apps/analysis/services/ with methods: transcribe(audio_url), health_check(), get_usage_stats().

- **[ ] Configure int8 quantization (40% VRAM reduction)** - Use WhisperX quantization parameter to reduce VRAM from ~10GB to ~2.8GB. Verify model loads correctly.

- **[ ] Implement batch processing (4 files simultaneously)** - Modify service to accept list of audio URLs. Process in parallel using RunPod's batch API.

- **[ ] Add forced word alignment for precise timestamps** - Enable forced alignment in WhisperX to get character-level word timestamps. Verify accuracy on test samples.

- **[ ] Add audio extraction from video (ffmpeg)** - Create Celery task to extract audio from uploaded video using ffmpeg: ffmpeg -i input.mp4 -ar 16000 -ac 1 audio.wav

- **[ ] Create transcript model with word-level timestamps** - Create Transcript model with: segments (JSONB), full_text, language, confidence, provider, model_version. Store word-level data in segments.

- **[ ] Implement retry logic for failed jobs** - Use Celery retry with exponential backoff. Maximum 3 retries, then mark assessment as error with status_message.

- **[ ] Run parallel transcription (OpenAI vs WhisperX) validation** - Run same 20 audio files through both OpenAI Whisper API and WhisperX. Calculate WER for comparison.

- **[ ] Calculate Word Error Rate (WER) - target < 18%** - Use jiwer library to calculate WER. Target <18% WER vs OpenAI's 16.7%.

- **[ ] Validate word-level timestamp accuracy** - Manually verify timestamp accuracy on 10 samples. Target <500ms average error.

- **[ ] Frontend transcript viewer component with word highlighting** - Build React component displaying transcript with word-level highlighting. Sync with video player current time.

- **[ ] Click-to-play from any word** - Add onClick handler to each word span to seek video to that timestamp.

- **[ ] Confidence indicators per word** - Display confidence score (0-1) as color/opacity on each word. Use green (high), yellow (medium), red (low).

---

#### Week 7: Feature Extraction Engine

- **[ ] Physical features extraction (librosa, webrtcvad)** - Extract: WPM (words per minute), pause ratio (pauses/total time), filler frequency (um/uh count), volume variance, rhythm stability.

- **[ ] Linguistic features extraction (spaCy, textstat)** - Extract: sentence length variance, vocabulary diversity (unique words/total), prompt relevance (keyword matching), clarity score, register formality.

- **[ ] Cognitive features extraction (keyword matching)** - Extract: reason density (reasoning keywords), counterpoint density (but/however/although), logical connector density (therefore/because), structure completeness.

- **[ ] Social features extraction (VADER sentiment)** - Extract: audience reference frequency (you/we), intention clarity, sentiment compound score.

- **[ ] FeatureSignals model and storage** - Create FeatureSignals model with all feature fields as Float columns. Add quality_flag (good/fair/poor) based on audio quality.

- **[ ] Feature extraction orchestration** - Create Celery task to run all feature extractors sequentially. Store results in FeatureSignals model.

---

#### Week 8: BDL Benchmark System

- **[ ] BDL v0.1 JSON schema definitions** - Define JSON schema for BDL (Band Description Language) with: bands, criteria, weightings, examples.

- **[ ] Benchmark data loader and validator** - Create utility to load BDL JSON files and validate schema compliance.

- **[ ] Benchmark engine (BDL interpreter)** - Create service to interpret BDL and apply scoring logic. Match student features to band criteria.

- **[ ] Evidence candidate generation algorithm** - Create algorithm to identify evidence clips: transcript_boundary (natural pauses), reason_dense (high reasoning keywords), emotion_peaks (sentiment shifts).

- **[ ] EvidenceCandidate model** - Create EvidenceCandidate model with: assessment_id, candidate_id, start_time, end_time, type, summary, features (JSONB).

- **[ ] Initial BDL data for 3 modes × 4 age bands** - Populate benchmark_versions table with initial BDL for: modes (presenting, explaining, persuading) × age bands (9-11, 11-12, 13-14, 14-16).

---

#### Week 9: LLM Scoring Service (OpenRouter)
**V2 Cost-Optimized Implementation**

- **[ ] Create OpenRouter account** - Sign up at openrouter.ai, add credits, generate API key. Configure budget alerts.

- **[ ] Implement `OpenRouterService` class** - Create Python service with: generate(prompt, system_prompt), parse_json_response(), get_usage().

- **[ ] Configure model selection (Gemini Flash, Claude Haiku)** - Support multiple models with fallback. Priority: Gemini Flash 2.0 > Claude Haiku > GPT-4o-mini.

- **[ ] Test structured JSON output parsing** - Verify LLM returns valid JSON for 50 prompts. Handle malformed responses gracefully.

- **[ ] Add fallback to alternative models** - Implement retry logic that tries next model if current fails. Log failures for analysis.

- **[ ] Mode-specific system prompts** - Create system prompts for each mode: presenting (focus on delivery), explaining (focus on clarity), persuading (focus on argumentation).

- **[ ] Rubric-constrained scoring prompts** - Build prompts that include band descriptions from BDL. Constrain LLM to output scores within valid ranges.

- **[ ] DraftReport generation with all strands** - Generate scores for all 4 strands (physical, linguistic, cognitive, social_emotional) in single LLM call.

- **[ ] Evidence clip selection and validation** - Use LLM to select best evidence clips from candidates. Validate clips have sufficient duration (>3s).

- **[ ] Score confidence calculation** - Calculate confidence based on: agreement between models, spread of scores across bands, quality of evidence.

- **[ ] Set up Ollama for local LLM testing (optional)** - Install Ollama locally, download llama3.2:3b. Useful for development without API costs.

- **[ ] Implement `OllamaService` class (optional)** - Mirror OpenRouterService interface for local testing. Useful when API is unavailable.

---

### Month 3: Scoring, Review, Launch & Optimization (Weeks 10-13)

#### Week 10: Teacher Review Interface

- **[ ] Draft report display with strand breakdown** - Build React component showing 4 strand cards with: band name, score (1-9), confidence indicator, justification text.

- **[ ] Video player with evidence clip navigation** - Integrate video player (video.js or similar) with clip markers. Click marker to jump to that timestamp.

- **[ ] Score editing interface with band selector** - Build dropdown/component to select band (1-9) for each strand. Show band description on hover.

- **[ ] Evidence clip replacement workflow** - Allow teacher to: remove existing clip, search transcript for new clip, set custom start/end times.

- **[ ] Evidence clip addition from video** - Add "Add Clip" button to open timestamp picker. Allow manual entry of start/end times.

- **[ ] Feedback editing with rich text** - Use Tiptap or Quill for rich text editing. Support bullet points, bold, italics.

- **[ ] Score comparison (AI vs. Teacher)** - Show side-by-side comparison when teacher modifies AI score. Highlight changes in different color.

---

#### Week 11: Sign-off, Audit & Export

- **[ ] SignedReport model and workflow** - Create SignedReport model copying data from DraftReport. Add: teacher_notes, signed_by, signed_at.

- **[ ] Comprehensive audit logging (all changes)** - Create AuditLog model for: score_changed, clip_changed, feedback_edited, signed. Log old_value and new_value.

- **[ ] PDF report generation with styling** - Use WeasyPrint or similar to generate styled PDF. Include: school header, student info, strand scores, evidence clips, feedback.

- **[ ] Sign-off confirmation with digital signature** - Show confirmation dialog with summary. On confirm, create SignedRecord and trigger notification.

- **[ ] Report sharing (download link)** - Generate time-limited signed URL for PDF. Allow sharing via email within the system.

- **[ ] Audit trail viewer** - Build admin page showing all changes to a report. Filter by action type, user, date range.

---

#### Week 12: Dashboard, Testing & Launch

- **[ ] Teacher dashboard with metrics** - Build dashboard showing: total assessments, completed this week, average score, pending reviews count.

- **[ ] Assessment status tracking (real-time)** - Show live status updates using WebSocket. Display: queued → uploading → processing → draft_ready.

- **[ ] WebSocket integration for live updates** - Set up Django Channels with Redis. Push status updates to frontend in real-time.

- **[ ] Error handling and retry mechanisms** - Implement proper error handling in all Celery tasks. Add dead letter queue for failed tasks after max retries.

- **[ ] End-to-end testing completion** - Write E2E tests using Playwright covering: student upload flow, teacher review flow, sign-off flow.

- **[ ] Performance optimization** - Profile API endpoints with Silk. Optimize N+1 queries, add select_related/prefetch_related.

- **[ ] Documentation finalization** - Complete API documentation (Swagger/OpenAPI). Write user guides for students and teachers.

---

#### Week 13: Cost Optimization & Monitoring (V2)

- **[ ] Set up AWS Cost Anomaly Detection** - Enable Cost Anomaly Detection in AWS Console. Create monitor for unusual spending patterns.

- **[ ] Configure budget alerts ($1000/month threshold)** - Set up AWS Budgets with: $1000/month threshold, 50% alert, 80% alert, 100% alert. Email to admin.

- **[ ] Implement cost tracking dashboard** - Create dashboard showing: daily costs by service, cost per assessment trend, forecast for month end.

- **[ ] Add cost allocation tags to all resources** - Apply tags: Environment (prod/staging), Service (api/worker), CostCenter (oracy-mvp).

- **[ ] Set up weekly cost reports** - Schedule email report every Monday showing: week total, vs previous week, vs budget.

- **[ ] Enable Fargate Spot for Celery workers** - Update ECS task definition to use FARGATE_SPOT capacity provider. Set up Spot interruption handling.

- **[ ] Test spot interruption handling** - Simulate Spot interruption (AWS can do this). Verify Celery retries task on different instance.

- **[ ] Configure task retry policies** - Set Celery task retry: max_retries=3, default_retry_delay=60 (exponential backoff).

- **[ ] Monitor spot instance availability** - Check Spot availability in current region. Consider fallback to On-Demand if unavailable.

- **[ ] Apply Intelligent-Tiering to media bucket** - Enable S3 Intelligent-Tiering for frequent/inrequent access optimization. Monitor for optimization savings.

- **[ ] Configure lifecycle policies for uploads/exports** - Set: temp files 7 days, exports 90 days, media 7 years (with Glacier).

- **[ ] Run full pipeline with 50 test assessments** - Execute 50 end-to-end assessments through full pipeline. Measure: latency, cost, quality.

- **[ ] Calculate actual cost per assessment** - Sum all costs (STT, LLM, compute, storage) / 50. Verify target < $0.50.

---

## Post-MVP Roadmap

### Phase 1: Stabilization & Polish (Months 4-5)

**Goals: Production hardening, Security audit, Performance optimization**

- **[ ] Security audit with external firm** - Hire third-party security firm to audit code, infrastructure, and processes. Address critical findings.

- **[ ] GDPR compliance certification** - Implement required GDPR features: data export, deletion, consent management. Get certification.

- **[ ] Penetration testing** - Conduct pen testing to identify vulnerabilities. Fix findings before public launch.

- **[ ] Performance monitoring (Datadog/New Relic)** - Deploy APM agent. Set up dashboards for: response time, error rate, throughput.

- **[ ] Error tracking (Sentry integration)** - Integrate Sentry for error tracking. Set up alerts for new error patterns.

- **[ ] Automated alerting** - Configure PagerDuty or similar for on-call. Define escalation policies.

- **[ ] User onboarding improvements** - Add tooltips, tutorials, guided walkthrough for first-time users. Collect feedback.

- **[ ] Help documentation and tutorials** - Create knowledge base with: getting started, FAQ, video tutorials.

- **[ ] In-app feedback system** - Add "Give Feedback" button. Capture screenshots and user comments.

**V2 Specific:**
- **[ ] RunPod endpoint monitoring** - Set up health checks and alerting for RunPod endpoint availability.
- **[ ] OpenRouter usage analytics** - Monitor API usage, costs, and rate limits. Alert on unusual patterns.
- **[ ] Fallback service health checks** - Implement periodic health checks for Vast.ai and Ollama fallbacks.
- **[ ] Cost per assessment tracking** - Track cost per assessment in production. Alert if > $0.50 target.

---

### Phase 2: Feature Expansion (Months 6-8)

**Student-Facing Features:**

- **[ ] Student dashboard (view progress, history)** - Build student-facing dashboard showing: completed assessments, scores over time, feedback history.

- **[ ] Practice mode (self-assessment without teacher)** - Allow students to record practice sessions without teacher assignment. Get AI feedback but no formal report.

- **[ ] Goal setting and tracking** - Allow students to set goals (e.g., "Improve speaking rate"). Track progress over time.

- **[ ] Achievement badges** - Implement badge system: First Recording, 10 Assessments, Perfect Score, etc. Display on profile.

- **[ ] Peer comparison (anonymized)** - Show student's performance vs cohort average (anonymized). No individual identification.

**Teacher Features:**

- **[ ] Bulk assessment creation wizard** - Multi-step wizard for creating many assessments at once. Select template, cohorts, date range.

- **[ ] Cohort analytics and insights** - Show cohort-level analytics: average scores, common areas for improvement, progress over time.

- **[ ] Progress tracking over time (charts)** - Build charts showing student/cohort progress. Use Recharts or similar library.

- **[ ] Student comparison tools** - Allow teachers to compare students within cohort on various metrics.

- **[ ] Comment templates** - Allow teachers to save and reuse common feedback snippets. Quick-insert in feedback editor.

- **[ ] Gradebook integration preparation** - Build API for gradebook integration. Support common formats (CSV, JSON).

**Administrative:**

- **[ ] School admin dashboard** - Dashboard for school admins: user counts, storage usage, billing status.

- **[ ] User management (invite, deactivate)** - Allow school admins to invite teachers, manage user access.

- **[ ] Billing and usage analytics** - Show billing history, usage by department, cost forecasts.

- **[ ] Benchmark version management UI** - Admin interface to upload and manage BDL versions.

- **[ ] Custom rubric builder (basic)** - Allow admins to create custom rubrics. Basic version (edit descriptions, not structure).

---

### Phase 3: AI Enhancement (Months 9-12)

**Prerequisites:**
- Minimum 500 teacher-reviewed assessments
- Sufficient variation in age bands and modes
- Cost per assessment < $0.50 confirmed

#### Phase 3.1: Scoring Model Training (Months 9-10)

- **[ ] Collect teacher edit data** - Export all cases where teacher modified AI score. Create training dataset.

- **[ ] Feature engineering from corrections** - Analyze what features correlate with teacher edits. Engineer new features.

- **[ ] Train classification model (strand → band)** - Train model to predict band from features. Use scikit-learn or similar.

- **[ ] A/B testing: LLM vs. Custom model** - Run both scoring methods on same assessments. Compare to teacher scores.

- **[ ] Gradual rollout with fallback** - Deploy custom model with LLM as fallback. Monitor accuracy.

- **[ ] Calculate training costs (SageMaker vs. RunPod)** - Compare cost of training on SageMaker vs. RunPod instances.

- **[ ] Compare inference costs: Custom model vs. OpenRouter** - Calculate cost per assessment with custom model vs. OpenRouter.

#### Phase 3.2: Evidence Ranking Model (Months 10-11)

- **[ ] Train model to select best evidence clips** - Train model to predict which clips are most relevant for each band.

- **[ ] Teacher preference learning** - Learn from which clips teachers keep vs. replace.

- **[ ] Replace deterministic selection** - Replace current rule-based selection with ML model.

- **[ ] Confidence scoring for evidence** - Output confidence score for each selected clip.

#### Phase 3.3: Advanced AI Features (Months 11-12)

- **[ ] Real-time coaching feedback (optional toggle)** - During recording, show real-time metrics: pace, filler words, volume.

- **[ ] Predictive analytics (at-risk students)** - Identify students who may struggle based on history. Suggest interventions.

- **[ ] Personalized improvement suggestions** - Generate personalized practice suggestions based on student's weak areas.

- **[ ] Automated progress reports** - Generate automated progress reports for parents/guardians.

---

### Phase 4: Scale & Enterprise (Year 2)

**Scalability:**

- **[ ] Read replicas for reporting queries** - Add RDS read replica. Route read-heavy queries to replica.

- **[ ] Database partitioning by school** - Implement database sharding by school_id for multi-tenant isolation.

- **[ ] Multi-region deployment (EU, US)** - Deploy to EU and US regions. Implement data residency controls.

- **[ ] CDN for global video delivery** - Set up CloudFront for global video streaming. Reduce latency worldwide.

- **[ ] Auto-scaling policies refinement** - Tune ECS auto-scaling based on production metrics.

**V2 Cost Optimization:**

- **[ ] Evaluate RunPod vs. Vast.ai at scale** - Compare pricing and performance at higher volumes.

- **[ ] Consider dedicated GPU server purchase** - Calculate ROI of dedicated GPU server vs. cloud GPU services.

- **[ ] Implement hybrid cloud/on-premise option** - Allow schools to host on-premise for data sovereignty.

- **[ ] Optimize model quantization for faster inference** - Further optimize models for lower latency/cost.

**Enterprise Features:**

- **[ ] MIS integration (SIMS, Arbor, PowerSchool)** - Build integrations with common UK MIS systems.

- **[ ] SAML/SSO authentication (Google, Microsoft)** - Implement SAML 2.0 for enterprise SSO.

- **[ ] Custom data retention policies** - Allow schools to configure data retention periods.

- **[ ] On-premise deployment option** - Package application for Docker-based on-premise deployment.

- **[ ] Advanced analytics and reporting** - Build analytics dashboard with custom reports, scheduled emails.

- **[ ] API access for integrations** - Public API with rate limiting, authentication, documentation.

---

## V2 Infrastructure Checklist

### Week 1: AWS Setup

- **[ ] RunPod account configured** - Sign up, add payment, generate API key.

- **[ ] Serverless GPU endpoint deployed (RTX 3090)** - Deploy serverless endpoint in RunPod console.

- **[ ] Docker image for WhisperX worker built with distil-large-v3** - Build and push Docker image to RunPod registry.

- **[ ] Model pre-downloaded in Docker image (faster cold start)** - Verify model files in image (~3GB).

- **[ ] Flashboot enabled (2s cold start target)** - Enable flashboot in endpoint settings.

- **[ ] OpenRouter account created** - Sign up, add credits, generate API key.

- **[ ] Ollama installed (local development)** - Install and verify Ollama works locally.

### Week 6: STT Pipeline

- **[ ] `RunPodWhisperXService` implemented** - Python class with transcribe() method.

- **[ ] WhisperX with distil-large-v3 configured** - Verify model loads and runs.

- **[ ] int8 quantization enabled (2.8GB VRAM)** - Verify quantization reduces VRAM usage.

- **[ ] Batch processing (4 files) working** - Test batch of 4 files.

- **[ ] Forced word alignment implemented** - Verify word-level timestamps.

- **[ ] Audio extraction working** - FFmpeg extracts audio from video.

- **[ ] Transcript model with word timestamps created** - Database model and API working.

- **[ ] Parallel validation complete (WER < 18% vs OpenAI 16.7%)** - WER measurement complete.

- **[ ] Retry logic implemented** - Celery retries on failure.

### Week 9: LLM Scoring

- **[ ] `OpenRouterService` implemented** - Python class with generate() method.

- **[ ] Multiple model support configured** - Fallback chain working.

- **[ ] Structured JSON output validated** - JSON parsing handles edge cases.

- **[ ] Fallback to alternative models working** - Retry with different model on failure.

- **[ ] Cost per assessment < $0.50 achieved** - Cost analysis complete.

### Week 13: Cost Optimization

- **[ ] AWS Cost Anomaly Detection enabled** - Monitor created and alerting.

- **[ ] Budget alerts configured** - Budgets set up with email notifications.

- **[ ] Fargate Spot enabled for workers** - Task definition updated.

- **[ ] S3 Intelligent-Tiering applied** - Bucket configuration complete.

- **[ ] Cost tracking dashboard deployed** - Dashboard shows real-time costs.

---

## Risk Mitigation Tasks

| Risk | Mitigation Action |
|------|-------------------|
| RunPod service outage | Implement Vast.ai and CPU fallback |
| OpenRouter rate limits | Implement local Ollama fallback |
| Cold start latency | Configure flashboot; cache warm workers |
| V2 accuracy lower than V1 | Parallel validation; keep V1 as backup |
| Cost savings not achieved | Weekly cost reviews; adjust resource sizes |

---

## Success Metrics

### Technical Metrics

- **[ ] STT Word Error Rate < 5% (vs OpenAI Whisper)** - Measure WER difference between WhisperX and OpenAI Whisper.

- **[ ] LLM scoring correlation > 0.95 (vs GPT-4o)** - Calculate Pearson correlation between OpenRouter and GPT-4o scores.

- **[ ] End-to-end latency < 3 minutes (95th percentile)** - Measure p95 latency from upload to draft ready.

- **[ ] System availability > 99.5%** - Monitor uptime with ping checks.

### Cost Metrics

- **[ ] Cost per assessment < $0.50 (full pipeline)** - Total costs / assessment count.

- **[ ] Monthly infrastructure < $700** - AWS costs for month.

- **[ ] 60% savings vs V1 architecture achieved** - (V1 cost - V2 cost) / V1 cost.

### Business Metrics

- **[ ] 50 assessments processed in testing** - QA testing complete.

- **[ ] Teacher satisfaction with report quality** - Survey teachers on report usefulness.

- **[ ] Zero data quality complaints** - No complaints about accuracy.

---

## Database Models to Implement

### Core Tables

- **[ ] schools** - id, name, identifier, region, created_at
- **[ ] users (Django AbstractUser extension)** - id, email, password_hash, role, school_id, first_name, last_name
- **[ ] students** - id, user_id, student_id, date_of_birth, year_group, age_band, eal, first_language, accommodations
- **[ ] cohorts** - id, teacher_id, name, year_group, academic_year
- **[ ] enrollments** - id, student_id, cohort_id, enrolled_at

### Assessment Tables

- **[ ] assessments** - id (UUID), student_id, cohort_id, mode, prompt, time_limit_seconds, status, consent_obtained
- **[ ] recordings** - id, assessment_id, s3_bucket, s3_key, file_size_bytes, duration_seconds

### Analysis Tables

- **[ ] transcripts** - id, assessment_id, segments (JSONB), full_text, confidence, provider, model_version
- **[ ] feature_signals** - id, assessment_id, wpm, pause_ratio, filler_frequency, [all physical/linguistic/cognitive/social features]
- **[ ] evidence_candidates** - id, assessment_id, candidate_id, start_time, end_time, type, summary, features

### Report Tables

- **[ ] draft_reports** - id, assessment_id, physical_score (JSONB), linguistic_score, cognitive_score, social_emotional_score, feedback, ai_model
- **[ ] signed_reports** - id, assessment_id, draft_id, [final scores], teacher_notes, signed_by, signed_at
- **[ ] audit_logs** - id, report_id, user_id, action, field, old_value, new_value, timestamp

### Benchmark Tables

- **[ ] benchmark_versions** - id, version, age_band, mode, definition (JSONB), is_active

---

## API Endpoints to Build

### Authentication

- **[ ] POST /api/auth/register/** - Register new user (student/teacher)
- **[ ] POST /api/auth/login/** - Get JWT tokens
- **[ ] POST /api/auth/logout/** - Invalidate refresh token
- **[ ] POST /api/auth/password-reset/** - Request password reset email
- **[ ] GET /api/auth/me/** - Get current user profile

### Students

- **[ ] GET /api/students/** - List students (with filters)
- **[ ] POST /api/students/** - Create new student
- **[ ] GET /api/students/{id}/** - Get student details
- **[ ] PUT /api/students/{id}/** - Update student
- **[ ] DELETE /api/students/{id}/** - Delete student (soft delete)
- **[ ] POST /api/students/import-csv/** - Bulk import from CSV

### Cohorts

- **[ ] GET /api/cohorts/** - List teacher's cohorts
- **[ ] POST /api/cohorts/** - Create new cohort
- **[ ] GET /api/cohorts/{id}/** - Get cohort details
- **[ ] PUT /api/cohorts/{id}/** - Update cohort
- **[ ] POST /api/cohorts/{id}/enroll/** - Enroll students
- **[ ] POST /api/cohorts/{id}/unenroll/** - Unenroll students

### Assessments

- **[ ] GET /api/assessments/** - List assessments (with filters)
- **[ ] POST /api/assessments/** - Create new assessment
- **[ ] GET /api/assessments/{id}/** - Get assessment details
- **[ ] PUT /api/assessments/{id}/** - Update assessment
- **[ ] POST /api/assessments/{id}/upload-video/** - Get presigned URL
- **[ ] GET /api/assessments/{id}/status/** - Get processing status

### Reports

- **[ ] GET /api/reports/draft/{assessment_id}/** - Get draft report
- **[ ] PUT /api/reports/draft/{assessment_id}/** - Update draft (teacher edits)
- **[ ] POST /api/reports/{assessment_id}/sign-off/** - Sign off report
- **[ ] GET /api/reports/{assessment_id}/pdf/** - Generate PDF
- **[ ] GET /api/reports/{assessment_id}/audit/** - Get audit trail

### Benchmarks

- **[ ] GET /api/benchmarks/** - List benchmark versions
- **[ ] GET /api/benchmarks/{version}/{age_band}/{mode}/** - Get specific benchmark

---

## Frontend Pages to Build

### Authentication

- **[ ] Login Page (/login)** - Email/password form, remember me, forgot password link
- **[ ] Register Page (/register)** - Role selection, school code, form fields
- **[ ] Password Reset Page (/password-reset)** - Request reset, enter new password

### Student

- **[ ] Student Dashboard (/dashboard)** - Show assigned assessments, progress
- **[ ] Assessment Task Page (/task/:id)** - Show prompt, start recording button
- **[ ] Recording Page (/record/:id)** - WebRTC recorder, countdown, preview
- **[ ] Progress Page (/progress)** - Show scores over time, feedback history

### Teacher

- **[ ] Teacher Dashboard (/teacher)** - Cohort overview, pending reviews, metrics
- **[ ] Cohort Management (/teacher/cohorts)** - CRUD for cohorts, student list
- **[ ] Student Management (/teacher/students)** - Student list, filters, CSV upload
- **[ ] Assessment Creation (/teacher/assessments/new)** - Wizard for creating assessments
- **[ ] Assessment Review (/teacher/review/:id)** - Video player, report editor, sign-off

### Admin

- **[ ] School Admin Dashboard (/admin)** - User management, usage stats
- **[ ] User Management (/admin/users)** - Invite, deactivate, role management
- **[ ] Benchmark Management (/admin/benchmarks)** - Upload/edit BDL versions
- **[ ] Reports & Analytics (/admin/reports)** - System-wide analytics
