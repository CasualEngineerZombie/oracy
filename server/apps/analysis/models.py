"""
Analysis models for the Oracy AI platform.

Handles transcript storage, feature signal extraction, and evidence candidates.
"""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.core.models import BaseModel


class Transcript(BaseModel):
    """
    Speech-to-text transcript with timestamps.
    
    Stores word-level or segment-level timestamps for analysis.
    Per MVP Section 2.1: Speech-to-Text (Timestamped)
    """
    
    assessment = models.OneToOneField(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="transcript"
    )
    
    # Segments with timestamps (JSON structure)
    # Format: [{"start": 0.0, "end": 5.2, "text": "...", 
    #           "words": [{"word": "...", "start": 0.0, "end": 0.5, "confidence": 0.95}]}]
    segments = models.JSONField(help_text="Transcript segments with word-level timestamps")
    
    # Full text for search/analysis
    full_text = models.TextField(help_text="Complete transcript text")
    
    # Language detection
    language = models.CharField(max_length=10, default="en-GB")
    
    # Confidence metrics
    confidence = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Overall transcription confidence"
    )
    
    # Provider info (MVP: Abstract behind service interface)
    provider = models.CharField(max_length=50, help_text="STT provider: openai, aws, etc.")
    model_version = models.CharField(max_length=50, help_text="Model version used")
    
    # Processing metadata
    processing_time_seconds = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = "transcripts"
        indexes = [
            models.Index(fields=["assessment"]),
            # Full-text search index (PostgreSQL)
            models.Index(fields=["full_text"], name="transcripts_full_text_fts"),
        ]
    
    def __str__(self):
        return f"Transcript for Assessment {self.assessment_id}"
    
    @property
    def word_count(self):
        """Count total words in transcript."""
        if not self.segments:
            return 0
        return sum(
            len(segment.get("words", []))
            for segment in self.segments
        )
    
    @property
    def duration(self):
        """Get transcript duration from last segment."""
        if not self.segments:
            return 0
        return self.segments[-1].get("end", 0)


class FeatureSignals(BaseModel):
    """
    Extracted feature signals from audio/video analysis.
    
    Per MVP Section 2.2: Deterministic Feature Extraction
    All values are normalized/scaled signals (0-1 range where applicable).
    """
    
    assessment = models.OneToOneField(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="feature_signals"
    )
    
    # Quality flag (MVP Section 4: Fairness safeguards)
    QUALITY_CHOICES = [
        ("good", "Good"),
        ("fair", "Fair"),
        ("poor", "Poor"),
    ]
    quality_flag = models.CharField(
        max_length=10,
        choices=QUALITY_CHOICES,
        default="good",
        help_text="Overall media quality assessment"
    )
    
    # =========================================================================
    # PHYSICAL FEATURES (MVP Section 2.2)
    # =========================================================================
    
    # Pace and pauses
    wpm = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text="Words per minute"
    )
    pause_ratio = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Ratio of pause time to total time"
    )
    pause_count = models.IntegerField(null=True, blank=True, help_text="Number of pauses detected")
    
    # Fillers and disfluencies
    filler_frequency = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Filler words per minute (um, uh, etc.)"
    )
    filler_count = models.IntegerField(null=True, blank=True)
    
    # Audio characteristics
    volume_variance = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="RMS energy variance (volume variability)"
    )
    volume_mean = models.FloatField(null=True, blank=True, help_text="Mean volume level")
    
    rhythm_stability = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Rhythm consistency score"
    )
    
    # Speech rate variability
    speech_rate_variance = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Variance in speaking rate"
    )
    
    # =========================================================================
    # LINGUISTIC FEATURES (MVP Section 2.2)
    # =========================================================================
    
    sentence_count = models.IntegerField(null=True, blank=True)
    
    sentence_length_mean = models.FloatField(
        null=True,
        blank=True,
        help_text="Average words per sentence"
    )
    sentence_length_variance = models.FloatField(
        null=True,
        blank=True,
        help_text="Variance in sentence length"
    )
    
    vocabulary_diversity = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Type-token ratio or similar diversity measure"
    )
    unique_word_count = models.IntegerField(null=True, blank=True)
    
    prompt_relevance = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Semantic relevance to prompt"
    )
    
    clarity_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Overall clarity based on audio + linguistic features"
    )
    
    register_formality = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Formality level of language"
    )
    
    # =========================================================================
    # COGNITIVE FEATURES (MVP Section 2.2)
    # =========================================================================
    
    # Reason markers
    reason_marker_count = models.IntegerField(null=True, blank=True)
    reason_density = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Reason markers per 100 words (because, for example, etc.)"
    )
    
    # Structure signals
    has_introduction = models.BooleanField(null=True, blank=True)
    has_conclusion = models.BooleanField(null=True, blank=True)
    structure_completeness = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="How complete the structure (intro/body/conclusion)"
    )
    
    # Counterpoints and argumentation
    counterpoint_count = models.IntegerField(null=True, blank=True)
    counterpoint_density = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Counterpoint markers per 100 words (however, although, etc.)"
    )
    
    # Logical connectors
    logical_connector_count = models.IntegerField(null=True, blank=True)
    logical_connector_density = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Logical connectors per 100 words (therefore, thus, etc.)"
    )
    
    # Evidence markers
    evidence_marker_count = models.IntegerField(null=True, blank=True)
    evidence_density = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Evidence markers per 100 words"
    )
    
    # Coherence
    coherence_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Discourse coherence score"
    )
    
    # =========================================================================
    # SOCIAL-EMOTIONAL FEATURES (MVP Section 2.2)
    # =========================================================================
    
    # Audience awareness (solo mode - MVP scope)
    audience_reference_count = models.IntegerField(null=True, blank=True)
    audience_reference_frequency = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Audience references per 100 words"
    )
    
    # Intention clarity
    intention_clarity = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Clarity of communicative intent"
    )
    
    # Sentiment analysis
    sentiment_positive = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    sentiment_negative = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    sentiment_neutral = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    sentiment_compound = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-1), MaxValueValidator(1)],
        help_text="Overall sentiment compound score"
    )
    
    # Confidence markers
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Speaker confidence estimate"
    )
    
    # =========================================================================
    # METADATA
    # =========================================================================
    
    extracted_at = models.DateTimeField(auto_now_add=True)
    extraction_duration_seconds = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = "feature_signals"
        indexes = [
            models.Index(fields=["assessment"]),
            models.Index(fields=["quality_flag"]),
        ]
    
    def __str__(self):
        return f"FeatureSignals for Assessment {self.assessment_id}"


