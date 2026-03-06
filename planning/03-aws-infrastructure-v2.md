# AWS Infrastructure V2 (Cost-Optimized)

## Overview

This document describes the cost-optimized infrastructure for Oracy AI V2. The primary goal is to maintain reliability and scalability while significantly reducing costs by:

1. Removing expensive managed AI services (AWS Transcribe)
2. Using self-hosted GPU compute (RunPod/Vast.ai) instead of per-use APIs
3. Optimizing instance sizes and scaling policies
4. Adding cost monitoring and alerting

## Cost Comparison: V1 vs V2

| Component | V1 (Cloud-Native) | V2 (Cost-Optimized) | Monthly Savings |
|-----------|-------------------|---------------------|-----------------|
| STT (1,000 assessments) | $600 (OpenAI + AWS) | $50 (self-hosted) | $550 (92%) |
| LLM Scoring | $400 (OpenAI) | $100 (OpenRouter) | $300 (75%) |
| Compute (ECS) | $400 | $300 | $100 (25%) |
| Database | $200 | $150 | $50 (25%) |
| Storage/Transfer | $150 | $100 | $50 (33%) |
| **Total** | **$1,750** | **$700** | **$1,050 (60%)** |

---

## Architecture Changes

### High-Level Changes

```
V1 Architecture (Cloud-Native):
┌─────────────────────────────────────────────────────────────┐
│  ECS Fargate → OpenAI API (Whisper)                         │
│             → AWS Transcribe (fallback)                     │
│             → OpenAI API (GPT-4o)                           │
└─────────────────────────────────────────────────────────────┘

V2 Architecture (Cost-Optimized):
┌─────────────────────────────────────────────────────────────┐
│  ECS Fargate → RunPod Serverless GPU (Whisper)              │
│             → OpenRouter (Multiple LLM providers)           │
│             → Ollama (Local LLM fallback)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## VPC Architecture (Unchanged)

The VPC architecture remains the same as V1:

| Component | CIDR | Purpose |
|-----------|------|---------|
| VPC | 10.0.0.0/16 | Main network |
| Public Subnets | 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24 | Load balancers, NAT gateways |
| Private App | 10.0.10.0/24, 10.0.11.0/24, 10.0.12.0/24 | ECS services |
| Private Data | 10.0.20.0/24, 10.0.21.0/24, 10.0.22.0/24 | Databases, cache |

---

## Compute Layer

### ECS Fargate - Optimized Task Sizes

V2 reduces task sizes and uses spot capacity where possible:

| Service | V1 Spec | V2 Spec | Change | Monthly Savings |
|---------|---------|---------|--------|-----------------|
| Django API | 512 CPU / 1024 MB | 256 CPU / 512 MB | -50% | ~$40 |
| Celery Worker | 1024 CPU / 2048 MB | 512 CPU / 1024 MB | -50% | ~$80 |
| Celery Beat | 256 CPU / 512 MB | 128 CPU / 256 MB | -50% | ~$10 |
| WebSocket | 512 CPU / 1024 MB | 256 CPU / 512 MB | -50% | ~$20 |

**Task Definition (V2):**

```json
{
  "family": "oracy-django-api-v2",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/oracy-ecs-task-role",
  "containerDefinitions": [
    {
      "name": "django",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/oracy-django:v2",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DJANGO_SETTINGS_MODULE", "value": "config.settings.production"},
        {"name": "DATABASE_URL", "value": "${DATABASE_URL}"},
        {"name": "REDIS_URL", "value": "${REDIS_URL}"},
        {"name": "STT_PROVIDER", "value": "runpod"},
        {"name": "LLM_PROVIDER", "value": "openrouter"}
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:oracy/secret-key"
        },
        {
          "name": "RUNPOD_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:oracy/runpod-key"
        },
        {
          "name": "OPENROUTER_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:oracy/openrouter-key"
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

### Capacity Providers Strategy

Use Fargate Spot for non-critical workloads:

```json
{
  "capacityProviders": ["FARGATE", "FARGATE_SPOT"],
  "defaultCapacityProviderStrategy": [
    {
      "base": 1,
      "weight": 1,
      "capacityProvider": "FARGATE"
    },
    {
      "weight": 3,
      "capacityProvider": "FARGATE_SPOT"
    }
  ]
}
```

**Services using Fargate Spot:**
- Celery Workers (can tolerate interruption)
- Celery Beat (with redundancy)

**Services requiring Fargate (standard):**
- Django API (user-facing)
- WebSocket (needs persistence)

---

## Database Layer

### RDS PostgreSQL - Right-Sized

| Setting | V1 | V2 | Savings |
|---------|-----|-----|---------|
| Instance | db.t3.medium | db.t3.small | ~$50/month |
| Storage | 100GB GP3 | 50GB GP3 (auto-grow) | ~$10/month |
| IOPS | 3000 (provisioned) | 3000 (burst) | ~$50/month |
| Multi-AZ | Yes | No (MVP only) | ~$60/month |

**V2 Configuration:**

```python
# terraform/rds_v2.tf
resource "aws_db_instance" "oracy_v2" {
  identifier        = "oracy-postgres-v2"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.t3.small"  # Downgraded from medium
  allocated_storage = 50             # Reduced from 100
  storage_type      = "gp3"
  
  multi_az               = false     # Disable for MVP (re-enable for production)
  publicly_accessible    = false
  deletion_protection    = true
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  
  # Cost allocation tag
  tags = {
    CostCenter = "ai-pipeline"
    Environment = var.environment
  }
}
```

**Note:** Re-enable Multi-AZ when moving to production with real users.

### ElastiCache Redis - Smaller Instance

| Setting | V1 | V2 | Savings |
|---------|-----|-----|---------|
| Node Type | cache.t3.micro | cache.t3.micro | Same |
| Cluster Mode | Disabled | Disabled | Same |

**No change required** - already using smallest instance.

---

## Storage Layer

### S3 Buckets - Lifecycle Optimizations

Enhanced lifecycle policies to reduce storage costs:

```json
{
  "Rules": [
    {
      "ID": "uploads-cleanup",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "uploads/"
      },
      "Expiration": {
        "Days": 3
      },
      "Transitions": [
        {
          "Days": 1,
          "StorageClass": "INTELLIGENT_TIERING"
        }
      ]
    },
    {
      "ID": "recordings-archive",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "recordings/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "INTELLIGENT_TIERING"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER_IR"
        }
      ]
    },
    {
      "ID": "exports-cleanup",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "exports/"
      },
      "Expiration": {
        "Days": 90
      }
    }
  ]
}
```

### Intelligent-Tiering

Enable S3 Intelligent-Tiering for automatic cost optimization:

```python
# Enable on media bucket
import boto3

s3 = boto3.client('s3')

s3.put_bucket_intelligent_tiering_configuration(
    Bucket='oracy-prod-media',
    Id='MediaOptimization',
    IntelligentTieringConfiguration={
        'Status': 'Enabled',
        'Tierings': [
            {
                'Days': 30,
                'AccessTier': 'ARCHIVE_ACCESS'
            }
        ]
    }
)
```

---

## AI/ML Infrastructure

### Removed Services

| Service | V1 Usage | V2 Replacement |
|---------|----------|----------------|
| AWS Transcribe | Fallback STT | Removed - use WhisperX self-hosted |
| Amazon SageMaker | Future training | Deferred to Phase 2 |

### New External Services

#### RunPod Integration with WhisperX

**Purpose:** Serverless GPU for WhisperX transcription with distil-large-v3

**Configuration:**
- Endpoint: Serverless GPU
- GPU: RTX 3090 (24GB) or RTX A4000 (16GB)
- Model: distil-large-v3 with int8 quantization (~2.8GB VRAM)
- Batch Size: 4-8 files simultaneously
- Min/Max Workers: 0/3 (scale to zero)
- Flashboot: Enabled (reduces cold start to ~2s)
- Container: Custom WhisperX image

```python
# RunPod endpoint configuration for WhisperX
{
  "name": "oracy-whisperx-v2",
  "gpu": "RTX 3090",
  "gpuCount": 1,
  "workers": {
    "min": 0,
    "max": 3
  },
  "flashboot": True,  # Reduces cold start to ~2 seconds
  "env": {
    "WHISPER_MODEL": "distil-large-v3",
    "COMPUTE_TYPE": "int8",  # 40% VRAM reduction
    "BATCH_SIZE": "4",
    "LANGUAGE": "en"
  }
}
```

**Cost:** ~$0.0003/minute of audio (vs $0.006 OpenAI / $0.024 AWS)
**Throughput:** 4-8 files simultaneously per worker (batch processing)

#### Vast.ai (Optional Backup)

**Purpose:** Dedicated GPU instances for high-volume periods with WhisperX batch processing

**Configuration:**
- Instance: RTX 3090 (24GB VRAM)
- Cost: ~$0.30/hour
- Can process: 8-16 files simultaneously (batch_size=16 with int8)
- Use when RunPod queue depth > 10 or for predictable high-volume periods

```python
# Celery task routing with WhisperX batching
from celery import Task

class RouteBasedOnLoad(Task):
    def apply_async(self, args=None, kwargs=None, **options):
        # Check RunPod queue depth
        queue_depth = get_runpod_queue_depth()
        
        if queue_depth > 10:
            # Route to Vast.ai for batch processing
            options['queue'] = 'vast_ai_transcription'
            # Vast.ai can handle larger batches
            kwargs['batch_size'] = 16  # vs 4 on RunPod
        else:
            options['queue'] = 'runpod_transcription'
            kwargs['batch_size'] = 4
        
        return super().apply_async(args, kwargs, **options)
```

**WhisperX on Vast.ai Setup:**
```yaml
# docker-compose.whisperx-vast.yml
version: '3.8'

services:
  whisperx-api:
    image: oracy/whisperx-gpu:latest
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - WHISPER_MODEL=distil-large-v3
      - COMPUTE_TYPE=int8
      - BATCH_SIZE=16  # Higher for dedicated GPU
      - LANGUAGE=en
    ports:
      - "8000:8000"
    volumes:
      - model-cache:/root/.cache/whisperx
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  model-cache:
```

---

## Cost Monitoring

### AWS Cost Anomaly Detection

```python
# terraform/cost_anomaly.tf
resource "aws_ce_anomaly_monitor" "oracy_daily" {
  name = "oracy-daily-spend"
  type = "DIMENSIONAL"
  
  monitor_specification = jsonencode({
    "Dimension" = "SERVICE"
  })
}

resource "aws_ce_anomaly_subscription" "oracy_alerts" {
  name = "oracy-cost-alerts"
  threshold = 150  # Alert if daily spend > $150
  frequency = "DAILY"
  
  monitor_arn_list = [aws_ce_anomaly_monitor.oracy_daily.arn]
  
  subscriber {
    type    = "EMAIL"
    address = "admin@oracy.ai"
  }
}
```

### Custom Cost Dashboard

```python
# monitoring/cost_tracker.py
import boto3
from datetime import datetime, timedelta

class CostTracker:
    """Track and report AI pipeline costs."""
    
    def __init__(self):
        self.ce = boto3.client('ce')
    
    def get_daily_costs(self):
        """Get yesterday's costs by service."""
        end = datetime.now().date()
        start = end - timedelta(days=1)
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start.isoformat(),
                'End': end.isoformat()
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        
        return response['ResultsByTime'][0]['Groups']
    
    def calculate_cost_per_assessment(self, num_assessments: int):
        """Calculate average cost per assessment."""
        total_cost = sum(
            float(g['Metrics']['BlendedCost']['Amount'])
            for g in self.get_daily_costs()
        )
        return total_cost / num_assessments if num_assessments > 0 else 0
```

### Budget Alerts

```python
# terraform/budget.tf
resource "aws_budgets_budget" "oracy_monthly" {
  name         = "oracy-monthly-budget"
  budget_type  = "COST"
  limit_amount = "1000"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  
  cost_filter {
    name = "TagKeyValue"
    values = [
      "user:Environment$production",
      "user:CostCenter$ai-pipeline"
    ]
  }
  
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["admin@oracy.ai"]
  }
  
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["admin@oracy.ai"]
  }
}
```

---

## Security Considerations

### External API Security

When using RunPod and OpenRouter, follow these practices:

```python
# config/secrets.py
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name: str) -> str:
    """Retrieve secret from AWS Secrets Manager."""
    client = boto3.client('secretsmanager')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        logger.error(f"Failed to retrieve secret: {e}")
        raise

# Usage
RUNPOD_API_KEY = get_secret("oracy/runpod-key")
OPENROUTER_API_KEY = get_secret("oracy/openrouter-key")
```

### Network Security

```python
# Security group for external API access
resource "aws_security_group_rule" "egress_external_apis" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = [
    "0.0.0.0/0"  # Required for RunPod, OpenRouter APIs
  ]
  security_group_id = aws_security_group.ecs_service.id
  description       = "HTTPS to external AI services"
}
```

---

## Migration Steps

### Phase 1: Infrastructure Preparation (Day 1)

1. Update ECS task definitions with new environment variables
2. Add RunPod and OpenRouter secrets to Secrets Manager
3. Deploy updated task definitions
4. Verify connectivity to external services

### Phase 2: Service Migration (Day 2-3)

1. Deploy new STT service (RunPod integration)
2. Deploy new LLM service (OpenRouter integration)
3. Run parallel processing for validation
4. Compare outputs between V1 and V2

### Phase 3: Optimization (Week 1)

1. Enable Fargate Spot for Celery workers
2. Apply S3 lifecycle policies
3. Set up cost monitoring and alerts
4. Tune auto-scaling policies

### Phase 4: Cleanup (Week 2)

1. Remove OpenAI API keys
2. Disable AWS Transcribe access
3. Archive old logs and exports
4. Document final cost savings

---

## Disaster Recovery

### Backup Strategy

| Component | Backup Method | Frequency | Retention |
|-----------|--------------|-----------|-----------|
| RDS | Automated snapshots | Daily | 7 days |
| RDS | Manual snapshots | Weekly | 30 days |
| S3 | Versioning + Cross-region | Continuous | 30 days |

### RunPod Fallback

If RunPod is unavailable:

```python
# stt/fallback_chain.py
async def transcribe_with_fallback(audio_path: str) -> Transcript:
    """Try WhisperX transcription services in priority order."""
    
    services = [
        RunPodWhisperXService(model="distil-large-v3"),  # Primary - fastest
        VastAIWhisperXService(model="distil-large-v3"),  # Secondary - dedicated GPU
        RunPodWhisperXService(model="base"),             # Tertiary - smaller model
        CPUWhisperXService(model="base"),                # Fallback - CPU only
    ]
    
    for service in services:
        try:
            return await service.transcribe(
                audio_path,
                batch_size=4 if 'CPU' not in service.__class__.__name__ else 1
            )
        except Exception as e:
            logger.warning(f"{service.__class__.__name__} failed: {e}")
            continue
    
    raise TranscriptionError("All STT services failed")
```

---

## Appendix: Terraform Configuration

### Variables

```hcl
# terraform/variables_v2.tf
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "enable_cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = true
}

variable "fargate_spot_weight" {
  description = "Weight for Fargate Spot in capacity provider strategy"
  type        = number
  default     = 3
}

variable "runpod_endpoint_id" {
  description = "RunPod serverless endpoint ID"
  type        = string
  sensitive   = true
}
```

### Cost-Optimized Module

```hcl
# terraform/modules/cost_optimized/main.tf
module "ecs_v2" {
  source = "./modules/ecs"
  
  # Use smaller task sizes
  task_cpu = {
    api     = 256
    worker  = 512
    beat    = 128
    ws      = 256
  }
  
  task_memory = {
    api     = 512
    worker  = 1024
    beat    = 256
    ws      = 512
  }
  
  # Enable Fargate Spot
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  spot_weight        = var.fargate_spot_weight
}

module "rds_v2" {
  source = "./modules/rds"
  
  instance_class    = "db.t3.small"
  allocated_storage = 50
  multi_az          = false
}
```
