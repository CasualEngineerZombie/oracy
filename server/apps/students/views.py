"""
Views for the students app.
"""

import csv
import io

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from apps.core.permissions import IsAdmin, IsAdminOrTeacher

from .models import Cohort, Enrollment, Student
from .serializers import (
    CohortCreateSerializer,
    CohortSerializer,
    EnrollmentSerializer,
    StudentCreateSerializer,
    StudentListSerializer,
    StudentSerializer,
)
from .services import CSVImportResult, students_bulk_import


class StudentViewSet(viewsets.ModelViewSet):
    """ViewSet for student management."""
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == "admin":
            return Student.objects.all()
        elif user.role == "teacher":
            # Teachers see students in their cohorts
            return Student.objects.filter(cohorts__teacher=user).distinct()
        else:
            # Students see only themselves
            return Student.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == "create":
            return StudentCreateSerializer
        elif self.action == "list":
            return StudentListSerializer
        return StudentSerializer
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        
        if self.action in ["create", "destroy"]:
            return [IsAdminOrTeacher()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=["get"])
    def assessments(self, request, pk=None):
        """Get all assessments for a student."""
        student = self.get_object()
        assessments = student.assessments.all()
        
        from apps.assessments.serializers import AssessmentListSerializer
        serializer = AssessmentListSerializer(assessments, many=True)
        return Response(serializer.data)
    
    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
    )
    def bulk_import(self, request):
        """
        Bulk import students from CSV file.
        
        Expected CSV columns:
        - student_id: School-specific ID (required)
        - first_name: Student's first name (required)
        - last_name: Student's last name (required)
        - email: Student's email address (required)
        - date_of_birth: Date in YYYY-MM-DD format (optional)
        - year_group: Year group number (optional, e.g., 7)
        - eal: Boolean for English as Additional Language (optional)
        
        Request parameters:
        - file: CSV file (multipart/form-data)
        - cohort_id: Optional cohort ID to enroll students into
        - academic_year: Academic year for age band calculation (e.g., '2025-2026')
        """
        # Check if file is provided
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        if not file_obj.name.endswith('.csv'):
            return Response(
                {"error": "File must be a CSV"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional parameters
        cohort_id = request.data.get('cohort_id')
        academic_year = request.data.get('academic_year')
        
        # Get cohort if provided
        cohort = None
        if cohort_id:
            try:
                cohort = Cohort.objects.get(id=cohort_id)
            except Cohort.DoesNotExist:
                return Response(
                    {"error": "Cohort not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Read CSV content
        try:
            csv_content = file_obj.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response(
                {"error": "File must be UTF-8 encoded"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Import students
        result = students_bulk_import(
            csv_content=csv_content,
            cohort=cohort,
            created_by=request.user,
            academic_year=academic_year,
        )
        
        return Response(result.to_dict(), status=status.HTTP_200_OK)


class CohortViewSet(viewsets.ModelViewSet):
    """ViewSet for cohort management."""
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == "admin":
            return Cohort.objects.all()
        elif user.role == "teacher":
            return Cohort.objects.filter(teacher=user)
        else:
            # Students see cohorts they're enrolled in
            return Cohort.objects.filter(students__user=user)
    
    def get_serializer_class(self):
        if self.action == "create":
            return CohortCreateSerializer
        return CohortSerializer
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        
        if self.action in ["create", "destroy"]:
            return [IsAdminOrTeacher()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=["post"])
    def add_student(self, request, pk=None):
        """Add a student to the cohort."""
        cohort = self.get_object()
        student_id = request.data.get("student_id")
        
        if not student_id:
            return Response(
                {"error": "student_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = Student.objects.get(id=student_id)
            cohort.students.add(student)
            return Response({"message": "Student added to cohort"})
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=["post"])
    def remove_student(self, request, pk=None):
        """Remove a student from the cohort."""
        cohort = self.get_object()
        student_id = request.data.get("student_id")
        
        if not student_id:
            return Response(
                {"error": "student_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = Student.objects.get(id=student_id)
            cohort.students.remove(student)
            return Response({"message": "Student removed from cohort"})
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )