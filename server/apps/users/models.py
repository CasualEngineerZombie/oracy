"""
User models for authentication and user management.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class School(models.Model):
    """
    School/Institution model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    identifier = models.CharField(max_length=50, unique=True)
    region = models.CharField(max_length=50, help_text="For data residency")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["name"]
        db_table = "schools"
    
    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with role-based access control.
    """
    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("teacher", "Teacher"),
        ("student", "Student"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    # Role
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    
    # School relationship
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users"
    )
    
    # Teacher-specific fields
    subject = models.CharField(max_length=100, blank=True)
    
    # Status
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    
    class Meta:
        ordering = ["-date_joined"]
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
            models.Index(fields=["school"]),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    @property
    def is_admin(self):
        return self.role == "admin"
    
    @property
    def is_teacher(self):
        return self.role == "teacher"
    
    @property
    def is_student_user(self):
        return self.role == "student"
