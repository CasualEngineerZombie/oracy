# Deployment Strategy

## Overview

This document outlines the CI/CD pipeline, environment management, and deployment procedures for Oracy AI.

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main, staging]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: oracy_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: |
          cd server
          uv pip install -e ".[dev]"

      - name: Run linting
        run: |
          cd server
          black --check .
          isort --check-only .
          flake8 .
          mypy .

      - name: Run security checks
        run: |
          cd server
          bandit -r apps/ -f json -o bandit-report.json || true
          safety check

      - name: Run tests
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/oracy_test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
        run: |
          cd server
          pytest --cov=apps --cov-report=xml --cov-report=html

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./server/coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: client/package-lock.json

      - name: Install dependencies
        run: |
          cd client
          npm ci

      - name: Run linting
        run: |
          cd client
          npm run lint

      - name: Run type check
        run: |
          cd client
          npm run type-check

      - name: Run unit tests
        run: |
          cd client
          npm run test:unit -- --coverage

      - name: Build
        run: |
          cd client
          npm run build
```

### Deployment Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main, staging]

env:
  AWS_REGION: ap-southeast-1
  ECR_REPOSITORY: oracy
  ECS_CLUSTER: oracy

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubActionsDeployRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push backend image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY-django:$IMAGE_TAG ./server
          docker push $ECR_REGISTRY/$ECR_REPOSITORY-django:$IMAGE_TAG

      - name: Build, tag, and push frontend image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY-react:$IMAGE_TAG ./client
          docker push $ECR_REGISTRY/$ECR_REPOSITORY-react:$IMAGE_TAG

  deploy-backend:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubActionsDeployRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service django-api \
            --force-new-deployment

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster $ECS_CLUSTER \
            --services django-api

  deploy-frontend:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubActionsDeployRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Deploy to S3
        run: |
          aws s3 sync ./client/dist s3://oracy-frontend-${{ github.ref_name }} \
            --delete \
            --cache-control "max-age=31536000,immutable"

      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"
```

---

## Environment Management

### Environment Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION                               │
│  • oracy.ai                                                     │
│  • AWS Account: oracy-prod                                      │
│  • RDS: db.r6g.xlarge (Multi-AZ)                                │
│  • ECS: 4-10 tasks                                              │
│  • S3: oracy-prod-media                                         │
│  • Backup: 7 days                                               │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Promote after QA
┌─────────────────────────────────────────────────────────────────┐
│                        STAGING                                  │
│  • staging.oracy.ai                                             │
│  • AWS Account: oracy-staging                                   │
│  • RDS: db.t3.medium (Single AZ)                                │
│  • ECS: 2 tasks                                                 │
│  • S3: oracy-staging-media                                      │
│  • Data: Anonymized production snapshot                         │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Auto-deploy on merge
┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPMENT                                 │
│  • localhost / Docker Compose                                   │
│  • Local PostgreSQL + Redis                                     │
│  • Mock external services (optional)                            │
└─────────────────────────────────────────────────────────────────┘
```

### Environment Variables per Environment

```bash
# .env.production
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
SECRET_KEY=<prod-secret>
DATABASE_URL=postgres://user:pass@prod-rds:5432/oracy
REDIS_URL=redis://prod-redis:6379/0
AWS_STORAGE_BUCKET_NAME=oracy-prod-media
OPENAI_API_KEY=<prod-key>
SENTRY_DSN=<prod-sentry>
```

```bash
# .env.staging
DJANGO_SETTINGS_MODULE=config.settings.staging
DEBUG=False
SECRET_KEY=<staging-secret>
DATABASE_URL=postgres://user:pass@staging-rds:5432/oracy
REDIS_URL=redis://staging-redis:6379/0
AWS_STORAGE_BUCKET_NAME=oracy-staging-media
OPENAI_API_KEY=<staging-key>
SENTRY_DSN=<staging-sentry>
```

---

## Blue/Green Deployment

### ECS Blue/Green with CodeDeploy

```hcl
# Terraform: ECS Blue/Green deployment
resource "aws_codedeploy_app" "oracy" {
  name             = "oracy-django"
  compute_platform = "ECS"
}

