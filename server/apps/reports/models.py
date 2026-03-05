"""
Report models for the Oracy AI platform.

Handles AI-generated draft reports and teacher-signed-off final reports.
"""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.core.models import BaseModel


class DraftReport(BaseModel):
    """
    AI-generated draft assessment report.
    
    Per MVP Section 1.3: Output (AI Draft Report)
    Contains scores, evidence clips, feedback, and goals.
    """
    
    # Band choices
    BAND_CHOICES = [
        ("emerging", "Emerging"),
        ("expected", "Expected"),
        ("exceeding", "Exceeding"),
    ]
    
    assessment = models.OneToOneField(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="draft_report"
    )
    
    # =========================================================================
    # STRAND SCORES (MVP Section 1.3)
    # Each score is stored as JSON with band, confidence, evidence, justification
    # =========================================================================
    
    # Physical strand
    physical_score = models.JSONField(
        default=dict,
        help_text="""
        {
            "band": "emerging|expected|exceeding",
            "confidence": 0.0-1.0,
            "evidence_clips": ["clip_0", "clip_3"],
            "justification": "Rubric-based justification text",
            "subskills": {
                "voice_projection": {"score": 0.7, "evidence": ["clip_1"]},
                "clarity": {"score": 0.8, "evidence": ["clip_2"]}
            }
        }
        """
    )
    
    # Linguistic strand
    linguistic_score = models.JSONField(
        default=dict,
        help_text="Same structure as physical_score"
    )
    
    # Cognitive strand
    cognitive_score = models.JSONField(
        default=dict,
        help_text="Same structure as physical_score"
    )
    
    # Social-emotional strand
    social_emotional_score = models.JSONField(
        default=dict,
        help_text="Same structure as physical_score"
    )
    
    # Overall confidence (average of strand confidences)
    overall_confidence = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    # =========================================================================
    # FEEDBACK (MVP Section 1.3)
    # =========================================================================
    
    feedback = models.JSONField(
        default=dict,
        help_text="""
        {
            "strengths": [
                {"text": "Strength 1", "strand": "cognitive", "evidence": "clip_0"},
                {"text": "Strength 2", "strand": "physical", "evidence": "clip_3"},
                {"text": "Strength 3", "strand": "linguistic", "evidence": "clip_5"}
            ],
            "next_steps": [
                {"text": "Next step 1", "strand": "social_emotional", "specific": true},
                {"text": "Next step 2", "strand": "cognitive", "specific": true},
                {"text": "Next step 3", "strand": "physical", "specific": true}
            ],
            "goals": [
                "Student-friendly practice goal 1",
                "Student-friendly practice goal 2"
            ]
        }
        """
    )
    
    # Mode-specific advice (MVP: not generic speaking tips)
    mode_specific_notes = models.TextField(
        blank=True,
        help_text="Mode-specific feedback notes"
    )
    
    # EAL accommodations (MVP Section 4: Fairness)
    eal_scaffolds = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        {
            "separated_scores": {
                "reasoning": "emerging|expected|exceeding",
                "language_surface": "emerging|expected|exceeding"
            },
            "scaffolds": [
                "Sentence stem suggestion 1",
                "Planning frame suggestion"
            ]
        }
        """
    )
    
    # =========================================================================
    # AI METADATA
    # =========================================================================
    
    ai_model = models.CharField(max_length=100, help_text="LLM model used for scoring")
    ai_provider = models.CharField(max_length=50, help_text="Provider: openai, anthropic, etc.")
    ai_version = models.CharField(max_length=50, help_text="Model version")
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generation_duration_seconds = models.FloatField(null=True, blank=True)
    
    # Processing metadata
    benchmark_version = models.CharField(
        max_length=20,
        help_text="Version of benchmark definitions used"
    )
    
    # Review status
    is_reviewed = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_draft_reports"
    )
    
    # Quality warnings
    warnings = models.JSONField(
        default=list,
        help_text="List of warnings: ['low_audio_quality', 'insufficient_evidence', etc.]"
    )
    
    class Meta:
        db_table = "draft_reports"
        indexes = [
            models.Index(fields=["assessment"]),
            models.Index(fields=["generated_at"]),
            models.Index(fields=["is_reviewed"]),
            models.Index(fields=["reviewed_by"]),
        ]
    
    def __str__(self):
        return f"Draft Report for Assessment {self.assessment_id}"
    
    @property
    def all_strands(self):
        """Return all strand scores as a dict."""
        return {
            "physical": self.physical_score,
            "linguistic": self.linguistic_score,
            "cognitive": self.cognitive_score,
            "social_emotional": self.social_emotional_score,
        }
    
    def get_strand_band(self, strand):
        """Get the band for a specific strand."""
        score_data = getattr(self, f"{strand}_score", {})
        return score_data.get("band")
    
    def has_sufficient_evidence(self, min_confidence=0.5):
        """Check if report has sufficient evidence across all strands."""
        for strand in ["physical", "linguistic", "cognitive", "social_emotional"]:
            score_data = getattr(self, f"{strand}_score", {})
            if score_data.get("confidence", 0) < min_confidence:
                return False
        return True


class SignedReport(BaseModel):
    """
    Teacher-signed-off final report.
    
    Per MVP Section 3: Teacher-in-the-Loop Verification
    This is the canonical version after teacher review.
    """
    
    assessment = models.OneToOneField(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="signed_report"
    )
    
    # Link to the draft report
    draft_report = models.ForeignKey(
        DraftReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="signed_version"
    )
    
    # =========================================================================
    # FINAL SCORES (may differ from draft after teacher edits)
    # =========================================================================
    
    physical_score = models.JSONField(
        default=dict,
        help_text="Final physical strand score after teacher review"
    )
    linguistic_score = models.JSONField(
        default=dict,
        help_text="Final linguistic strand score after teacher review"
    )
    cognitive_score = models.JSONField(
        default=dict,
        help_text="Final cognitive strand score after teacher review"
    )
    social_emotional_score = models.JSONField(
        default=dict,
        help_text="Final social-emotional strand score after teacher review"
    )
    
    # =========================================================================
    # FINAL FEEDBACK
    # =========================================================================
    
    feedback = models.JSONField(
        default=dict,
        help_text="Final feedback after teacher edits"
    )
    
    # Teacher notes (private, not shown to students)
    teacher_notes = models.TextField(
        blank=True,
        help_text="Private notes for teacher reference"
    )
    
    # =========================================================================
    # SIGN-OFF
    # =========================================================================
    
    signed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="signed_reports",
        limit_choices_to={"role__in": ["teacher", "admin"]}
    )
    signed_at = models.DateTimeField(null=True, blank=True)
    
    # Digital signature/verification
    signature_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="Hash of report content for verification"
    )
    
    # Changes summary (what was modified from draft)
    changes_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        {
            "scores_modified": ["physical", "cognitive"],
            "clips_swapped": {"physical": ["clip_0", "clip_2"]},
            "feedback_edited": true,
            "notes_added": true
        }
        """
    )
    
    # Export tracking
    exported_at = models.DateTimeField(null=True, blank=True)
    export_format = models.CharField(
        max_length=20,
        blank=True,
        choices=[("pdf", "PDF"), ("csv", "CSV"), ("json", "JSON")]
    )
    
    class Meta:
        db_table = "signed_reports"
        indexes = [
            models.Index(fields=["assessment"]),
            models.Index(fields=["signed_by"]),
            models.Index(fields=["signed_at"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"Signed Report for Assessment {self.assessment_id}"
    
    @property
    def is_signed(self):
        return self.signed_at is not None and self.signed_by is not None
    
    def get_changes_from_draft(self):
        """Compare with draft report and identify changes."""
        if not self.draft_report:
            return {}
        
        changes = {
            "scores_modified": [],
            "clips_changed": {},
            "feedback_edited": False,
        }
        
        for strand in ["physical", "linguistic", "cognitive", "social_emotional"]:
            draft_band = self.draft_report.get_strand_band(strand)
            final_data = getattr(self, f"{strand}_score", {})
            final_band = final_data.get("band")
            
            if draft_band != final_band:
                changes["scores_modified"].append(strand)
            
            # Check evidence clips
            draft_clips = set(self.draft_report.all_strands.get(strand, {}).get("evidence_clips", []))
            final_clips = set(final_data.get("evidence_clips", []))
            if draft_clips != final_clips:
                changes["clips_changed"][strand] = {
                    "removed": list(draft_clips - final_clips),
                    "added": list(final_clips - draft_clips),
                }
        
        # Check feedback
        if self.feedback != self.draft_report.feedback:
            changes["feedback_edited"] = True
        
        return changes
