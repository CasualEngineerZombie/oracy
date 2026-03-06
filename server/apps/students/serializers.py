"""
Serializers for the students app.
"""

from rest_framework import serializers

from apps.users.serializers import UserSerializer

from .models import Cohort, Enrollment, Student


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model."""
    
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    
    class Meta:
        model = Student
        fields = [
            "id",
            "user",
            "full_name",
            "email",
            "student_id",
            "date_of_birth",
            "year_group",
            "age_band",
            "eal",
            "first_language",
            "accommodations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a student."""
    
    user_id = serializers.UUIDField()
    
    class Meta:
        model = Student
        fields = [
            "user_id",
            "student_id",
            "date_of_birth",
            "year_group",
            "age_band",
            "eal",
            "first_language",
            "accommodations",
        ]


class CohortSerializer(serializers.ModelSerializer):
    """Serializer for Cohort model."""
    
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cohort
        fields = [
            "id",
            "name",
            "teacher",
            "teacher_name",
            "year_group",
            "academic_year",
            "students",
            "student_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_student_count(self, obj):
        return obj.students.count()


class CohortCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a cohort."""
    
    class Meta:
        model = Cohort
        fields = [
            "name",
            "teacher",
            "year_group",
            "academic_year",
        ]


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model."""
    
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    cohort_name = serializers.CharField(source="cohort.name", read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_name",
            "cohort",
            "cohort_name",
            "enrolled_at",
            "withdrawn_at",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "enrolled_at", "created_at"]


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for student lists."""
    
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    cohorts = CohortSerializer(many=True, read_only=True)
    
    class Meta:
        model = Student
        fields = [
            "id",
            "full_name",
            "student_id",
            "year_group",
            "age_band",
            "eal",
            "cohorts",
        ]