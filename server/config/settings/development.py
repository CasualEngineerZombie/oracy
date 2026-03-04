"""
Development settings for Oracy AI Server.
"""

from .base import *

# =============================================================================
# DEBUG SETTINGS
# =============================================================================

DEBUG = True

# =============================================================================
# ALLOWED HOSTS
# =============================================================================

ALLOWED_HOSTS = ["*"]

# =============================================================================
# EMAIL
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# DEBUG TOOLBAR
# =============================================================================

INSTALLED_APPS += ["debug_toolbar"]

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = "DEBUG"
LOG_FORMAT = "simple"

LOGGING["formatters"]["simple"]["format"] = "{levelname} {asctime} {message}"
LOGGING["handlers"]["console"]["formatter"] = "simple"
LOGGING["root"]["level"] = LOG_LEVEL

# Enable SQL query logging in development
LOGGING["loggers"]["django.db.backends"]["level"] = "DEBUG"

# =============================================================================
# CORS
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# MEDIA FILES (Local storage in development)
# =============================================================================

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# =============================================================================
# CELERY (Run tasks synchronously in development for easier debugging)
# =============================================================================

CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").lower() in ("true", "1", "yes")
CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# SENTRY (Disable in development)
# =============================================================================

SENTRY_DSN = ""