resource "aws_codedeploy_deployment_group" "oracy" {
  app_name               = aws_codedeploy_app.oracy.name
  deployment_group_name  = "oracy-django-dg"
  service_role_arn       = aws_iam_role.codedeploy.arn
  deployment_config_name = "CodeDeployDefault.ECSAllAtOnce"

  blue_green_deployment_config {
    deployment_ready_option {
      action_on_timeout = "CONTINUE_DEPLOYMENT"
    }

    terminate_blue_instances_on_deployment_success {
      action                           = "TERMINATE"
      termination_wait_time_in_minutes = 30
    }
  }

  ecs_service {
    cluster_name = aws_ecs_cluster.oracy.name
    service_name = aws_ecs_service.django.name
  }

  deployment_style {
    deployment_option = "WITH_TRAFFIC_CONTROL"
    deployment_type   = "BLUE_GREEN"
  }
}
```

### Deployment Process

1. **Build** - Create Docker images with commit SHA tag
2. **Push** - Upload to ECR
3. **Register** - Register new task definition
4. **Deploy** - CodeDeploy creates green environment
5. **Health Check** - Verify green environment health
6. **Traffic Shift** - Gradually shift traffic (10% → 50% → 100%)
7. **Monitor** - Watch error rates for 30 minutes
8. **Cleanup** - Terminate blue environment on success

### Rollback Procedure

```bash
# Manual rollback to previous version
aws ecs update-service \
  --cluster oracy \
  --service django-api \
  --task-definition oracy-django:PREVIOUS_REVISION \
  --force-new-deployment

# Or via CodeDeploy
aws deploy rollback-deployment \
  --deployment-id d-ABCD1234
```

---

## Database Migrations

### Zero-Downtime Migration Strategy

```python
# Migration safety rules
"""
1. Add new columns as nullable (or with defaults)
2. Create indexes CONCURRENTLY
3. Backfill data in batches
4. Make column non-nullable in separate migration
5. Remove old columns in later release
"""

# Example safe migration
class Migration(migrations.Migration):
    atomic = False  # Allow concurrent index creation
    
    operations = [
        # Step 1: Add new column as nullable
        migrations.AddField(
            model_name='assessment',
            name='new_field',
            field=models.CharField(max_length=100, null=True),
        ),
        
        # Step 2: Create index concurrently
        migrations.RunSQL(
            sql='CREATE INDEX CONCURRENTLY idx_assessments_new ON assessments(new_field);',
            reverse_sql='DROP INDEX idx_assessments_new;'
        ),
    ]
```

### Migration Deployment Process

```bash
# 1. Run migrations BEFORE deploying new code
# (ensure backward compatibility)

python manage.py migrate --database=production

# 2. Deploy new code

# 3. Verify migrations applied
python manage.py showmigrations

# 4. If rollback needed, rollback code first, then migrations
python manage.py migrate app_name PREVIOUS_MIGRATION
```

---

## Monitoring & Alerting

### CloudWatch Dashboards

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", "ServiceName", "django-api", "ClusterName", "oracy"],
          ["...", "celery-worker", ".", "."]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-southeast-1",
        "title": "ECS CPU Utilization"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "oracy-postgres"],
          ["...", "DatabaseConnections", ".", "."]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-southeast-1",
        "title": "RDS Metrics"
      }
    }
  ]
}
```

### Alerting Rules

```yaml
# CloudWatch Alarms
HighCPUAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: "Oracy-HighCPU"
    MetricName: CPUUtilization
    Namespace: AWS/ECS
    Statistic: Average
    Period: 300
    EvaluationPeriods: 2
    Threshold: 80
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - arn:aws:sns:ap-southeast-1:ACCOUNT:oracy-alerts

HighErrorRateAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: "Oracy-HighErrorRate"
    MetricName: 5xxErrorRate
    Namespace: AWS/ApplicationELB
    Statistic: Average
    Period: 60
    EvaluationPeriods: 2
    Threshold: 1
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - arn:aws:sns:ap-southeast-1:ACCOUNT:oracy-alerts

DatabaseConnectionsAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: "Oracy-HighDBConnections"
    MetricName: DatabaseConnections
    Namespace: AWS/RDS
    Statistic: Average
    Period: 300
    EvaluationPeriods: 2
    Threshold: 150
    ComparisonOperator: GreaterThanThreshold
```

### Error Tracking (Sentry)

```python
# config/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    environment="production",
    release=os.getenv('GIT_COMMIT_SHA'),
)
```

---

## Disaster Recovery

### Backup Strategy

| Component | Backup Method | Frequency | Retention |
|-----------|--------------|-----------|-----------|
| RDS | Automated snapshots + manual | Daily | 7 days |
| RDS | Cross-region snapshot | Weekly | 30 days |
| S3 | Versioning + Cross-region replication | Continuous | Versioned |
| Application config | Terraform state + Secrets Manager | On change | Versioned |

