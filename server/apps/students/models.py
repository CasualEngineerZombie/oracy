"""
Student and cohort management models.
"""

import uuid

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Student(BaseModel):
    """
    Student profile model.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )
    student_id = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    year_group = models.CharField(max_length=10, help_text="e.g., '7', '11'")
    age_band = models.CharField(max_length=10, help_text="e.g., '11-12'")
    
    # Language profile
    eal = models.BooleanField(default=False, verbose_name="English as Additional Language")
    first_language = models.CharField(max_length=50, blank=True)
    
    # Accommodations (SEND, etc.)
    accommodations = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ["student_id"]
        db_table = "students"
        indexes = [
            models.Index(fields=["year_group"]),
            models.Index(fields=["age_band"]),
            models.Index(fields=["student_id"]),
        ]
    
    def __str__(self):
        return f"{self.student_id} - {self.user.full_name}"
    
    @property
    def full_name(self):
        return self.user.full_name
    
    @property
    def email(self):
        return self.user.email


class Cohort(BaseModel):
    """
    Class/group of students.
    """
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "teacher"},
        related_name="cohorts"
    )
    year_group = models.CharField(max_length=10)
    academic_year = models.CharField(max_length=9, help_text="e.g., '2025-2026'")
    students = models.ManyToManyField(
        Student,
        through="Enrollment",
        related_name="cohorts"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["-academic_year", "name"]
        db_table = "cohorts"
        unique_together = ["name", "teacher", "academic_year"]
        indexes = [
            models.Index(fields=["teacher"]),
            models.Index(fields=["academic_year"]),
            models.Index(fields=["year_group"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.academic_year})"


class Enrollment(BaseModel):
    """
    Student-Cohort relationship.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    cohort = models.ForeignKey(
        Cohort,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "enrollments"
        unique_together = ["student", "cohort"]
        indexes = [
            models.Index(fields=["student", "cohort"]),
            models.Index(fields=["cohort", "enrolled_at"]),
        ]
    
    def __str__(self):
        return f"{self.student} in {self.cohort}"
    
    @property
    def is_active(self):
        return self.withdrawn_at is None
