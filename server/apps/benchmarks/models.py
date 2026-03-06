"""
Benchmark models for the Oracy AI platform.

This is the core IP - the Benchmark Definition Language (BDL).
Per MVP Section 2.3: Benchmarking Layer (Core IP)
"""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class BenchmarkVersion(models.Model):
    """
    Benchmark Definition Language (BDL) storage.
    
    Versioned rubric definitions for each age band and mode of talk.
    This is the core IP that must be modular and separable from AI provider.
    """
    
    # Primary key is composite: version + age_band + mode
    version = models.CharField(max_length=20, help_text="e.g., 'v1.0.0', 'v1.1.0'")
    age_band = models.CharField(max_length=10, help_text="e.g., '11-12', '13-14'")
    
    MODE_CHOICES = [
        ("presenting", "Presenting"),
        ("explaining", "Explaining"),
        ("persuading", "Persuading"),
    ]
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    
    # Full BDL definition as structured JSON
    definition = models.JSONField(
        help_text="""
        Complete benchmark definition:
        {
            "version": "v1.0.0",
            "age_band": "11-12",
            "mode": "presenting",
            "strands": {
                "physical": {
                    "description": "Physical delivery and voice",
                    "subskills": {
                        "voice_projection": {
                            "description": "Clear, audible voice",
                            "weight": 0.3,
                            "bands": {
                                "emerging": {
                                    "descriptor": "Voice is often too quiet or unclear",
                                    "evidence_rules": ["wpm < 80 OR volume_variance < 0.3"],
                                    "disallowed": ["mumbled speech", "inaudible sections"]
                                },
                                "expected": {
                                    "descriptor": "Voice is generally clear and audible",
                                    "evidence_rules": ["wpm 80-140 AND volume_variance 0.3-0.7"],
                                    "disallowed": []
                                },
                                "exceeding": {
                                    "descriptor": "Voice is consistently clear with effective variation",
                                    "evidence_rules": ["wpm 100-160 AND volume_variance > 0.5 AND rhythm_stability > 0.7"],
                                    "disallowed": []
                                }
                            }
                        },
                        "pace_control": {...},
                        "clarity": {...}
                    }
                },
                "linguistic": {...},
                "cognitive": {...},
                "social_emotional": {...}
            },
            "scoring_logic": {
                "minimum_evidence_clips": 3,
                "maximum_evidence_clips": 8,
                "confidence_threshold": 0.6,
                "strand_weights": {
                    "physical": 0.25,
                    "linguistic": 0.25,
                    "cognitive": 0.35,
                    "social_emotional": 0.15
                }
            },
            "feedback_templates": {
                "strengths": {
                    "presenting": [
                        "You maintained good eye contact with your audience",
                        "Your opening was clear and engaging",
                        "You used vocal variety effectively to emphasize key points"
                    ],
                    "explaining": [...],
                    "persuading": [...]
                },
                "next_steps": {
                    "presenting": [...],
                    "explaining": [...],
                    "persuading": [...]
                }
            },
            "eal_scaffolds": {
                "sentence_stems": [...],
                "planning_frames": [...],
                "vocabulary_supports": [...]
            }
        }
        """
    )
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Whether this version is currently in use")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_benchmarks"
    )
    notes = models.TextField(blank=True, help_text="Release notes or changelog")
    
    class Meta:
        db_table = "benchmark_versions"
        unique_together = ["version", "age_band", "mode"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["age_band", "mode"]),
            models.Index(fields=["age_band", "mode", "is_active"]),
        ]
        ordering = ["-version", "age_band", "mode"]
    
    def __str__(self):
        return f"Benchmark {self.version} - {self.age_band} - {self.mode}"
    
    @classmethod
    def get_active_benchmark(cls, age_band, mode):
        """Get the active benchmark for a given age band and mode."""
        return cls.objects.filter(
            age_band=age_band,
            mode=mode,
            is_active=True
        ).first()
    
    @classmethod
    def get_latest_version(cls, age_band, mode):
        """Get the latest benchmark version for a given age band and mode."""
        return cls.objects.filter(
            age_band=age_band,
            mode=mode
        ).order_by("-version").first()
    
    def get_strand_definition(self, strand):
        """Get the definition for a specific strand."""
        return self.definition.get("strands", {}).get(strand, {})
    
    def get_band_descriptor(self, strand, band):
        """Get the descriptor for a specific strand and band."""
        strand_def = self.get_strand_definition(strand)
        return strand_def.get("bands", {}).get(band, {})
    
    def get_scoring_logic(self):
        """Get the scoring logic configuration."""
        return self.definition.get("scoring_logic", {})
    
    def get_feedback_templates(self, type_name):
        """Get feedback templates for a specific type."""
        return self.definition.get("feedback_templates", {}).get(type_name, {})
    
    def get_eal_scaffolds(self):
        """Get EAL scaffolding suggestions."""
        return self.definition.get("eal_scaffolds", {})


class StrandSubskill(models.Model):
    """
    Individual subskill definitions within a benchmark.
    
    Optional normalized storage for easier querying.
    """
    
    STRAND_CHOICES = [
        ("physical", "Physical"),
        ("linguistic", "Linguistic"),
        ("cognitive", "Cognitive"),
        ("social_emotional", "Social-Emotional"),
    ]
    
    BAND_CHOICES = [
        ("emerging", "Emerging"),
        ("expected", "Expected"),
        ("exceeding", "Exceeding"),
    ]
    
    benchmark = models.ForeignKey(
        BenchmarkVersion,
        on_delete=models.CASCADE,
        related_name="subskills"
    )
    
    strand = models.CharField(max_length=20, choices=STRAND_CHOICES)
    name = models.CharField(max_length=50, help_text="e.g., 'voice_projection'")
    description = models.TextField()
    weight = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight within the strand"
    )
    
    # Band descriptors
    emerging_descriptor = models.TextField()
    expected_descriptor = models.TextField()
    exceeding_descriptor = models.TextField()
    
    # Evidence rules (simplified storage)
    evidence_rules = models.JSONField(
        default=list,
        help_text="List of evidence rule strings"
    )
    disallowed_shortcuts = models.JSONField(
        default=list,
        help_text="List of patterns that should not count as evidence"
    )
    
    class Meta:
        db_table = "strand_subskills"
        unique_together = ["benchmark", "strand", "name"]
        indexes = [
            models.Index(fields=["benchmark", "strand"]),
        ]
    
    def __str__(self):
        return f"{self.strand}.{self.name} ({self.benchmark})"
    
    def get_descriptor(self, band):
        """Get the descriptor for a specific band."""
        return getattr(self, f"{band}_descriptor", "")
