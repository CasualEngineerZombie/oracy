"""
Views for the students app.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
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