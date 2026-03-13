"""
Serializers for the assessments app.
"""

from rest_framework import serializers

from apps.students.models import Student
from apps.students.serializers import StudentSerializer

from .models import Assessment, Recording


class RecordingSerializer(serializers.ModelSerializer):
    """Serializer for Recording model."""
    
    class Meta:
        model = Recording
        fields = [
            "id",
            "original_filename",
            "file_size_bytes",
            "duration_seconds",
            "video_quality_score",
            "audio_quality_score",
            "audio_extracted",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AssessmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing assessments (lightweight)."""
    
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    has_recording = serializers.BooleanField(read_only=True)
    has_draft_report = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Assessment
        fields = [
            "id",
            "student",
            "student_name",
            "mode",
            "prompt",
            "status",
            "status_message",
            "consent_obtained",
            "created_at",
            "has_recording",
            "has_draft_report",
        ]
        read_only_fields = ["id", "created_at", "status", "status_message"]


class AssessmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed assessment view."""
    
    student = StudentSerializer(read_only=True)
    recording = RecordingSerializer(read_only=True)
    
    class Meta:
        model = Assessment
        fields = [
            "id",
            "student",
            "cohort",
            "mode",
            "prompt",
            "time_limit_seconds",
            "consent_obtained",
            "consent_date",
            "status",
            "status_message",
            "recording",
            "created_at",
            "uploaded_at",
            "completed_at",
        ]
        read_only_fields = [
            "id", "created_at", "uploaded_at", "completed_at",
            "status", "status_message"
        ]


class AssessmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new assessment."""
    
    student_id = serializers.UUIDField(write_only=True)
    cohort_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Assessment
        fields = [
            "student_id",
            "cohort_id",
            "mode",
            "prompt",
            "time_limit_seconds",
            "consent_obtained",
        ]
    
    def validate_mode(self, value):
        """Validate mode is one of the allowed choices."""
        valid_modes = ["presenting", "explaining", "persuading"]
        if value not in valid_modes:
            raise serializers.ValidationError(
                f"Mode must be one of: {', '.join(valid_modes)}"
            )
        return value
    
    def validate_student_id(self, value):
        """Validate student exists."""
        try:
            Student.objects.get(id=value)
        except Student.DoesNotExist:
            raise serializers.ValidationError("Student not found")
        return value
    
    def create(self, validated_data):
        """Create assessment with proper relationships."""
        student_id = validated_data.pop("student_id")
        cohort_id = validated_data.pop("cohort_id")
        
        student = Student.objects.get(id=student_id)
        
        assessment = Assessment.objects.create(
            student=student,
            cohort_id=cohort_id,
            **validated_data
        )
        
        return assessment


class AssessmentBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating assessments for a cohort."""
    
    cohort_id = serializers.UUIDField()
    mode = serializers.ChoiceField(choices=["presenting", "explaining", "persuading"])
    prompt = serializers.CharField()
    time_limit_seconds = serializers.IntegerField(required=False, default=180)
    
    def validate_cohort_id(self, value):
        """Validate cohort exists."""
        from apps.students.models import Cohort
        try:
            Cohort.objects.get(id=value)
        except Cohort.DoesNotExist:
            raise serializers.ValidationError("Cohort not found")
        return value


class RecordingUploadSerializer(serializers.Serializer):
    """Serializer for uploading a recording."""
    
    file = serializers.FileField()
    
    def validate_file(self, value):
        """Validate file type and size."""
        # Check file type
        allowed_types = ['video/mp4', 'video/quicktime', 'video/x-msvideo']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"File type not supported. Allowed: {', '.join(allowed_types)}"
            )
        
        # Check file size (max 500MB)
        max_size = 500 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File too large. Maximum size: 500MB"
            )
        
        return value


class AssessmentStatusSerializer(serializers.ModelSerializer):
    """Serializer for assessment status updates."""
    
    class Meta:
        model = Assessment
        fields = ["status", "status_message"]
        read_only_fields = ["status", "status_message"]


class AssessmentSignOffSerializer(serializers.Serializer):
    """Serializer for signing off an assessment."""
    
    physical_band = serializers.ChoiceField(
        choices=[("emerging", "Emerging"), ("expected", "Expected"), ("exceeding", "Exceeding")]
    )
    linguistic_band = serializers.ChoiceField(
        choices=[("emerging", "Emerging"), ("expected", "Expected"), ("exceeding", "Exceeding")]
    )
    cognitive_band = serializers.ChoiceField(
        choices=[("emerging", "Emerging"), ("expected", "Expected"), ("exceeding", "Exceeding")]
    )
    social_emotional_band = serializers.ChoiceField(
        choices=[("emerging", "Emerging"), ("expected", "Expected"), ("exceeding", "Exceeding")]
    )
    
    physical_clips = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    linguistic_clips = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    cognitive_clips = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    social_emotional_clips = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    
    feedback_strengths = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    feedback_next_steps = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    feedback_goals = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    
    teacher_notes = serializers.CharField(required=False, allow_blank=True)


class PresignedURLSerializer(serializers.Serializer):
    """Serializer for generating presigned upload URLs."""
    
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    file_size = serializers.IntegerField(min_value=1, max_value=500 * 1024 * 1024)  # 500MB max
    
    def validate_content_type(self, value):
        """Validate content type is a supported video format."""
        allowed_types = ['video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo']
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"Invalid content type. Allowed: {', '.join(allowed_types)}"
            )
        return value


class PresignedURLResponseSerializer(serializers.Serializer):
    """Serializer for presigned URL response."""
    
    upload_url = serializers.URLField()
    file_key = serializers.CharField()
    assessment_id = serializers.CharField()
    expires_in = serializers.IntegerField()
