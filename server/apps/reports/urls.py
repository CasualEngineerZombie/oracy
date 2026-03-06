from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import CohortReportViewSet, DraftReportViewSet, ReportViewSet

app_name = "reports"

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'drafts', DraftReportViewSet, basename='draft-report')

urlpatterns = [
    path('', include(router.urls)),
    # Cohort reports
    path('cohorts/export/', CohortReportViewSet.as_view({'get': 'export_cohort_pdf'}), name='cohort-export'),
]
