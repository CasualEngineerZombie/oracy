from django.urls import path

from .views import AssessmentViewSet

app_name = "assessments"

urlpatterns = [
    path("", AssessmentViewSet.as_view({"get": "list", "post": "create"}), name="assessment-list"),
    path("<uuid:pk>/", AssessmentViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="assessment-detail"),
    path("<uuid:pk>/upload_recording/", AssessmentViewSet.as_view({"post": "upload_recording"}), name="assessment-upload"),
    path("<uuid:pk>/process/", AssessmentViewSet.as_view({"post": "process"}), name="assessment-process"),
    path("<uuid:pk>/transcript/", AssessmentViewSet.as_view({"get": "transcript"}), name="assessment-transcript"),
    path("<uuid:pk>/features/", AssessmentViewSet.as_view({"get": "features"}), name="assessment-features"),
    path("<uuid:pk>/evidence/", AssessmentViewSet.as_view({"get": "evidence"}), name="assessment-evidence"),
    path("<uuid:pk>/draft_report/", AssessmentViewSet.as_view({"get": "draft_report"}), name="assessment-draft-report"),
    path("<uuid:pk>/sign_off/", AssessmentViewSet.as_view({"post": "sign_off"}), name="assessment-sign-off"),
    path("<uuid:pk>/signed_report/", AssessmentViewSet.as_view({"get": "signed_report"}), name="assessment-signed-report"),
    path("<uuid:pk>/update_consent/", AssessmentViewSet.as_view({"post": "update_consent"}), name="assessment-update-consent"),
]
