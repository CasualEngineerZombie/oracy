"""
Views for the users app.
"""

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.authentication import (
    generate_access_token,
    generate_refresh_token,
)
from apps.core.permissions import IsAdmin, IsAdminOrTeacher

from .models import School
from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    SchoolSerializer,
    TokenResponseSerializer,
    UserCreateSerializer,
    UserProfileSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    """
    Authentication viewset for login, logout, and token refresh.
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=["post"])
    def login(self, request):
        """
        Authenticate user and return JWT tokens.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate tokens
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        
        return Response({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_LIFETIME * 60,
            "user": UserSerializer(user).data,
        })
    
    @action(detail=False, methods=["post"])
    def refresh(self, request):
        """
        Refresh access token using refresh token.
        """
        refresh_token = request.data.get("refresh_token")
        
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            
            if payload.get("type") != "refresh":
                raise jwt.InvalidTokenError("Invalid token type")
            
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id, is_active=True)
            
        except jwt.ExpiredSignatureError:
            return Response(
                {"error": "Refresh token has expired"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate new access token
        access_token = generate_access_token(user)
        
        return Response({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_LIFETIME * 60,
        })
    
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout user (client should discard tokens).
        """
        return Response({"message": "Successfully logged out"})


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        Custom permissions for different actions.
        """
        if self.action == "create":
            return [IsAdmin()]
        elif self.action in ["list", "destroy"]:
            return [IsAdmin()]
        elif self.action in ["retrieve", "update", "partial_update"]:
            return [IsAuthenticated()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class.
        """
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        """
        Filter users based on role.
        """
        user = self.request.user
        
        if user.role == "admin":
            return User.objects.all()
        elif user.role == "teacher":
            # Teachers can see users from their school
            return User.objects.filter(school=user.school)
        else:
            # Students can only see themselves
            return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current user profile.
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=["patch"], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Update current user profile.
        """
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(UserProfileSerializer(request.user).data)
    
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change user password.
        """
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"error": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        
        return Response({"message": "Password changed successfully"})


class SchoolViewSet(viewsets.ModelViewSet):
    """
    ViewSet for school management.
    """
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAdmin]
