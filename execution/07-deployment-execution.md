# Deployment Execution

Step-by-step guide for deploying Oracy AI to staging and production environments.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Staging Deployment](#staging-deployment)
4. [Production Deployment](#production-deployment)
5. [Rollback Procedures](#rollback-procedures)
6. [Post-Deployment Verification](#post-deployment-verification)

---

## Deployment Overview

### Deployment Architecture

```
GitHub → GitHub Actions → AWS ECR → AWS ECS → ALB → Application
                  ↓
            Terraform → AWS Infrastructure
```

### Environments

| Environment | Branch | URL | Purpose |
|-------------|--------|-----|---------|
| Local | any | localhost | Development |
| Staging | staging | staging.oracy.ai | Pre-production testing |
| Production | main | app.oracy.ai | Live system |

### Deployment Frequency

- **Staging**: On every push to `staging` branch
- **Production**: Manual trigger after staging validation

---

## Pre-Deployment Checklist

### Code Quality

```bash
# 1. Run all tests locally
cd server && pytest
cd client && npm run test

# 2. Check code formatting
cd server && black --check .
cd server && isort --check-only .
cd client && npm run lint

# 3. Type checking
cd server && mypy .
cd client && npm run type-check

# 4. Security scan
cd server && bandit -r apps/
cd server && safety check
```

### Version Verification

```bash
# Verify version bump (if applicable)
git tag -l "v*" | sort -V | tail -5

# Update version files
# server/config/__init__.py
# client/package.json
```

### Database Preparation

```bash
# Generate migration check
cd server
python manage.py makemigrations --check --dry-run
# Should output "No changes detected"

# Backup production database (before deployment)
aws rds create-db-snapshot \
  --db-instance-identifier oracy-production \
  --db-snapshot-identifier pre-deploy-$(date +%Y%m%d-%H%M%S)
```

### Communication

- [ ] Notify team of planned deployment
- [ ] Check monitoring dashboards
- [ ] Prepare rollback plan
- [ ] Schedule maintenance window (if applicable)

---

## Staging Deployment

### Automatic Deployment (via GitHub Actions)

```bash
# 1. Merge changes to staging branch
git checkout staging
git merge feature/your-feature
git push origin staging

# 2. GitHub Actions automatically:
#    - Runs tests
#    - Builds Docker images
#    - Pushes to ECR
#    - Deploys to ECS staging cluster

# 3. Monitor deployment
# Visit: https://github.com/oracy/oracy/actions
```

### Manual Deployment (if needed)

```bash
# 1. Build and push images
export AWS_REGION=ap-southeast-1
export ECR_REPOSITORY=oracy

# Login to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REPOSITORY

# Build backend
cd server
docker build -t $ECR_REPOSITORY:backend-staging .
docker tag $ECR_REPOSITORY:backend-staging $ECR_REPOSITORY:backend-staging-$(git rev-parse --short HEAD)
docker push $ECR_REPOSITORY:backend-staging

# Build frontend
cd ../client
docker build -t $ECR_REPOSITORY:frontend-staging .
docker tag $ECR_REPOSITORY:frontend-staging $ECR_REPOSITORY:frontend-staging-$(git rev-parse --short HEAD)
docker push $ECR_REPOSITORY:frontend-staging

# 2. Update ECS service
aws ecs update-service \
  --cluster oracy-staging \
  --service backend \
  --force-new-deployment

aws ecs update-service \
  --cluster oracy-staging \
  --service frontend \
  --force-new-deployment
```

### Verify Staging Deployment

```bash
# Check service status
aws ecs describe-services \
  --cluster oracy-staging \
  --services backend frontend

# Verify health endpoint
curl https://staging.oracy.ai/health

# Run smoke tests
cd tests
cd e2e && npm run test:staging
```

---

## Production Deployment

### Step 1: Create Release Branch

```bash
# Create release branch from main
git checkout main
git pull origin main
git checkout -b release/v1.2.0

# Cherry-pick or merge features
git merge staging

# Update version
# Edit: server/config/__init__.py -> __version__ = '1.2.0'
# Edit: client/package.json -> "version": "1.2.0"

git add .
git commit -m "Bump version to 1.2.0"
git push origin release/v1.2.0
```

### Step 2: Create Pull Request

```bash
# Create PR from release/v1.2.0 to main
gh pr create \
  --title "Release v1.2.0" \
  --body "$(cat RELEASE_NOTES.md)" \
  --base main \
  --head release/v1.2.0
```

### Step 3: Deploy to Production

#### Option A: GitHub Actions (Recommended)

```bash
# After PR is merged to main, trigger production deployment:
gh workflow run deploy-production.yml \
  --ref main \
  -f version=1.2.0

# Monitor deployment
gh run watch
```

#### Option B: Manual Deployment

```bash
# 1. Set production context
export AWS_PROFILE=oracy-production
export AWS_REGION=ap-southeast-1

# 2. Database backup (CRITICAL)
aws rds create-db-snapshot \
  --db-instance-identifier oracy-production \
  --db-snapshot-identifier pre-deploy-$(date +%Y%m%d-%H%M%S)

# 3. Run migrations (can be done before or during deployment)
aws ecs run-task \
  --cluster oracy-production \
  --task-definition oracy-migrate \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"

# 4. Deploy backend (Blue/Green)
aws ecs update-service \
  --cluster oracy-production \
  --service backend \
  --task-definition oracy-backend:NEW_REVISION \
  --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true}"

# 5. Deploy frontend
aws ecs update-service \
  --cluster oracy-production \
  --service frontend \
  --force-new-deployment

# 6. Deploy Celery workers
aws ecs update-service \
  --cluster oracy-production \
  --service celery-worker \
  --force-new-deployment
```

### Step 4: Monitor Deployment

```bash
# Watch service events
aws ecs describe-services \
  --cluster oracy-production \
  --services backend frontend celery-worker

# Check CloudWatch logs
aws logs tail /ecs/oracy-production/backend --follow

# Monitor ALB target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...:targetgroup/oracy-backend/...
```

---

## Rollback Procedures

### Automatic Rollback (ECS Circuit Breaker)

ECS automatically rolls back if health checks fail:

```bash
# Check if rollback occurred
aws ecs describe-services \
  --cluster oracy-production \
  --services backend

# Look for: "rolloutState": "ROLLED_BACK"
```

### Manual Rollback

```bash
# 1. Get previous task definition
aws ecs describe-task-definition \
  --task-definition oracy-backend \
  --include TAGS

# 2. Update service to previous revision
aws ecs update-service \
  --cluster oracy-production \
  --service backend \
  --task-definition oracy-backend:PREVIOUS_REVISION \
  --force-new-deployment

# 3. Verify rollback
curl https://app.oracy.ai/health
```

### Database Rollback (Emergency)

```bash
# Only if migration caused issues

# 1. Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier oracy-production-rollback \
  --db-snapshot-identifier pre-deploy-YYYYMMDD-HHMMSS \
  --db-instance-class db.t3.medium

# 2. Update application to point to restored DB
# 3. Verify functionality
# 4. Rename instances after verification
```

---

## Post-Deployment Verification

### Health Checks

```bash
# 1. Basic health check
curl -f https://app.oracy.ai/health || echo "Health check failed"

# 2. API health check
curl -f https://app.oracy.ai/api/health/detailed

# 3. Check all endpoints
endpoints=(
  "/api/auth/token/"
  "/api/users/me/"
  "/api/assessments/"
  "/api/students/"
)

for endpoint in "${endpoints[@]}"; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "https://app.oracy.ai$endpoint")
  echo "$endpoint: $status"
done
```

### Smoke Tests

```bash
# Run production smoke tests
cd tests/e2e
BASE_URL=https://app.oracy.ai npm run test:smoke

# Or with Playwright
npx playwright test --project=production
```

### Monitoring Verification

```bash
# Check CloudWatch alarms
aws cloudwatch describe-alarms \
  --state-value ALARM

# Check for errors in logs (last 5 minutes)
aws logs filter-log-events \
  --log-group-name /ecs/oracy-production/backend \
  --start-time $(date -d '5 minutes ago' +%s)000 \
  --filter-pattern "ERROR"
```

### Performance Verification

```bash
# Quick load test
locust -f locustfile.py \
  --host=https://app.oracy.ai \
  --users=10 \
  --spawn-rate=2 \
  --run-time=1m \
  --headless
```

### Post-Deployment Checklist

- [ ] Application responds to health checks
- [ ] Login/logout works correctly
- [ ] Key user flows functional
- [ ] AI pipeline processing new assessments
- [ ] No critical errors in logs
- [ ] Performance metrics acceptable
- [ ] Monitoring alerts functioning
- [ ] Notify team of successful deployment

---

## Infrastructure Deployment (Terraform)

### Deploy Infrastructure Changes

```bash
cd infrastructure/terraform

# Initialize
terraform init

# Plan changes
terraform plan -var-file="production.tfvars" -out=tfplan

# Review plan

# Apply
terraform apply tfplan
```

### Environment-Specific Variables

```hcl
# production.tfvars
environment = "production"
region = "ap-southeast-1"

database_instance_class = "db.r5.xlarge"
database_allocated_storage = 100

ecs_task_cpu = 2048
ecs_task_memory = 4096

desired_count_backend = 3
desired_count_frontend = 2
desired_count_celery = 2

enable_waf = true
enable_cdn = true
```

---

## Deployment Notifications

### Slack Notification (GitHub Actions)

```yaml
- name: Notify Slack
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Deployment ${{ job.status }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Oracy AI Deployment*\nEnvironment: ${{ inputs.environment }}\nVersion: ${{ inputs.version }}\nStatus: ${{ job.status }}"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## Emergency Procedures

### Immediate Rollback

If critical issue detected:

```bash
# 1. Enable maintenance mode (if applicable)
# Set env var: MAINTENANCE_MODE=true

# 2. Rollback immediately
aws ecs update-service \
  --cluster oracy-production \
  --service backend \
  --task-definition oracy-backend:STABLE_REVISION

# 3. Notify team
# 4. Investigate issue
# 5. Fix and redeploy
```

### Contact Information

| Role | Contact | Use For |
|------|---------|---------|
| Tech Lead | Slack: @tech-lead | Deployment issues |
| DevOps | Slack: @devops | Infrastructure problems |
| On-Call | PagerDuty | Production outages |