# Security & Compliance

## Overview

Oracy AI handles sensitive educational data including video recordings of minors. This document outlines the security architecture and compliance measures.

---

## Authentication & Authorization

### JWT-Based Authentication

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### Password Security

```python
# Use Argon2 for password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'apps.users.validators.CustomPasswordValidator',
    },
]
```

### Role-Based Access Control (RBAC)

```python
# apps/users/permissions.py
from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin'

class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'teacher'

class IsOwnerOrAdmin(permissions.BasePermission):
    """Allow if user is admin or owns the resource."""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.user == request.user

class CanAccessStudent(permissions.BasePermission):
    """Teachers can only access students in their cohorts."""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        # Check if student is in any of teacher's cohorts
        return obj.enrollments.filter(
            cohort__teacher=request.user
        ).exists()
```

### Object-Level Permissions

```python
# apps/assessments/views.py
from django.shortcuts import get_object_or_404

class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    
    def get_queryset(self):
        """Teachers only see assessments from their cohorts."""
        user = self.request.user
        
        if user.role == 'admin':
            return Assessment.objects.all()
        
        if user.role == 'teacher':
            return Assessment.objects.filter(
                cohort__teacher=user
            )
        
        # Students only see their own
        return Assessment.objects.filter(
            student__user=user
        )
    
    def perform_create(self, serializer):
        """Ensure teacher owns the cohort they're creating for."""
        cohort = serializer.validated_data['cohort']
        
        if self.request.user.role == 'teacher' and cohort.teacher != self.request.user:
            raise PermissionDenied("You don't have access to this cohort.")
        
        serializer.save()
```

---

## Video Storage Security

### S3 Security Configuration

```python
# config/settings/production.py

# Private bucket - no public access
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_DEFAULT_ACL = 'private'
AWS_S3_FILE_OVERWRITE = False

# Server-side encryption
AWS_S3_ENCRYPTION = True
AWS_S3_KMS_KEY_ID = os.getenv('AWS_KMS_KEY_ID')  # Customer-managed key

# Presigned URL expiration (1 hour for viewing, 15 min for upload)
AWS_QUERYSTRING_EXPIRE = 3600
AWS_QUERYSTRING_AUTH = True
```

