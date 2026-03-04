"""
Production settings for Oracy AI Server.
"""

from .base import *

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

DEBUG = False

# Ensure SECRET_KEY is set in production
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY must be set in production")

# =============================================================================
# ALLOWED HOSTS
# =============================================================================

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
    raise ValueError("DJANGO_ALLOWED_HOSTS must be set in production")

# =============================================================================
# HTTPS SETTINGS
# =============================================================================

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

# =============================================================================
# STATIC & MEDIA FILES (S3 in production)
# =============================================================================

# Use S3 for media storage
USE_S3 = True
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# CloudFront for static files (optional)
AWS_CLOUDFRONT_DOMAIN = os.getenv("AWS_CLOUDFRONT_DOMAIN", "")
if AWS_CLOUDFRONT_DOMAIN:
    STATIC_URL = f"https://{AWS_CLOUDFRONT_DOMAIN}/static/"
    MEDIA_URL = f"https://{AWS_CLOUDFRONT_DOMAIN}/media/"

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "json"

# Add file handler for production
LOGGING["handlers"]["file"] = {
    "class": "logging.handlers.RotatingFileHandler",
    "filename": "/var/log/oracy/django.log",
    "maxBytes": 10485760,  # 10MB
    "backupCount": 10,
    "formatter": "json",
}

LOGGING["root"]["handlers"] = ["console", "file"]

for logger in LOGGING["loggers"]:
    LOGGING["loggers"][logger]["handlers"] = ["console", "file"]

# =============================================================================
# CACHING (ElastiCache in production)
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    }
}

# =============================================================================
# RATE LIMITING
# =============================================================================

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
]

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "100/hour",
    "user": "1000/hour",
}

# =============================================================================
# CELERY
# =============================================================================

CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# =============================================================================
# EMAIL (SES in production)
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "email-smtp.ap-southeast-1.amazonaws.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@oracy.ai")

# =============================================================================
# ADMINS & MANAGERS
# =============================================================================

ADMINS = [
    ("Oracy Team", "admin@oracy.ai"),
]

MANAGERS = ADMINS

# =============================================================================
# SECURITY MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
] + MIDDLEWARE
