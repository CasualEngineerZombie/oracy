"""
Custom User manager.
"""

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular User with the given email and password.
        """
        if not email:
            raise ValueError("The Email must be set")
        
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        
        return self.create_user(email, password, **extra_fields)
    
    def teachers(self):
        """
        Return queryset of teachers.
        """
        return self.filter(role="teacher")
    
    def students(self):
        """
        Return queryset of students.
        """
        return self.filter(role="student")
    
    def admins(self):
        """
        Return queryset of admins.
        """
        return self.filter(role="admin")
