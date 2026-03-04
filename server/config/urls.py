"""
URL configuration for Oracy AI Server.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
    # API v1
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/students/", include("apps.students.urls")),
    path("api/v1/assessments/", include("apps.assessments.urls")),
    path("api/v1/analysis/", include("apps.analysis.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/benchmarks/", include("apps.benchmarks.urls")),
    
    # Prometheus metrics
    path("", include("django_prometheus.urls")),
]
