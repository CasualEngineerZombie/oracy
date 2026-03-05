"""
Views for the users app.
"""

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
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
    RefreshTokenSerializer,
    SchoolSerializer,
    TokenRefreshResponseSerializer,
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

    @extend_schema(
        summary="User Login",
        description="Authenticate user with email and password to receive JWT tokens.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Login successful",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "token_type": "Bearer",
                            "expires_in": 3600,
                            "user": {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "email": "user@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "full_name": "John Doe",
                                "role": "teacher",
                                "school": None,
                                "subject": "Mathematics",
                                "is_active": True,
                                "is_verified": True,
                                "date_joined": "2024-01-01T00:00:00Z",
                            },
                        },
                    ),
                ],
            ),
            401: OpenApiResponse(
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        "Invalid Credentials",
                        value={"error": "Invalid credentials"},
                    ),
                ],
            ),
        },
        tags=["Authentication"],
    )
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
    
    @extend_schema(
        summary="Refresh Access Token",
        description="Generate a new access token using a valid refresh token.",
        request=RefreshTokenSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenRefreshResponseSerializer,
                description="Token refresh successful",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "token_type": "Bearer",
                            "expires_in": 3600,
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(
                description="Refresh token is required",
                examples=[
                    OpenApiExample(
                        "Missing Token",
                        value={"error": "Refresh token is required"},
                    ),
                ],
            ),
            401: OpenApiResponse(
                description="Invalid or expired token",
                examples=[
                    OpenApiExample(
                        "Expired Token",
                        value={"error": "Refresh token has expired"},
                    ),
                    OpenApiExample(
                        "Invalid Token",
                        value={"error": "Invalid token"},
                    ),
                ],
            ),
        },
        tags=["Authentication"],
    )
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
    
    @extend_schema(
        summary="User Logout",
        description="Logout user. Client should discard stored tokens. Requires authentication.",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Logout successful",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "Successfully logged out"},
                    ),
                ],
            ),
            401: OpenApiResponse(
                description="Authentication required",
            ),
        },
        tags=["Authentication"],
    )
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout user (client should discard tokens).
        """
        return Response({"message": "Successfully logged out"})

    @extend_schema(
        summary="Register New User",
        description="Register a new user account. Does not require authentication. Only works if no admin exists yet (initial setup) or for public registration if enabled.",
        request=UserCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=UserSerializer,
                description="User created successfully",
            ),
            400: OpenApiResponse(
                description="Validation error",
            ),
            403: OpenApiResponse(
                description="Registration disabled - admin users already exist",
            ),
        },
        tags=["Authentication"],
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        """
        Register a new user. Only works for initial setup when no admin exists.
        """
        # Check if this is initial setup (no admin users exist)
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # If admin users already exist, require admin permission to create more
        if User.objects.filter(role="admin").exists():
            return Response(
                {"error": "Registration is disabled. Contact an administrator to create an account."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Allow first user to be created (will be admin)
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create user with admin role for initial setup
        user = User.objects.create_user(**serializer.validated_data)
        user.role = "admin"
        user.is_verified = True
        user.save()

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        summary="List Users",
        description="Get a paginated list of users. Admins see all users, teachers see school users.",
    ),
    create=extend_schema(
        summary="Create User",
        description="Create a new user. Only admins can create users.",
        request=UserCreateSerializer,
        responses={201: UserSerializer},
    ),
    retrieve=extend_schema(
        summary="Get User",
        description="Retrieve a specific user by ID.",
        responses={200: UserSerializer},
    ),
    update=extend_schema(
        summary="Update User",
        description="Fully update a user. Only admins can update any user.",
        request=UserUpdateSerializer,
        responses={200: UserSerializer},
    ),
    partial_update=extend_schema(
        summary="Partial Update User",
        description="Partially update a user. Only admins can update any user.",
        request=UserUpdateSerializer,
        responses={200: UserSerializer},
    ),
    destroy=extend_schema(
        summary="Delete User",
        description="Delete a user. Only admins can delete users.",
        responses={204: None},
    ),
)
@extend_schema(tags=["Users"])
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
    
    @extend_schema(
        summary="Get Current User",
        description="Get the profile of the currently authenticated user.",
        responses={200: UserProfileSerializer},
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current user profile.
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Update Current User Profile",
        description="Update the profile of the currently authenticated user.",
        request=UserUpdateSerializer,
        responses={200: UserProfileSerializer},
    )
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
    
    @extend_schema(
        summary="Change Password",
        description="Change the password of the currently authenticated user.",
        request=PasswordChangeSerializer,
        responses={
            200: OpenApiResponse(
                description="Password changed successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "Password changed successfully"},
                    ),
                ],
            ),
            400: OpenApiResponse(
                description="Invalid password",
                examples=[
                    OpenApiExample(
                        "Wrong Password",
                        value={"error": "Current password is incorrect"},
                    ),
                ],
            ),
        },
    )
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


@extend_schema(tags=["Schools"])
class SchoolViewSet(viewsets.ModelViewSet):
    """
    ViewSet for school management.
    """
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAdmin]