### Bucket Policy

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
      "Sid": "DenyIncorrectKMSKey",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::oracy-prod-media/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption-aws-kms-key-id": "arn:aws:kms:REGION:ACCOUNT:key/KEY-ID"
        }
      }
    },
    {
      "Sid": "AllowECSAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:role/oracy-ecs-task-role"
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::oracy-prod-media/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

### Presigned URL Implementation

```python
# apps/assessments/services/storage.py
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

class SecureVideoStorage:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME
    
    def generate_upload_url(
        self,
        assessment_id: str,
        filename: str,
        content_type: str,
        file_size: int,
        expiration: int = 900  # 15 minutes
    ) -> dict:
        """Generate presigned URL for direct browser upload."""
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        s3_key = f"uploads/{assessment_id}/{safe_filename}"
        
        # Size limit validation (500MB)
        if file_size > 500 * 1024 * 1024:
            raise ValueError("File too large (max 500MB)")
        
        try:
            url = self.s3.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': s3_key,
                    'ContentType': content_type,
                    'ServerSideEncryption': 'aws:kms',
                    'SSEKMSKeyId': settings.AWS_S3_KMS_KEY_ID,
                },
                ExpiresIn=expiration
            )
            
            return {
                'uploadUrl': url,
                's3Key': s3_key,
                'expiresIn': expiration
            }
        except ClientError as e:
            logger.error(f"Failed to generate upload URL: {e}")
            raise
    
    def generate_view_url(
        self,
        s3_key: str,
        expiration: int = 3600  # 1 hour
    ) -> str:
        """Generate time-limited viewing URL."""
        
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': s3_key,
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate view URL: {e}")
            raise
    
    def move_to_permanent(self, temp_s3_key: str, assessment_id: str) -> str:
        """Move from uploads/ to permanent recordings/ location."""
        
        # Parse date for organization
        from datetime import datetime
        now = datetime.utcnow()
        
        permanent_key = (
            f"recordings/{now.year}/{now.month:02d}/"
            f"{assessment_id}/video.mp4"
        )
        
        # Copy object
        self.s3.copy_object(
            CopySource={'Bucket': self.bucket, 'Key': temp_s3_key},
            Bucket=self.bucket,
            Key=permanent_key,
            ServerSideEncryption='aws:kms',
            SSEKMSKeyId=settings.AWS_S3_KMS_KEY_ID,
        )
        
        # Delete temporary
        self.s3.delete_object(Bucket=self.bucket, Key=temp_s3_key)
        
        return permanent_key
```

### Access Logging

```python
# Enable S3 access logging
AWS_S3_LOGGING = {
    'bucket': 'oracy-access-logs',
    'prefix': 's3-access/'
}

# Log all presigned URL generations
class VideoAccessLogger:
    def log_access(self, user_id: str, assessment_id: str, action: str):
        AuditLog.objects.create(
            user_id=user_id,
            assessment_id=assessment_id,
            action=f'video_{action}',
            timestamp=timezone.now(),
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT'),
        )
```

---

## Data Protection (GDPR)

### Data Classification

| Data Type | Classification | Encryption at Rest | Encryption in Transit |
|-----------|---------------|-------------------|----------------------|
| Video recordings | High (Special Category) | KMS (AES-256) | TLS 1.3 |
| Student PII | High | KMS (AES-256) | TLS 1.3 |
| Transcripts | Medium | KMS (AES-256) | TLS 1.3 |
| Assessment scores | Medium | RDS encryption | TLS 1.3 |
| Audit logs | High | S3-SSE | TLS 1.3 |

### Consent Management

```python
# apps/assessments/models.py

class Assessment(models.Model):
    # ... fields ...
    
    consent_obtained = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    consent_recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_consents'
    )
    
    # Consent can be withdrawn
    consent_withdrawn = models.BooleanField(default=False)
    consent_withdrawn_at = models.DateTimeField(null=True, blank=True)
    consent_withdrawn_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='withdrawn_consents'
    )
    
    def withdraw_consent(self, withdrawn_by: User):
        """Handle consent withdrawal - triggers data deletion."""
        self.consent_withdrawn = True
        self.consent_withdrawn_at = timezone.now()
        self.consent_withdrawn_by = withdrawn_by
        self.save()
        
        # Trigger deletion workflow
        from .tasks import delete_assessment_data
        delete_assessment_data.delay(self.id)
```

### Right to Erasure (GDPR Article 17)

```python
# apps/assessments/tasks.py

@app.task
def delete_assessment_data(assessment_id: str):
    """Complete deletion of assessment data (GDPR erasure)."""
    
    assessment = Assessment.objects.get(id=assessment_id)
    
    # 1. Delete video from S3
    if assessment.recording:
        storage = SecureVideoStorage()
        storage.s3.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=assessment.recording.s3_key
        )
        if assessment.recording.audio_s3_key:
            storage.s3.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=assessment.recording.audio_s3_key
            )
    
    # 2. Delete evidence clips
    for clip in assessment.evidence_clips.all():
        storage.s3.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=clip.s3_key
        )
    
    # 3. Soft delete database records (retain audit log)
    assessment.deleted_at = timezone.now()
    assessment.save()
    
    # 4. Anonymize student reference in reports
    SignedReport.objects.filter(assessment=assessment).update(
        anonymized=True,
        student_identifier_hash=hashlib.sha256(
            str(assessment.student_id).encode()
        ).hexdigest()[:16]
    )
```

### Data Export (GDPR Article 20 - Portability)

```python
# apps/reports/export.py

class GDPRDataExporter:
    """Export all data for a student (GDPR portability)."""
    
    def export_student_data(self, student_id: int) -> dict:
        student = Student.objects.get(id=student_id)
        
        return {
            'student_profile': {
                'student_id': student.student_id,
                'year_group': student.year_group,
                'age_band': student.age_band,
                'eal': student.eal,
                'first_language': student.first_language,
            },
            'assessments': [
                {
                    'id': str(a.id),
                    'mode': a.mode,
                    'prompt': a.prompt,
                    'created_at': a.created_at.isoformat(),
                    'transcript': a.transcript.full_text if hasattr(a, 'transcript') else None,
                    'scores': {
                        'physical': a.signed_report.physical_score if hasattr(a, 'signed_report') else None,
                        'linguistic': a.signed_report.linguistic_score if hasattr(a, 'signed_report') else None,
                        'cognitive': a.signed_report.cognitive_score if hasattr(a, 'signed_report') else None,
                        'social_emotional': a.signed_report.social_emotional_score if hasattr(a, 'signed_report') else None,
                    },
                    'feedback': a.signed_report.feedback if hasattr(a, 'signed_report') else None,
                }
                for a in Assessment.objects.filter(student=student)
            ],
            'export_generated_at': timezone.now().isoformat(),
        }
```

---

## Audit Logging

### Comprehensive Audit Trail

```python
# apps/audit/models.py

class AuditLog(models.Model):
    """Comprehensive audit log for all data changes."""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
        ('sign', 'Sign Report'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('video_access', 'Video Access'),
        ('consent_withdraw', 'Consent Withdrawn'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Who
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    user_email = models.EmailField()  # Snapshot in case user is deleted
    
    # What
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50)  # 'Assessment', 'Report', etc.
    resource_id = models.CharField(max_length=100)
    
    # Details
    field = models.CharField(max_length=100, blank=True)
    old_value = models.JSONField(null=True)
    new_value = models.JSONField(null=True)
    
    # Context
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action', 'timestamp']),
        ]
        ordering = ['-timestamp']


# Middleware for automatic logging
class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log specific actions
        if request.user.is_authenticated:
            self._log_request(request, response)
        
        return response
    
    def _log_request(self, request, response):
        # Log video access
        if 'recordings' in request.path and request.method == 'GET':
            AuditLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action='video_access',
                resource_type='Recording',
                resource_id=request.resolver_match.kwargs.get('id', 'unknown'),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
```

### Model Change Tracking

```python
# apps/core/models.py

from django_currentuser.middleware import get_current_user

class AuditedModel(models.Model):
    """Abstract base model with automatic audit logging."""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_updated'
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)
```

---

## Network Security

### TLS Configuration

```python
# Production settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

### AWS WAF Configuration

```hcl
# Terraform configuration for WAF
resource "aws_wafv2_web_acl" "main" {
  name        = "oracy-waf"
  description = "WAF rules for Oracy AI"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting
  rule {
    name     = "RateLimit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # SQL injection protection
  rule {
    name     = "SQLInjection"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLInjectionRule"
      sampled_requests_enabled   = true
    }
  }

  # Known bad actors
  rule {
    name     = "BadActors"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BadActorsRule"
      sampled_requests_enabled   = true
    }
  }
}
```

---

## Secrets Management

### AWS Secrets Manager

```python
# config/settings/production.py
import boto3
import json

