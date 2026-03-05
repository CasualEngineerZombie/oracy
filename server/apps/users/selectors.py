"""
User selectors for the Oracy AI platform.

Following Django Styleguide - Selectors contain business logic for fetching from the database.

Naming conventions:
- user_get(*, user_id: str) -> Optional[User]
- user_get_by_email(*, email: str) -> Optional[User]
- user_list(*, filters: dict) -> QuerySet[User]
- user_list_for_school(*, school_id: str) -> QuerySet[User]
"""

from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

User = get_user_model()


def user_get(*, user_id: str) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        user_id: The UUID of the user
    
    Returns:
        User if found, None otherwise
    """
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


def user_get_by_email(*, email: str) -> Optional[User]:
    """
    Get a user by email address.
    
    Args:
        email: The email to look up
    
    Returns:
        User if found, None otherwise
    """
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


def user_list(
    *,
    role: Optional[str] = None,
    school_id: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> QuerySet[User]:
    """
    List users with optional filtering.
    
    Args:
        role: Filter by role (admin, teacher, student)
        school_id: Filter by school
        is_active: Filter by active status
    
    Returns:
        QuerySet of users
    """
    queryset = User.objects.all()
    
    if role:
        queryset = queryset.filter(role=role)
    if school_id:
        queryset = queryset.filter(school_id=school_id)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    return queryset


def user_list_teachers(*, school_id: Optional[str] = None) -> QuerySet[User]:
    """
    List all teachers.
    
    Args:
        school_id: Optional school filter
    
    Returns:
        QuerySet of teacher users
    """
    queryset = User.objects.filter(role="teacher")
    
    if school_id:
        queryset = queryset.filter(school_id=school_id)
    
    return queryset


def user_list_students(*, school_id: Optional[str] = None) -> QuerySet[User]:
    """
    List all student users.
    
    Args:
        school_id: Optional school filter
    
    Returns:
        QuerySet of student users
    """
    queryset = User.objects.filter(role="student")
    
    if school_id:
        queryset = queryset.filter(school_id=school_id)
    
    return queryset


def user_list_admins() -> QuerySet[User]:
    """
    List all admin users.
    
    Returns:
        QuerySet of admin users
    """
    return User.objects.filter(role="admin")


def user_exists(*, email: str) -> bool:
    """
    Check if a user with the given email exists.
    
    Args:
        email: The email to check
    
    Returns:
        True if user exists, False otherwise
    """
    return User.objects.filter(email=email).exists()


def user_get_active(*, user_id: str) -> Optional[User]:
    """
    Get an active user by ID.
    
    Args:
        user_id: The UUID of the user
    
    Returns:
        User if found and active, None otherwise
    """
    try:
        return User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return None
