"""
Custom permission classes for the Oracy AI API.
"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission that checks if user is an admin.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "admin"


class IsTeacher(permissions.BasePermission):
    """
    Permission that checks if user is a teacher.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "teacher"


class IsStudent(permissions.BasePermission):
    """
    Permission that checks if user is a student.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "student"


class IsAdminOrTeacher(permissions.BasePermission):
    """
    Permission that checks if user is an admin or teacher.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ["admin", "teacher"]


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that checks if user is the owner of the resource or an admin.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        return hasattr(obj, "user") and obj.user == request.user


class IsTeacherOfStudent(permissions.BasePermission):
    """
    Permission that checks if the user is a teacher of the student.
    """
    def has_object_permission(self, request, view, obj):
        from apps.students.models import Enrollment
        
        if request.user.role != "teacher":
            return False
        
        # Check if teacher has the student in any of their cohorts
        return Enrollment.objects.filter(
            student=obj,
            cohort__teacher=request.user
        ).exists()


class ReadOnly(permissions.BasePermission):
    """
    Permission that only allows read-only access.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