def get_secret(secret_name):
    """Retrieve secret from AWS Secrets Manager."""
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Load secrets
secrets = get_secret('oracy/production')

SECRET_KEY = secrets['django_secret_key']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': secrets['db_name'],
        'USER': secrets['db_user'],
        'PASSWORD': secrets['db_password'],
        'HOST': secrets['db_host'],
        'PORT': secrets['db_port'],
    }
}
OPENAI_API_KEY = secrets['openai_api_key']
```

### Environment Variable Validation

```python
# config/settings/base.py
import environ

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, None),
    ALLOWED_HOSTS=(list, []),
)

# Required environment variables
REQUIRED_ENV = [
    'SECRET_KEY',
    'DATABASE_URL',
    'REDIS_URL',
    'AWS_STORAGE_BUCKET_NAME',
]

for var in REQUIRED_ENV:
    if not env(var):
        raise ImproperlyConfigured(f'{var} environment variable is required')
```

---

## Compliance Checklist

### GDPR Compliance

- [ ] **Lawful basis** - Consent obtained before recording
- [ ] **Right to be informed** - Privacy notice provided
- [ ] **Right of access** - Data export functionality
- [ ] **Right to rectification** - Edit capabilities for teachers
- [ ] **Right to erasure** - Complete deletion workflow
- [ ] **Right to restrict processing** - Pause processing capability
- [ ] **Right to data portability** - JSON/CSV export
- [ ] **Right to object** - Objection handling process
- [ ] **Data minimization** - Only collect necessary data
- [ ] **Purpose limitation** - Clear purpose defined
- [ ] **Storage limitation** - Retention policies enforced
- [ ] **Security** - Encryption and access controls
- [ ] **Accountability** - Audit logging
- [ ] **DPO** - Data Protection Officer appointed

### Children's Data (UK GDPR)

- [ ] Age verification for consent
- [ ] Parental consent for under-13s
- [ ] Clear privacy notices for children
- [ ] Enhanced security measures
- [ ] Regular data protection impact assessments (DPIA)

### Data Residency

- [ ] Primary region: EU (for EU schools)
- [ ] Backup region: Same jurisdiction
- [ ] Cross-border transfer safeguards

---

## Incident Response

### Security Incident Procedure

1. **Detection** - CloudWatch alarms, WAF logs, audit logs
2. **Assessment** - Severity classification
3. **Containment** - Isolate affected systems
4. **Investigation** - Root cause analysis
5. **Remediation** - Fix vulnerability
6. **Recovery** - Restore services
7. **Post-incident** - Lessons learned

### Data Breach Notification

- **Within 72 hours** - Notify ICO (if applicable)
- **Without undue delay** - Notify affected individuals
- **Documentation** - All breaches recorded

### Contact

- **Security team**: security@oracy.ai
- **DPO**: dpo@oracy.ai
- **Incident hotline**: +44 XXX XXX XXXX
