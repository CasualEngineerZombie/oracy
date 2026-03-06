from django.urls import path

from .views import CohortViewSet, StudentViewSet

app_name = "students"

urlpatterns = [
    # Student URLs
    path("", StudentViewSet.as_view({"get": "list", "post": "create"}), name="student-list"),
    path("<uuid:pk>/", StudentViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="student-detail"),
    path("<uuid:pk>/assessments/", StudentViewSet.as_view({"get": "assessments"}), name="student-assessments"),
    
    # Cohort URLs
    path("cohorts/", CohortViewSet.as_view({"get": "list", "post": "create"}), name="cohort-list"),
    path("cohorts/<uuid:pk>/", CohortViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="cohort-detail"),
    path("cohorts/<uuid:pk>/add_student/", CohortViewSet.as_view({"post": "add_student"}), name="cohort-add-student"),
    path("cohorts/<uuid:pk>/remove_student/", CohortViewSet.as_view({"post": "remove_student"}), name="cohort-remove-student"),
]
