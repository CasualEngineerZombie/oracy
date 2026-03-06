# Oracy AI - Implementation Plan

## Executive Summary

Oracy AI is a pilot-ready MVP that produces teacher-verifiable, inspection-grade evidence of oracy progression from a single student recording (solo mode only in MVP). The system uses a multi-stage AI pipeline to analyze video/audio recordings and generate structured assessment reports across four strands: Physical, Linguistic, Cognitive, and Social-emotional.

## Table of Contents

1. [Architecture Overview](./01-architecture-overview.md)
   - System Architecture Diagram
   - High-Level Data Flow
   - Core Components

2. [Tech Stack](./02-tech-stack.md)
   - Frontend (React)
   - Backend (Django)
   - Database & Storage
   - AI/ML Services
   - DevOps & Infrastructure

3. [AWS Infrastructure](./03-aws-infrastructure.md)
   - VPC & Networking
   - Compute (ECS/Fargate, EC2)
   - Storage (S3, RDS, ElastiCache)
   - AI/ML Services (AWS Transcribe, SageMaker)
   - Security & IAM
   - CDN & CloudFront

4. [AI/ML Pipeline](./04-ai-ml-pipeline.md)
   - Speech-to-Text (OpenAI Whisper/AWS Transcribe)
   - Deterministic Feature Extraction
   - Benchmarking Layer (Core IP)
   - Evidence Candidate Generation
   - Rubric-Constrained LLM Scoring
   - Model Selection & Providers

5. [Backend Structure](./05-backend-structure.md)
   - Django Project Structure
   - Apps & Responsibilities
   - Database Schema
   - API Design (REST + WebSocket)
   - Background Jobs (Celery)

6. [Frontend Structure](./06-frontend-structure.md)
   - React Project Structure
   - Component Architecture
   - State Management
   - Routing & Navigation
   - Video Recording & Playback

7. [Database Schema](./07-database-schema.md)
   - Core Tables
   - Relationships
   - Indexes & Constraints
   - Data Retention

8. [Security & Compliance](./08-security-compliance.md)
   - Authentication & Authorization
   - Data Protection (GDPR/Schrems II)
   - Video Storage Security
   - Audit Logging

9. [Development Roadmap](./09-development-roadmap.md)
   - Week 1 Deliverables
   - Week 2 Deliverables
   - Post-MVP Phases
   - Future Model Training Strategy

10. [Deployment Strategy](./10-deployment-strategy.md)
    - CI/CD Pipeline
    - Environment Management
    - Blue/Green Deployment
    - Monitoring & Alerting

## Quick Reference

### MVP Assessment Modes
- **Presenting** - Solo presentation skills
- **Explaining** - Explanation and clarification
- **Persuading** - Argumentation and persuasion

### Four Assessment Strands
1. **Physical** - Delivery, pace, volume, fillers
2. **Linguistic** - Vocabulary, clarity, register
3. **Cognitive** - Structure, reasoning, examples
4. **Social-emotional** - Intention, tone, audience awareness

### Band Levels
- **Emerging** - Below age expectation
- **Expected** - At age expectation
- **Exceeding** - Above age expectation

### AI Pipeline Stages
1. Speech-to-Text (Timestamped)
2. Deterministic Feature Extraction
3. Benchmarking Layer
4. Evidence Candidate Generation
5. Rubric-Constrained LLM Scoring

---

*Document Version: 1.0*
*Last Updated: March 2026*
*Status: Draft*
