# AWS Infrastructure

## Overview

This document describes the AWS infrastructure architecture for Oracy AI, designed for scalability, security, and cost-efficiency.

## VPC Architecture

### Network Layout

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              VPC (10.0.0.0/16)                                  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                        PUBLIC SUBNETS                                      │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐ │  │
│  │  │  Public Subnet A    │  │  Public Subnet B    │  │  Public Subnet C │ │  │
│  │  │  (10.0.1.0/24)      │  │  (10.0.2.0/24)      │  │  (10.0.3.0/24)   │ │  │
│  │  │                     │  │                     │  │                  │ │  │
│  │  │  • ALB              │  │  • NAT Gateway B    │  │  • NAT Gateway C │ │  │
│  │  │  • Bastion Host     │  │                     │  │                  │ │  │
│  │  └─────────────────────┘  └─────────────────────┘  └──────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                           │                                      │
│                                           │ IGW                                   │
│                                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                        PRIVATE APP SUBNETS                                 │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐ │  │
│  │  │  App Subnet A       │  │  App Subnet B       │  │  App Subnet C    │ │  │
│  │  │  (10.0.10.0/24)     │  │  (10.0.11.0/24)     │  │  (10.0.12.0/24)  │ │  │
│  │  │                     │  │                     │  │                  │ │  │
│  │  │  • ECS Fargate      │  │  • ECS Fargate      │  │  • ECS Fargate   │ │  │
│  │  │    (Django API)     │  │    (Celery Worker)  │  │    (Celery Beat) │ │  │
│  │  └─────────────────────┘  └─────────────────────┘  └──────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                           │                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                        PRIVATE DATA SUBNETS                                │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐ │  │
│  │  │  Data Subnet A      │  │  Data Subnet B      │  │  Data Subnet C   │ │  │
│  │  │  (10.0.20.0/24)     │  │  (10.0.21.0/24)     │  │  (10.0.22.0/24)  │ │  │
│  │  │                     │  │                     │  │                  │ │  │
│  │  │  • RDS PostgreSQL   │  │  • RDS PostgreSQL   │  │  • ElastiCache   │ │  │
│  │  │    (Primary)        │  │    (Standby)        │  │    Redis         │ │  │
│  │  └─────────────────────┘  └─────────────────────┘  └──────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Availability Zones
- **3 AZs minimum** (ap-southeast-1a, ap-southeast-1b, ap-southeast-1c for Singapore)
- Resources distributed across AZs for high availability

### Network Components

| Component | CIDR | Purpose |
|-----------|------|---------|
| VPC | 10.0.0.0/16 | Main network |
| Public Subnets | 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24 | Load balancers, NAT gateways |
| Private App | 10.0.10.0/24, 10.0.11.0/24, 10.0.12.0/24 | ECS services |
| Private Data | 10.0.20.0/24, 10.0.21.0/24, 10.0.22.0/24 | Databases, cache |

### Security Groups

