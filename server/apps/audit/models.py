"""
Audit models for the Oracy AI platform.

Handles comprehensive audit logging for teacher actions and system events.
Per MVP Section 3: Teacher-in-the-Loop Verification
Per MVP Section 5: Data Architecture - AuditLogs table
"""

from django.db import models


class AuditLog(models.Model):
    """
    Comprehensive audit log for all significant actions.
    
    Tracks what changed, by whom, when - essential for:
    - Trust and accountability
    - Future model training
    - Compliance and inspection readiness
    """
    
    ACTION_CHOICES = [
        ("score_changed", "Score Changed"),
        ("clip_changed", "Evidence Clip Changed"),
        ("feedback_edited", "Feedback Edited"),
        ("signed_off", "Report Signed Off"),
        ("assessment_created", "Assessment Created"),
        ("assessment_uploaded", "Recording Uploaded"),
        ("processing_started", "Processing Started"),
        ("draft_generated", "Draft Report Generated"),
        ("notes_added", "Teacher Notes Added"),
        ("consent_updated", "Consent Updated"),
        ("student_created", "Student Created"),
        ("student_updated", "Student Updated"),
        ("user_login", "User Login"),
        ("user_logout", "User Logout"),
        ("export_generated", "Export Generated"),
    ]
    
    # What happened
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    
    # Who did it
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )
    
    # Context - what object was affected
    # Using generic relations would be cleaner, but for audit simplicity,
    # we store object type and ID as strings
    object_type = models.CharField(
        max_length=50,
        help_text="Model name: 'Assessment', 'DraftReport', etc."
    )
    object_id = models.CharField(
        max_length=50,
        help_text="UUID or ID of the affected object"
    )
    
    # Specific field that changed (if applicable)
    field = models.CharField(
        max_length=50,
        blank=True,
        help_text="Field name that was modified"
    )
    
    # Before and after values
    old_value = models.JSONField(
        null=True,
        blank=True,
        help_text="Previous value (for updates)"
    )
    new_value = models.JSONField(
        null=True,
        blank=True,
        help_text="New value after change"
    )
    
    # Additional context
    description = models.TextField(
        blank=True,
        help_text="Human-readable description of the action"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context: IP address, user agent, etc."
    )
    
    # When it happened
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["object_type", "object_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["timestamp"]),
            # Composite indexes for common queries
            models.Index(fields=["object_type", "object_id", "timestamp"]),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
    
    @classmethod
    def log_score_change(cls, user, report, strand, old_band, new_band, old_clips, new_clips):
        """Log a score change action."""
        return cls.objects.create(
            action="score_changed",
            user=user,
            object_type="DraftReport",
            object_id=str(report.id),
            field=f"{strand}_score",
            old_value={"band": old_band, "evidence_clips": old_clips},
            new_value={"band": new_band, "evidence_clips": new_clips},
            description=f"Changed {strand} band from {old_band} to {new_band}"
        )
    
    @classmethod
    def log_clip_change(cls, user, report, strand, old_clips, new_clips):
        """Log an evidence clip change."""
        return cls.objects.create(
            action="clip_changed",
            user=user,
            object_type="DraftReport",
            object_id=str(report.id),
            field=f"{strand}_score.evidence_clips",
            old_value=old_clips,
            new_value=new_clips,
            description=f"Changed {strand} evidence clips from {old_clips} to {new_clips}"
        )
    
    @classmethod
    def log_feedback_edit(cls, user, report, old_feedback, new_feedback):
        """Log a feedback edit."""
        return cls.objects.create(
            action="feedback_edited",
            user=user,
            object_type="DraftReport",
            object_id=str(report.id),
            field="feedback",
            old_value=old_feedback,
            new_value=new_feedback,
            description="Modified feedback content"
        )
    
    @classmethod
    def log_sign_off(cls, user, signed_report):
        """Log a report sign-off."""
        return cls.objects.create(
            action="signed_off",
            user=user,
            object_type="SignedReport",
            object_id=str(signed_report.id),
            description=f"Signed off report for assessment {signed_report.assessment_id}"
        )
    
    @classmethod
    def log_assessment_creation(cls, user, assessment):
        """Log assessment creation."""
        return cls.objects.create(
            action="assessment_created",
            user=user,
            object_type="Assessment",
            object_id=str(assessment.id),
            description=f"Created {assessment.mode} assessment for student {assessment.student_id}"
        )
    
    @classmethod
    def log_processing_event(cls, assessment, event_type, description=""):
        """Log a processing pipeline event."""
        return cls.objects.create(
            action=event_type,
            user=None,  # System event
            object_type="Assessment",
            object_id=str(assessment.id),
            description=description or f"Processing event: {event_type}"
        )


class ReportChangeHistory(models.Model):
    """
    Detailed change history for reports.
    
    Tracks every modification made during teacher review.
    More granular than AuditLog for report-specific changes.
    """
    
    CHANGE_TYPE_CHOICES = [
        ("strand_band", "Strand Band Changed"),
        ("evidence_clip", "Evidence Clip Changed"),
        ("justification", "Justification Edited"),
        ("strength", "Strength Modified"),
        ("next_step", "Next Step Modified"),
        ("goal", "Goal Modified"),
        ("teacher_notes", "Teacher Notes Added/Edited"),
    ]
    
    report = models.ForeignKey(
        "reports.DraftReport",
        on_delete=models.CASCADE,
        related_name="change_history"
    )
    
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    strand = models.CharField(
        max_length=20,
        blank=True,
        help_text="Which strand was affected (if applicable)"
    )
    
    # Detailed change information
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    # Who made the change
    changed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_changes"
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    
    # Reason for change (optional)
    change_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = "report_change_history"
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["report"]),
            models.Index(fields=["changed_by"]),
            models.Index(fields=["changed_at"]),
            models.Index(fields=["report", "changed_at"]),
        ]
    
    def __str__(self):
        return f"{self.change_type} on {self.report} by {self.changed_by}"
