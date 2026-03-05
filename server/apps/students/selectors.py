"""
Student selectors for the Oracy AI platform.

Following Django Styleguide - Selectors contain business logic for fetching from the database.

Naming conventions:
- student_get(*, student_id: str) -> Optional[Student]
- student_list(*, filters: dict) -> QuerySet[Student]
- cohort_get(*, cohort_id: str) -> Optional[Cohort]
- cohort_list(*, filters: dict) -> QuerySet[Cohort]
"""

from typing import Optional

from django.db.models import QuerySet

from .models import Cohort, Enrollment, Student


def student_get(*, student_id: str) -> Optional[Student]:
    """
    Get a student by ID.
    
    Args:
        student_id: The UUID of the student
    
    Returns:
        Student if found, None otherwise
    """
    try:
        return Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return None


def student_get_by_user(*, user_id: str) -> Optional[Student]:
    """
    Get a student by user ID.
    
    Args:
        user_id: The UUID of the user
    
    Returns:
        Student if found, None otherwise
    """
    try:
        return Student.objects.get(user_id=user_id)
    except Student.DoesNotExist:
        return None


def student_list(
    *,
    year_group: Optional[int] = None,
    eal_status: Optional[bool] = None,
    sen_status: Optional[bool] = None,
    school_id: Optional[str] = None,
) -> QuerySet[Student]:
    """
    List students with optional filtering.
    
    Args:
        year_group: Filter by year group
        eal_status: Filter by EAL status
        sen_status: Filter by SEN status
        school_id: Filter by school
    
    Returns:
        QuerySet of students
    """
    queryset = Student.objects.all()
    
    if year_group:
        queryset = queryset.filter(year_group=year_group)
    if eal_status is not None:
        queryset = queryset.filter(eal_status=eal_status)
    if sen_status is not None:
        queryset = queryset.filter(sen_status=sen_status)
    if school_id:
        queryset = queryset.filter(user__school_id=school_id)
    
    return queryset


def student_list_for_teacher(*, teacher_id: str) -> QuerySet[Student]:
    """
    List all students enrolled in a teacher's cohorts.
    
    Args:
        teacher_id: UUID of the teacher
    
    Returns:
        QuerySet of students
    """
    return Student.objects.filter(
        cohorts__teacher_id=teacher_id
    ).distinct()


def student_list_for_cohort(*, cohort_id: str) -> QuerySet[Student]:
    """
    List all students in a specific cohort.
    
    Args:
        cohort_id: UUID of the cohort
    
    Returns:
        QuerySet of students
    """
    return Student.objects.filter(
        enrollments__cohort_id=cohort_id
    )


def cohort_get(*, cohort_id: str) -> Optional[Cohort]:
    """
    Get a cohort by ID.
    
    Args:
        cohort_id: The UUID of the cohort
    
    Returns:
        Cohort if found, None otherwise
    """
    try:
        return Cohort.objects.get(id=cohort_id)
    except Cohort.DoesNotExist:
        return None


def cohort_list(
    *,
    teacher_id: Optional[str] = None,
    year_group: Optional[int] = None,
    academic_year: Optional[str] = None,
) -> QuerySet[Cohort]:
    """
    List cohorts with optional filtering.
    
    Args:
        teacher_id: Filter by teacher
        year_group: Filter by year group
        academic_year: Filter by academic year
    
    Returns:
        QuerySet of cohorts
    """
    queryset = Cohort.objects.all()
    
    if teacher_id:
        queryset = queryset.filter(teacher_id=teacher_id)
    if year_group:
        queryset = queryset.filter(year_group=year_group)
    if academic_year:
        queryset = queryset.filter(academic_year=academic_year)
    
    return queryset


def enrollment_exists(*, student_id: str, cohort_id: str) -> bool:
    """
    Check if a student is enrolled in a cohort.
    
    Args:
        student_id: UUID of the student
        cohort_id: UUID of the cohort
    
    Returns:
        True if enrollment exists, False otherwise
    """
    return Enrollment.objects.filter(
        student_id=student_id,
        cohort_id=cohort_id
    ).exists()