class EvidenceCandidate(BaseModel):
    """
    Pre-generated evidence clip candidates.
    
    Per MVP Section 2.4: Evidence Candidate Generation (Deterministic)
    These are candidate segments that the LLM can select from for evidence.
    """
    
    # Candidate types
    TYPE_CHOICES = [
        ("transcript_boundary", "Transcript Boundary"),
        ("reason_dense", "Reason Dense"),
        ("filler_heavy", "Filler Heavy"),
        ("volume_variance", "Volume Variance"),
        ("prompt_relevant", "Prompt Relevant"),
        ("introduction", "Introduction"),
        ("conclusion", "Conclusion"),
        ("example_given", "Example Given"),
        ("counterpoint", "Counterpoint"),
        ("audience_reference", "Audience Reference"),
    ]
    
    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="evidence_candidates"
    )
    
    # Candidate identifier (clip_0, clip_1, etc.)
    candidate_id = models.CharField(max_length=20, help_text="e.g., 'clip_0', 'clip_1'")
    
    # Timing
    start_time = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Start time in seconds"
    )
    end_time = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="End time in seconds"
    )
    
    # Type and summary
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    summary = models.TextField(help_text="Brief description of the segment")
    
    # Transcript excerpt
    transcript_text = models.TextField(help_text="The transcript text for this segment")
    
    # Features JSON (relevant features for this segment)
    features = models.JSONField(
        default=dict,
        help_text="Relevant features: {wpm, filler_count, reason_markers, etc.}"
    )
    
    # Strand relevance (which strands this candidate might support)
    relevant_strands = models.JSONField(
        default=list,
        help_text="List of strands this candidate is relevant for: ['physical', 'linguistic', 'cognitive', 'social_emotional']"
    )
    
    class Meta:
        db_table = "evidence_candidates"
        unique_together = ["assessment", "candidate_id"]
        indexes = [
            models.Index(fields=["assessment"]),
            models.Index(fields=["assessment", "type"]),
            models.Index(fields=["type"]),
        ]
    
    def __str__(self):
        return f"Evidence {self.candidate_id} for Assessment {self.assessment_id}"
    
    @property
    def duration(self):
        return self.end_time - self.start_time
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be greater than start time")
        if self.duration < 5 or self.duration > 60:
            raise ValidationError("Evidence clips should be 5-60 seconds")
