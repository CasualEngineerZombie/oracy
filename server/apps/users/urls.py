"""
URL configuration for the users app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthViewSet, SchoolViewSet, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"schools", SchoolViewSet, basename="school")

# Auth routes
auth_patterns = [
    path("login/", AuthViewSet.as_view({"post": "login"}), name="login"),
    path("refresh/", AuthViewSet.as_view({"post": "refresh"}), name="refresh"),
    path("logout/", AuthViewSet.as_view({"post": "logout"}), name="logout"),
]

urlpatterns = [
    path("", include(router.urls)),
    path("", include(auth_patterns)),
]
