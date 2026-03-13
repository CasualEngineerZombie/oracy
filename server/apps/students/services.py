"""
Student services for the Oracy AI platform.

Following Django Styleguide - Services contain business logic for writing to the database.

Naming conventions:
- student_create(*, user_id: str, ...) -> Student
- student_update(*, student: Student, ...) -> Student
- cohort_create(*, name: str, ...) -> Cohort
- enrollment_create(*, student: Student, ...) -> Enrollment
"""

import csv
import io
from datetime import datetime
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.users.models import User

from .models import Cohort, Enrollment, Student


def calculate_age_band(date_of_birth: datetime.date, academic_year: str = None) -> str:
    """
    Calculate age band based on date of birth and academic year.
    
    UK academic year starts September 1. Age bands:
    - 8-9: Year 4 (ages 8-9)
    - 9-10: Year 5 (ages 9-10)
    - 10-11: Year 6 (ages 10-11)
    - 11-12: Year 7 (ages 11-12)
    - 12-13: Year 8 (ages 12-13)
    - 13-14: Year 9 (ages 13-14)
    - 14-15: Year 10 (ages 14-15)
    - 15-16: Year 11 (ages 15-16)
    - 16-18: Year 12-13 (ages 16-18)
    
    Args:
        date_of_birth: Student's date of birth
        academic_year: Academic year in format '2025-2026'
    
    Returns:
        Age band string (e.g., '11-12')
    """
    if not date_of_birth:
        return "11-12"  # Default
    
    # Parse academic year to get the September 1 cutoff
    if academic_year:
        try:
            year_start = int(academic_year.split('-')[0])
        except (ValueError, IndexError):
            year_start = datetime.now().year
    else:
        year_start = datetime.now().year
    
    # Calculate age as of September 1 of the academic year start
    cutoff_date = datetime(year_start, 9, 1).date()
    
    # If birthday is after September 1, they're one year younger
    if date_of_birth.month > 9 or (date_of_birth.month == 9 and date_of_birth.day > 1):
        age = year_start - date_of_birth.year - 1
    else:
        age = year_start - date_of_birth.year
    
    # Map age to age band
    if age <= 9:
        return "8-9"
    elif age <= 10:
        return "9-10"
    elif age <= 11:
        return "10-11"
    elif age <= 12:
        return "11-12"
    elif age <= 13:
        return "12-13"
    elif age <= 14:
        return "13-14"
    elif age <= 15:
        return "14-15"
    elif age <= 16:
        return "15-16"
    else:
        return "16-18"


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


class CSVImportResult:
    """Result of a CSV import operation."""
    
    def __init__(self):
        self.created = []
        self.updated = []
        self.errors = []
        self.skipped = []
    
    @property
    def success_count(self) -> int:
        return len(self.created) + len(self.updated)
    
    @property
    def error_count(self) -> int:
        return len(self.errors) + len(self.skipped)
    
    def to_dict(self) -> dict:
        return {
            "created": self.created,
            "updated": self.updated,
            "errors": self.errors,
            "skipped": self.skipped,
            "summary": {
                "total_created": len(self.created),
                "total_updated": len(self.updated),
                "total_errors": self.error_count,
            }
        }