### Recovery Procedures

#### RDS Point-in-Time Recovery

```bash
# Restore to specific point in time
aws rds restore-db-instance-to-point-in-time \
  --source-db-instanceIdentifier oracy-postgres \
  --target-db-instance-identifier oracy-postgres-recovery \
  --restore-time 2026-03-01T12:00:00Z
```

#### Cross-Region Failover

```bash
# Promote read replica in secondary region
aws rds promote-read-replica \
  --db-instance-identifier oracy-postgres-replica

# Update application to use new endpoint
# (via environment variable or parameter store)
```

### RTO/RPO Targets

| Scenario | RTO (Recovery Time) | RPO (Data Loss) |
|----------|-------------------|-----------------|
| Single AZ failure | 5 minutes (Multi-AZ) | 0 |
| Database corruption | 30 minutes | 5 minutes (PITR) |
| Region failure | 2 hours | 1 hour (async replication) |
| Complete loss | 4 hours | 1 hour |

---

## Local Development

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: oracy
      POSTGRES_USER: oracy
      POSTGRES_PASSWORD: oracy
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./server
      dockerfile: Dockerfile.dev
    environment:
      DATABASE_URL: postgres://oracy:oracy@db:5432/oracy
      REDIS_URL: redis://redis:6379/0
      DEBUG: "true"
    volumes:
      - ./server:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  frontend:
    build:
      context: ./client
      dockerfile: Dockerfile.dev
    environment:
      VITE_API_URL: http://localhost:8000/api
    volumes:
      - ./client:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    depends_on:
      - backend

  celery:
    build:
      context: ./server
      dockerfile: Dockerfile.dev
    command: celery -A config worker -l info
    environment:
      DATABASE_URL: postgres://oracy:oracy@db:5432/oracy
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./server:/app
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### Local Development Commands

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm run test

# View logs
docker-compose logs -f backend
docker-compose logs -f celery

# Reset database
docker-compose down -v
docker-compose up -d db
```

---

## Release Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Security scan clean (bandit, safety, npm audit)
- [ ] Database migrations reviewed
- [ ] Feature flags configured
- [ ] Monitoring dashboards verified
- [ ] Rollback plan documented

### Deployment
- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Notify team of production deployment
- [ ] Deploy to production (blue/green)
- [ ] Verify health checks pass
- [ ] Monitor error rates for 30 minutes

### Post-Deployment
- [ ] Verify critical user journeys
- [ ] Check Sentry for new errors
- [ ] Monitor CloudWatch metrics
- [ ] Update runbooks/documentation
- [ ] Announce deployment complete

### Rollback Criteria
- Error rate > 1% for 5 minutes
- Any 500 errors on critical paths
- Performance degradation > 50%
- Data integrity issues
- Security incident

---

## Secrets Management

### AWS Secrets Manager Structure

```
oracy/
├── production/
│   ├── django-secret-key
│   ├── database-credentials
│   ├── openai-api-key
│   └── jwt-signing-key
├── staging/
│   ├── django-secret-key
│   ├── database-credentials
│   ├── openai-api-key
│   └── jwt-signing-key
└── development/
    └── (local .env files)
```

### Secret Rotation Schedule

| Secret | Rotation Frequency | Process |
|--------|-------------------|---------|
| Database password | 90 days | Update RDS, restart services |
| API keys | 180 days | Generate new, update secrets, restart |
| JWT signing key | On demand | Invalidate all sessions |
| Django secret | On demand | Session flush required |

---

## Cost Monitoring

### AWS Cost Alarms

```yaml
BudgetAlarm:
  Type: AWS::Budgets::Budget
  Properties:
    Budget:
      BudgetName: "Oracy-Monthly-Budget"
      BudgetLimit:
        Amount: 2000
        Unit: USD
      TimeUnit: MONTHLY
      BudgetType: COST
    NotificationsWithSubscribers:
      - Notification:
          NotificationType: ACTUAL
          ComparisonOperator: GREATER_THAN
          Threshold: 80
        Subscribers:
          - SubscriptionType: SNS
            Address: arn:aws:sns:ap-southeast-1:ACCOUNT:oracy-alerts
```

### Cost Optimization Measures
- Use Spot instances for Celery workers (dev/staging)
- S3 Intelligent Tiering for old videos
- RDS Reserved Instances for production
- CloudFront caching to reduce origin requests
- Lambda for lightweight processing (optional)
