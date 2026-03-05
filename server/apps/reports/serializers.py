"""
Serializers for the reports app.
"""

from rest_framework import serializers

from .models import DraftReport, SignedReport


class StrandScoreSerializer(serializers.Serializer):
    """Serializer for strand score data."""
    band = serializers.ChoiceField(choices=['emerging', 'expected', 'exceeding'])
    confidence = serializers.FloatField(min_value=0, max_value=1, required=False)
    evidence_clips = serializers.ListField(child=serializers.CharField(), required=False)
    justification = serializers.CharField(required=False)
    subskills = serializers.DictField(required=False)


class FeedbackSerializer(serializers.Serializer):
    """Serializer for feedback data."""
    strengths = serializers.ListField(required=False)
    next_steps = serializers.ListField(required=False)
    goals = serializers.ListField(child=serializers.CharField(), required=False)


class DraftReportSerializer(serializers.ModelSerializer):
    """Serializer for draft reports."""
    
    physical_score = serializers.JSONField()
    linguistic_score = serializers.JSONField()
    cognitive_score = serializers.JSONField()
    social_emotional_score = serializers.JSONField()
    feedback = serializers.JSONField()
    eal_scaffolds = serializers.JSONField(required=False)
    warnings = serializers.ListField(child=serializers.CharField(), required=False)
    
    # Read-only assessment details
    assessment_mode = serializers.CharField(source='assessment.mode', read_only=True)
    assessment_prompt = serializers.CharField(source='assessment.prompt', read_only=True)
    student_name = serializers.CharField(source='assessment.student.get_full_name', read_only=True)
    
    class Meta:
        model = DraftReport
        fields = [
            'id',
            'assessment',
            'assessment_mode',
            'assessment_prompt',
            'student_name',
            'physical_score',
            'linguistic_score',
            'cognitive_score',
            'social_emotional_score',
            'feedback',
            'eal_scaffolds',
            'overall_confidence',
            'warnings',
            'is_reviewed',
            'reviewed_by',
            'reviewed_at',
            'generated_at',
            'ai_model',
            'ai_provider',
            'benchmark_version',
        ]
        read_only_fields = [
            'generated_at',
            'ai_model',
            'ai_provider',
            'ai_version',
        ]


class SignedReportSerializer(serializers.ModelSerializer):
    """Serializer for signed reports."""
    
    physical_score = serializers.JSONField()
    linguistic_score = serializers.JSONField()
    cognitive_score = serializers.JSONField()
    social_emotional_score = serializers.JSONField()
    feedback = serializers.JSONField()
    changes_summary = serializers.JSONField(required=False)
    
    # Read-only details
    assessment_mode = serializers.CharField(source='assessment.mode', read_only=True)
    assessment_prompt = serializers.CharField(source='assessment.prompt', read_only=True)
    student_name = serializers.CharField(source='assessment.student.get_full_name', read_only=True)
    signed_by_name = serializers.CharField(source='signed_by.get_full_name', read_only=True)
    
    class Meta:
        model = SignedReport
        fields = [
            'id',
            'assessment',
            'draft_report',
            'assessment_mode',
            'assessment_prompt',
            'student_name',
            'physical_score',
            'linguistic_score',
            'cognitive_score',
            'social_emotional_score',
            'feedback',
            'teacher_notes',
            'signed_by',
            'signed_by_name',
            'signed_at',
            'signature_hash',
            'changes_summary',
            'exported_at',
            'export_format',
            'created_at',
        ]
        read_only_fields = [
            'signed_at',
            'signature_hash',
            'exported_at',
            'created_at',
        ]


class ReportSummarySerializer(serializers.Serializer):
    """Serializer for report summary data (for lists)."""
    id = serializers.UUIDField()
    student_name = serializers.CharField()
    assessment_mode = serializers.CharField()
    overall_band = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    is_signed = serializers.BooleanField()
    
    def get_overall_band(self, obj):
        """Calculate overall band from strand scores."""
        from collections import Counter
        
        bands = []
        for strand in ['physical', 'linguistic', 'cognitive', 'social_emotional']:
            score = getattr(obj, f'{strand}_score', {})
            if isinstance(score, dict):
                bands.append(score.get('band', 'expected'))
        
        if bands:
            return Counter(bands).most_common(1)[0][0]
        return 'expected'
