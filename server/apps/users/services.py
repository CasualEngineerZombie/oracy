"""
User services for the Oracy AI platform.

Following Django Styleguide - Services contain business logic for writing to the database.

Naming conventions:
- user_create(*, email: str, ...) -> User
- user_update(*, user: User, ...) -> User
- user_change_password(*, user: User, ...) -> None
- user_authenticate(*, email: str, ...) -> Optional[User]
- user_generate_tokens(*, user: User) -> TokenPair
- user_refresh_access_token(*, refresh_token: str) -> AccessToken
- user_request_password_reset(*, email: str) -> Optional[str]
- user_reset_password(*, token: str, new_password: str) -> User
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.core.authentication import generate_access_token, generate_refresh_token

User = get_user_model()

# Password reset token lifetime (1 hour)
PASSWORD_RESET_TOKEN_LIFETIME = 60  # minutes


def user_create(
    *,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    role: str,
    school_id: Optional[str] = None,
    subject: Optional[str] = None,
) -> User:
    """
    Create a new user with the given data.
    
    Args:
        email: User's email address
        password: User's password (will be hashed)
        first_name: User's first name
        last_name: User's last name
        role: User's role (admin, teacher, student)
        school_id: Optional school UUID
        subject: Optional subject (for teachers)
    
    Returns:
        The created User instance
    """
    user_data = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
        "subject": subject,
    }
    
    if school_id:
        user_data["school_id"] = school_id
    
    user = User.objects.create_user(**user_data)
    user.set_password(password)
    user.full_clean()
    user.save()
    
    return user


def user_update(
    *,
    user: User,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    subject: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> User:
    """
    Update an existing user's data.
    
    Args:
        user: The user to update
        first_name: New first name (if provided)
        last_name: New last name (if provided)
        subject: New subject (if provided)
        is_active: New active status (if provided)
    
    Returns:
        The updated User instance
    """
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if subject is not None:
        user.subject = subject
    if is_active is not None:
        user.is_active = is_active
    
    user.full_clean()
    user.save()
    
    return user


def user_change_password(
    *,
    user: User,
    new_password: str,
) -> None:
    """
    Change a user's password.
    
    Args:
        user: The user whose password to change
        new_password: The new password (will be hashed)
    """
    user.set_password(new_password)
    user.save()


def user_authenticate(
    *,
    email: str,
    password: str,
) -> Optional[User]:
    """
    Authenticate a user with email and password.
    
    Args:
        email: User's email address
        password: User's password
    
    Returns:
        The User if authentication succeeds, None otherwise
    """
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return None
    
    if not user.check_password(password):
        return None
    
    return user


TokenPair = Tuple[str, str]


def user_generate_tokens(*, user: User) -> TokenPair:
    """
    Generate access and refresh tokens for a user.
    
    Args:
        user: The user to generate tokens for
    
    Returns:
        Tuple of (access_token, refresh_token)
    """
    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)
    
    return access_token, refresh_token


def user_refresh_access_token(*, refresh_token: str) -> Optional[str]:
    """
    Generate a new access token from a refresh token.
    
    Args:
        refresh_token: The refresh token string
    
    Returns:
        New access token if valid, None otherwise
    
    Raises:
        jwt.ExpiredSignatureError: If refresh token has expired
        jwt.InvalidTokenError: If refresh token is invalid
    """
    payload = jwt.decode(
        refresh_token,
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )
    
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Invalid token type")
    
    user_id = payload.get("user_id")
    user = User.objects.get(id=user_id, is_active=True)
    
    return generate_access_token(user)


def user_get_by_email(*, email: str) -> Optional[User]:
    """
    Get a user by email address.
    
    Args:
        email: The email to look up
    
    Returns:
        User if found and active, None otherwise
    """
    try:
        return User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return None


def user_get_by_id(*, user_id: str) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        user_id: The UUID of the user
    
    Returns:
        User if found and active, None otherwise
    """
    try:
        return User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return None


def generate_password_reset_token(user: User) -> str:
    """
    Generate a password reset token for the user.
    
    Args:
        user: The user requesting password reset
    
    Returns:
        JWT token for password reset
    """
    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "type": "password_reset",
        "exp": datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_TOKEN_LIFETIME),
        "iat": datetime.utcnow(),
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def user_request_password_reset(*, email: str) -> Optional[str]:
    """
    Request a password reset for a user.
    
    Args:
        email: The user's email address
    
    Returns:
        Password reset token if user exists, None otherwise
        (Returns None to prevent email enumeration)
    """
    try:
        user = User.objects.get(email__iexact=email, is_active=True)
    except User.DoesNotExist:
        # Return None to prevent email enumeration
        return None
    
    return generate_password_reset_token(user)


def user_reset_password(*, token: str, new_password: str) -> User:
    """
    Reset a user's password using a token.
    
    Args:
        token: The password reset token
        new_password: The new password
    
    Returns:
        The user whose password was reset
    
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )
    
    if payload.get("type") != "password_reset":
        raise jwt.InvalidTokenError("Invalid token type")
    
    user_id = payload.get("user_id")
    user = User.objects.get(id=user_id)
    
    user.set_password(new_password)
    user.save()
    
    return user
