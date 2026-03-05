"""
Student services for the Oracy AI platform.

Following Django Styleguide - Services contain business logic for writing to the database.

Naming conventions:
- student_create(*, user_id: str, ...) -> Student
- student_update(*, student: Student, ...) -> Student
- cohort_create(*, name: str, ...) -> Cohort
- enrollment_create(*, student: Student, ...) -> Enrollment
"""

from typing import Optional

from django.db import transaction

from apps.audit.models import AuditLog

from .models import Cohort, Enrollment, Student


def student_create(
    *,
    user_id: str,
    student_id: str = "",
    year_group: int,
    eal_status: bool = False,
    sen_status: bool = False,
    created_by: Optional = None,
) -> Student:
    """
    Create a new student.
    
    Args:
        user_id: UUID of the associated user
        student_id: School-specific student ID
        year_group: Student's year group (1-13)
        eal_status: English as Additional Language status
        sen_status: Special Educational Needs status
        created_by: User who created the student
    
    Returns:
        The created Student instance
    """
    student = Student(
        user_id=user_id,
        student_id=student_id,
        year_group=year_group,
        eal_status=eal_status,
        sen_status=sen_status,
    )
    student.full_clean()
    student.save()
    
    if created_by:
        AuditLog.objects.create(
            action='student_created',
            user=created_by,
            object_type='Student',
            object_id=str(student.id),
            description=f'Student created: {student.user.get_full_name()}',
        )
    
    return student


def student_update(
    *,
    student: Student,
    year_group: Optional[int] = None,
    eal_status: Optional[bool] = None,
    sen_status: Optional[bool] = None,
) -> Student:
    """
    Update a student's data.
    
    Args:
        student: The student to update
        year_group: New year group (if provided)
        eal_status: New EAL status (if provided)
        sen_status: New SEN status (if provided)
    
    Returns:
        The updated Student instance
    """
    if year_group is not None:
        student.year_group = year_group
    if eal_status is not None:
        student.eal_status = eal_status
    if sen_status is not None:
        student.sen_status = sen_status
    
    student.full_clean()
    student.save()
    
    return student


@transaction.atomic
def cohort_create(
    *,
    name: str,
    teacher_id: str,
    year_group: int,
    academic_year: str,
    created_by: Optional = None,
) -> Cohort:
    """
    Create a new cohort.
    
    Args:
        name: Name of the cohort
        teacher_id: UUID of the assigned teacher
        year_group: Year group for the cohort
        academic_year: Academic year string (e.g., '2024-2025')
        created_by: User who created the cohort
    
    Returns:
        The created Cohort instance
    """
    cohort = Cohort(
        name=name,
        teacher_id=teacher_id,
        year_group=year_group,
        academic_year=academic_year,
    )
    cohort.full_clean()
    cohort.save()
    
    if created_by:
        AuditLog.objects.create(
            action='cohort_created',
            user=created_by,
            object_type='Cohort',
            object_id=str(cohort.id),
            description=f'Cohort created: {name}',
        )
    
    return cohort


@transaction.atomic
def enrollment_create(
    *,
    student: Student,
    cohort: Cohort,
    enrolled_by: Optional = None,
) -> Enrollment:
    """
    Enroll a student in a cohort.
    
    Args:
        student: The student to enroll
        cohort: The cohort to enroll in
        enrolled_by: User who performed the enrollment
    
    Returns:
        The created Enrollment instance
    
    Raises:
        ValueError: If student is already enrolled in the cohort
    """
    # Check if already enrolled
    if Enrollment.objects.filter(student=student, cohort=cohort).exists():
        raise ValueError(f"Student {student.id} is already enrolled in cohort {cohort.id}")
    
    enrollment = Enrollment.objects.create(
        student=student,
        cohort=cohort,
    )
    
    if enrolled_by:
        AuditLog.objects.create(
            action='student_enrolled',
            user=enrolled_by,
            object_type='Enrollment',
            object_id=str(enrollment.id),
            description=f'Student {student.user.get_full_name()} enrolled in {cohort.name}',
        )
    
    return enrollment