```
┌─────────────────────────────────────────────────────────────────┐
│  ALB Security Group                                             │
│  Ingress:                                                       │
│    • 80/tcp from 0.0.0.0/0 (redirect to 443)                    │
│    • 443/tcp from 0.0.0.0/0 (CloudFront or direct)              │
│  Egress: All                                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ECS Service Security Group                                     │
│  Ingress:                                                       │
│    • 8000/tcp from ALB SG                                       │
│  Egress:                                                        │
│    • 5432/tcp to RDS SG                                         │
│    • 6379/tcp to ElastiCache SG                                 │
│    • 443/tcp to S3 API                                          │
│    • 443/tcp to external APIs (OpenAI, etc.)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RDS Security Group                                           │
│  Ingress:                                                       │
│    • 5432/tcp from ECS Service SG                               │
│    • 5432/tcp from Bastion SG (admin)                           │
│  Egress: None (no outbound needed)                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Compute Layer

### ECS Fargate Cluster

#### Service Configuration

| Service | Task CPU | Task Memory | Min | Max | Purpose |
|---------|----------|-------------|-----|-----|---------|
| Django API | 512 | 1024 | 2 | 10 | Main API server |
| Celery Worker | 1024 | 2048 | 2 | 20 | AI pipeline processing |
| Celery Beat | 256 | 512 | 1 | 1 | Task scheduler |
| WebSocket | 512 | 1024 | 2 | 5 | Real-time notifications |

#### Task Definitions

```json
{
  "family": "oracy-django-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/oracy-ecs-task-role",
  "containerDefinitions": [
    {
      "name": "django",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/oracy-django:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DJANGO_SETTINGS_MODULE", "value": "config.settings.production"},
        {"name": "DATABASE_URL", "value": "${DATABASE_URL}"},
        {"name": "REDIS_URL", "value": "${REDIS_URL}"}
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:oracy/secret-key"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:oracy/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/oracy-django",
          "awslogs-region": "ap-southeast-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Auto Scaling Policies

**Django API Service:**
- Target tracking on ALB request count per target (target: 1000)
- Scale out: +2 tasks when CPU > 70% for 2 minutes
- Scale in: -1 task when CPU < 30% for 5 minutes
- Cooldown: 300 seconds

**Celery Worker Service:**
- Scale based on SQS queue depth (if using SQS) or Redis queue length
- Target queue depth: 100 messages per worker
- Max workers: 20 (to control AI API costs)

---

## Database Layer

### RDS PostgreSQL

#### Instance Configuration (MVP)

| Setting | Value |
|---------|-------|
| Engine | PostgreSQL 15.4 |
| Instance Class | db.t3.medium (can scale to db.r6g.xlarge) |
| Multi-AZ | Yes (production) / No (dev) |
| Storage | 100GB GP3 (auto-scaling enabled) |
| IOPS | 3000 |
| Backup Retention | 7 days |
| Encryption | AWS KMS (AES-256) |
| Maintenance Window | Sunday 03:00-04:00 UTC |

#### Parameter Group Settings

```ini
max_connections = 200
shared_buffers = {DBInstanceClassMemory/32768}
effective_cache_size = {DBInstanceClassMemory/8192}
work_mem = {DBInstanceClassMemory/32768/max_connections}
maintenance_work_mem = {DBInstanceClassMemory/8192}

# Logging
log_statement = 'mod'
log_min_duration_statement = 1000
log_connections = on
log_disconnections = on

# Performance
random_page_cost = 1.1
effective_io_concurrency = 200
```

#### Read Replica (Future)
- Add read replica for reporting/analytics queries
- Cross-region replica for disaster recovery

### ElastiCache Redis

#### Cluster Configuration

| Setting | Value |
|---------|-------|
| Node Type | cache.t3.micro (dev) / cache.m6g.large (prod) |
| Engine | Redis 7.0 |
| Cluster Mode | Disabled (single node for MVP, cluster later) |
| Multi-AZ | Yes |
| Auto-failover | Yes |
| Encryption | In-transit (TLS) and at-rest |
| Snapshot Retention | 1 day |

#### Redis Use Cases
1. **Session Storage**: Django session backend
2. **Celery Broker**: Task queue
3. **Celery Result Backend**: Task results
4. **API Cache**: Frequently accessed data (benchmarks, user profiles)
5. **Rate Limiting**: Django ratelimit backend

---

## Storage Layer

### S3 Buckets

#### Bucket Structure

```
oracy-{environment}-media              # Video/audio recordings
  ├── uploads/                         # Temporary upload staging
  ├── recordings/                      # Final processed recordings
  │   ├── {year}/                    # Organized by year
  │   │   ├── {month}/
  │   │   │   ├── {assessment_id}/
  │   │   │   │   ├── video.mp4
  │   │   │   │   ├── audio.wav
  │   │   │   │   └── thumbnail.jpg
  ├── clips/                           # Evidence clips
  └── exports/                         # Generated PDFs

oracy-{environment}-assets            # Static assets (CSS, JS, images)
  ├── static/                          # Django collectstatic output
  └── media/                           # User-uploaded assets

oracy-{environment}-logs               # Application logs
  ├── app-logs/                        # Django application logs
  ├── alb-logs/                        # Load balancer access logs
  └── cloudtrail/                      # AWS API audit logs

oracy-{environment}-backups            # Database backups
  ├── rds-snapshots/                   # Automated RDS backups
  └── manual/                          # Manual backups
```

#### S3 Security Configuration

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyNonSSL",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::oracy-prod-media/*",
        "arn:aws:s3:::oracy-prod-media"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    },
    {
      "Sid": "AllowECSTaskRole",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:role/oracy-ecs-task-role"
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::oracy-prod-media/*"
    }
  ]
}
```

#### S3 Lifecycle Policies

| Bucket Path | Transition to IA | Transition to Glacier | Expiration |
|-------------|------------------|----------------------|------------|
| uploads/* | 1 day | - | 7 days (temporary) |
| recordings/* | 30 days | 90 days | Never (7yr retention) |
| clips/* | 30 days | 90 days | Never |
| exports/* | 7 days | 30 days | 365 days |

### CloudFront Distribution

#### Distribution Configuration

| Setting | Value |
|---------|-------|
| Origins | S3 (assets), ALB (API), S3 (media streaming) |
| Price Class | PriceClass_All (global) or PriceClass_100 (Asia focus) |
| SSL | ACM certificate (oracy.ai, *.oracy.ai) |
| Compression | Brotli and Gzip |
| HTTP/2 & HTTP/3 | Enabled |
| WAF | AWS WAF Web ACL attached |

#### Cache Behaviors

| Path Pattern | Origin | TTL | Forward Headers |
|--------------|--------|-----|-----------------|
| /api/* | ALB | 0 (no cache) | All |
| /ws/* | ALB | 0 (WebSocket) | All |
| /static/* | S3 Assets | 1 year | None |
| /media/recordings/* | S3 Media | 1 hour (signed URLs) | Authorization |
| /* | S3 Assets | Default | None |

#### Signed URLs for Video

All video access through CloudFront with signed URLs:
- URL expiration: 1 hour
- Restrict viewer access: Yes
- Trusted signer: Or account

---

## AI/ML Services (AWS Native)

### AWS Transcribe (Optional/Fallback)

#### Usage Pattern
```python
# For high-accuracy fallback or batch processing
import boto3

transcribe = boto3.client('transcribe')

response = transcribe.start_transcription_job(
    TranscriptionJobName=f"oracy-{assessment_id}",
    Media={'MediaFileUri': f's3://oracy-media/recordings/{path}'},
    MediaFormat='mp4',
    LanguageCode='en-GB',  # or en-US
    Settings={
        'ShowSpeakerLabels': False,
        'MaxSpeakerLabels': 1,
        'ChannelIdentification': False,
        'ShowAlternatives': False,
    },
    OutputBucketName='oracy-transcripts',
    OutputKey=f'{assessment_id}/transcript.json'
)
```

### Amazon SageMaker (Future Custom Models)

Reserved for Phase 2 custom model training:
- Notebook instances for experimentation
- Training jobs for rubric classifier
- Endpoints for model serving
- Model monitoring and drift detection

---

## Security & IAM

### IAM Roles

#### ECS Task Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:oracy/*"
    }
  ]
}
```

#### ECS Task Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::oracy-*-media/*",
        "arn:aws:s3:::oracy-*-exports/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "transcribe:StartTranscriptionJob",
        "transcribe:GetTranscriptionJob"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    }
  ]
}
```

### Secrets Manager

Secrets stored in AWS Secrets Manager:
- `oracy/secret-key` - Django SECRET_KEY
- `oracy/openai-key` - OpenAI API key
- `oracy/anthropic-key` - Anthropic API key
- `oracy/database-password` - RDS master password
- `oracy/jwt-signing-key` - JWT signing key

### KMS Keys

| Key Alias | Purpose |
|-----------|---------|
| `alias/oracy-rds` | RDS encryption |
| `alias/oracy-s3` | S3 bucket encryption |
| `alias/oracy-secrets` | Secrets Manager encryption |
| `alias/oracy-ebs` | EBS volume encryption |

---

## Monitoring & Logging

### CloudWatch

#### Log Groups
- `/ecs/oracy-django` - Django application logs
- `/ecs/oracy-celery` - Celery worker logs
- `/aws/alb/oracy` - Load balancer access logs
- `/aws/rds/oracy` - RDS slow query logs

#### Metrics & Alarms

| Metric | Threshold | Action |
|--------|-----------|--------|
| ECS CPU Utilization | > 80% for 5 min | Scale out |
| ECS Memory Utilization | > 85% for 5 min | Alert + Review |
| RDS CPU Utilization | > 80% for 10 min | Scale up instance |
| RDS FreeableMemory | < 100MB | Alert immediately |
| S3 5xx Errors | > 10 in 5 min | Alert + Investigate |
| ALB 5xx Errors | > 1% of requests | Alert + Investigate |

### X-Ray

Enable distributed tracing:
- Django middleware for request tracing
- Celery task tracing
- AWS SDK instrumentation (boto3)

### CloudTrail

- Log all API calls to S3, RDS, IAM
- Store logs in S3 with Glacier transition
- Enable log file validation

---

## Cost Optimization

### Reserved Capacity
- RDS Reserved Instances (1-year, no upfront)
- Savings Plans for Fargate compute

### Spot Instances (Optional)
- Use Fargate Spot for Celery workers (fault-tolerant)
- Up to 70% cost savings

### S3 Intelligent Tiering
- Automatically move infrequently accessed videos to cheaper tiers

### CloudFront Caching
- Aggressive caching for static assets
- Reduce origin requests by 90%+
