"""
Assessment models for the Oracy AI platform.
"""

import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.core.models import BaseModel


class Assessment(BaseModel):
    """
    Oracy assessment model.
    
    Represents a single student assessment with metadata and status tracking.
    """
    
    # Assessment modes per MVP brief Section 1.1
    MODE_CHOICES = [
        ("presenting", "Presenting"),
        ("explaining", "Explaining"),
        ("persuading", "Persuading"),
    ]
    
    # Status workflow per database schema
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("uploading", "Uploading"),
        ("processing", "Processing"),
        ("draft_ready", "Draft Ready"),
        ("under_review", "Under Review"),
        ("signed_off", "Signed Off"),
        ("error", "Error"),
    ]
    
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="assessments"
    )
    cohort = models.ForeignKey(
        "students.Cohort",
        on_delete=models.CASCADE,
        related_name="assessments"
    )
    
    # Mode of talk (MVP Section 1.1)
    mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        help_text="Mode of talk: presenting, explaining, or persuading"
    )
    
    # Task context metadata (AI spec)
    prompt = models.TextField(help_text="The prompt or topic given to the student")
    time_limit_seconds = models.IntegerField(
        default=180,
        validators=[MinValueValidator(30), MaxValueValidator(600)],
        help_text="Time limit in seconds (30s to 10min)"
    )
    
    # Consent and privacy
    consent_obtained = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    status_message = models.TextField(blank=True, help_text="Human-readable status or error message")
    
    # Timestamps
    uploaded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "assessments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["cohort"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["mode"]),
            # Composite index for teacher dashboard queries
            models.Index(fields=["cohort", "status", "created_at"]),
        ]
    
    def __str__(self):
        return f"Assessment {self.id} - {self.student} ({self.mode})"
    
    @property
    def is_pending(self):
        return self.status == "pending"
    
    @property
    def is_processing(self):
        return self.status == "processing"
    
    @property
    def is_draft_ready(self):
        return self.status == "draft_ready"
    
    @property
    def is_under_review(self):
        return self.status == "under_review"
    
    @property
    def is_signed_off(self):
        return self.status == "signed_off"
    
    @property
    def has_recording(self):
        return hasattr(self, "recording")
    
    @property
    def has_transcript(self):
        return hasattr(self, "transcript")
    
    @property
    def has_feature_signals(self):
        return hasattr(self, "feature_signals")
    
    @property
    def has_draft_report(self):
        return hasattr(self, "draft_report")


class Recording(BaseModel):
    """
    Video/audio recording for an assessment.
    
    Stores S3 references and media metadata.
    """
    
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name="recording"
    )
    
    # Original upload info
    original_filename = models.CharField(max_length=255, blank=True)
    file_size_bytes = models.BigIntegerField()
    
    # S3 storage (MVP Section 5: Storage)
    s3_bucket = models.CharField(max_length=100)
    s3_key = models.CharField(max_length=500)
    
    # Audio extraction (for STT processing)
    audio_extracted = models.BooleanField(default=False)
    audio_s3_key = models.CharField(max_length=500, blank=True)
    
    # Media metadata
    duration_seconds = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Quality scores (MVP Section 4: Quality indicators)
    video_quality_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Video quality score 0-1"
    )
    audio_quality_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Audio quality score 0-1"
    )
    
    # Format info
    video_codec = models.CharField(max_length=50, blank=True)
    audio_codec = models.CharField(max_length=50, blank=True)
    resolution = models.CharField(max_length=20, blank=True, help_text="e.g., '1920x1080'")
    frame_rate = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = "recordings"
        indexes = [
            models.Index(fields=["assessment"]),
        ]
    
    def __str__(self):
        return f"Recording for Assessment {self.assessment_id}"