def students_bulk_import(
    csv_content: str,
    cohort: Cohort = None,
    created_by: User = None,
    academic_year: str = None,
) -> CSVImportResult:
    """
    Import students from CSV content.
    
    Expected CSV columns:
    - student_id: School-specific ID (required)
    - first_name: Student's first name (required)
    - last_name: Student's last name (required)
    - email: Student's email address (required)
    - date_of_birth: Date in YYYY-MM-DD format (optional)
    - year_group: Year group number (optional, e.g., 7)
    - eal: Boolean for English as Additional Language (optional, defaults to false)
    
    Args:
        csv_content: CSV file content as string
        cohort: Optional cohort to enroll students into
        created_by: User performing the import
        academic_year: Academic year for age band calculation
    
    Returns:
        CSVImportResult with details of imported students
    """
    result = CSVImportResult()
    
    # Parse CSV
    try:
        reader = csv.DictReader(io.StringIO(csv_content))
    except Exception as e:
        result.errors.append(f"Failed to parse CSV: {str(e)}")
        return result
    
    # Validate headers
    required_columns = ['student_id', 'first_name', 'last_name', 'email']
    if reader.fieldnames:
        missing = [col for col in required_columns if col not in reader.fieldnames]
        if missing:
            result.errors.append(f"Missing required columns: {', '.join(missing)}")
            return result
    else:
        result.errors.append("Could not read CSV headers")
        return result
    
    # Process each row
    for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
        try:
            # Validate required fields
            student_id = row.get('student_id', '').strip()
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            email = row.get('email', '').strip()
            
            if not student_id:
                result.skipped.append({
                    "row": row_num,
                    "reason": "Missing student_id"
                })
                continue
            
            if not first_name or not last_name:
                result.skipped.append({
                    "row": row_num,
                    "student_id": student_id,
                    "reason": "Missing first_name or last_name"
                })
                continue
            
            if not email:
                result.skipped.append({
                    "row": row_num,
                    "student_id": student_id,
                    "reason": "Missing email"
                })
                continue
            
            # Parse optional fields
            date_of_birth = None
            dob_str = row.get('date_of_birth', '').strip()
            if dob_str:
                try:
                    date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    result.skipped.append({
                        "row": row_num,
                        "student_id": student_id,
                        "reason": f"Invalid date format: {dob_str}. Use YYYY-MM-DD"
                    })
                    continue
            
            year_group = row.get('year_group', '').strip()
            if year_group:
                try:
                    year_group = int(year_group)
                except ValueError:
                    year_group = 7  # Default
            else:
                year_group = 7  # Default
            
            eal = row.get('eal', '').strip().lower() in ['true', '1', 'yes', 'y']
            
            # Calculate age band
            age_band = calculate_age_band(date_of_birth, academic_year)
            
            # Check if user already exists
            existing_user = None
            existing_student = None
            
            if User.objects.filter(email__iexact=email).exists():
                existing_user = User.objects.get(email__iexact=email)
                if hasattr(existing_user, 'student_profile'):
                    existing_student = existing_user.student_profile
            
            if existing_student:
                # Update existing student
                existing_student.student_id = student_id
                existing_student.date_of_birth = date_of_birth
                existing_student.year_group = str(year_group)
                existing_student.age_band = age_band
                existing_student.eal = eal
                existing_student.save()
                
                result.updated.append({
                    "row": row_num,
                    "student_id": student_id,
                    "name": f"{first_name} {last_name}",
                    "action": "updated"
                })
            else:
                # Create new user and student
                # Generate username from email or first/last name
                username = email.split('@')[0] if '@' in email else f"{first_name.lower()}.{last_name.lower()}"
                
                # Ensure unique username
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=User.objects.make_random_password(),  # Generate random password
                    first_name=first_name,
                    last_name=last_name,
                    role='student',
                )
                
                # Create student profile
                student = Student.objects.create(
                    user=user,
                    student_id=student_id,
                    date_of_birth=date_of_birth,
                    year_group=str(year_group),
                    age_band=age_band,
                    eal=eal,
                )
                
                result.created.append({
                    "row": row_num,
                    "student_id": student_id,
                    "name": f"{first_name} {last_name}",
                    "action": "created"
                })
            
            # Enroll in cohort if provided
            if cohort and existing_student:
                if not Enrollment.objects.filter(student=existing_student, cohort=cohort).exists():
                    Enrollment.objects.create(student=existing_student, cohort=cohort)
            elif cohort:
                # Get the student we just created
                student = Student.objects.get(student_id=student_id)
                if not Enrollment.objects.filter(student=student, cohort=cohort).exists():
                    Enrollment.objects.create(student=student, cohort=cohort)
            
        except Exception as e:
            result.errors.append({
                "row": row_num,
                "student_id": row.get('student_id', 'unknown'),
                "reason": str(e)
            })
    
    # Log the import
    if created_by:
        AuditLog.objects.create(
            action='students_bulk_import',
            user=created_by,
            object_type='BulkImport',
            object_id=str(int(timezone.now().timestamp())),
            description=f'Bulk imported {result.success_count} students ({len(result.created)} created, {len(result.updated)} updated)',
        )
    
    return result


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
