from django.urls import path

from .views import (
    AuthViewSet,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    SchoolViewSet,
    UserViewSet,
)

app_name = "users"

urlpatterns = [
    # Auth URLs
    path("login/", AuthViewSet.as_view({"post": "login"}), name="login"),
    path("refresh/", AuthViewSet.as_view({"post": "refresh"}), name="refresh"),
    path("logout/", AuthViewSet.as_view({"post": "logout"}), name="logout"),
    path("register/", AuthViewSet.as_view({"post": "register"}), name="register"),
    
    # Password Reset URLs
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    
    # User URLs
    path("users/", UserViewSet.as_view({"get": "list", "post": "create"}), name="user-list"),
    path("users/me/", UserViewSet.as_view({"get": "me"}), name="user-me"),
    path("users/me/update/", UserViewSet.as_view({"patch": "update_profile"}), name="user-update-profile"),
    path("users/me/change_password/", UserViewSet.as_view({"post": "change_password"}), name="user-change-password"),
    path("users/<uuid:pk>/", UserViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="user-detail"),
    
    # School URLs
    path("schools/", SchoolViewSet.as_view({"get": "list", "post": "create"}), name="school-list"),
    path("schools/<uuid:pk>/", SchoolViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="school-detail"),
]
