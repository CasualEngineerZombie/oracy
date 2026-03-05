"""
Assessment selectors for the Oracy AI platform.

Following Django Styleguide - Selectors contain business logic for fetching from the database.

Naming conventions:
- assessment_get(*, assessment_id: str) -> Optional[Assessment]
- assessment_list(*, filters: dict) -> QuerySet[Assessment]
- assessment_list_for_teacher(*, teacher_id: str) -> QuerySet[Assessment]
- recording_get(*, recording_id: str) -> Optional[Recording]
"""

from typing import Optional

from django.db.models import Prefetch, QuerySet

from .models import Assessment, Recording


def assessment_get(*, assessment_id: str) -> Optional[Assessment]:
    """
    Get an assessment by ID.
    
    Args:
        assessment_id: The UUID of the assessment
    
    Returns:
        Assessment if found, None otherwise
    """
    try:
        return Assessment.objects.get(id=assessment_id)
    except Assessment.DoesNotExist:
        return None


def assessment_get_with_recording(*, assessment_id: str) -> Optional[Assessment]:
    """
    Get an assessment by ID with recording prefetched.
    
    Args:
        assessment_id: The UUID of the assessment
    
    Returns:
        Assessment if found, None otherwise
    """
    try:
        return Assessment.objects.select_related('recording').get(id=assessment_id)
    except Assessment.DoesNotExist:
        return None


def assessment_list(
    *,
    status: Optional[str] = None,
    student_id: Optional[str] = None,
    cohort_id: Optional[str] = None,
    mode: Optional[str] = None,
) -> QuerySet[Assessment]:
    """
    List assessments with optional filtering.
    
    Args:
        status: Filter by status
        student_id: Filter by student
        cohort_id: Filter by cohort
        mode: Filter by assessment mode
    
    Returns:
        QuerySet of assessments
    """
    queryset = Assessment.objects.all()
    
    if status:
        queryset = queryset.filter(status=status)
    if student_id:
        queryset = queryset.filter(student_id=student_id)
    if cohort_id:
        queryset = queryset.filter(cohort_id=cohort_id)
    if mode:
        queryset = queryset.filter(mode=mode)
    
    return queryset


def assessment_list_for_teacher(*, teacher_id: str) -> QuerySet[Assessment]:
    """
    List all assessments for a teacher's cohorts.
    
    Args:
        teacher_id: UUID of the teacher
    
    Returns:
        QuerySet of assessments
    """
    return Assessment.objects.filter(cohort__teacher_id=teacher_id)


def assessment_list_for_student(*, student_id: str) -> QuerySet[Assessment]:
    """
    List all assessments for a specific student.
    
    Args:
        student_id: UUID of the student
    
    Returns:
        QuerySet of assessments
    """
    return Assessment.objects.filter(student_id=student_id)


def assessment_list_pending_processing() -> QuerySet[Assessment]:
    """
    List all assessments that are ready for processing.
    
    Returns:
        QuerySet of assessments in uploading or error state
    """
    return Assessment.objects.filter(status__in=['uploading', 'error'])


def assessment_list_with_drafts(*, teacher_id: Optional[str] = None) -> QuerySet[Assessment]:
    """
    List assessments that have draft reports ready.
    
    Args:
        teacher_id: Optional teacher filter
    
    Returns:
        QuerySet of assessments with drafts
    """
    queryset = Assessment.objects.filter(
        status__in=['draft_ready', 'under_review']
    ).select_related('draft_report')
    
    if teacher_id:
        queryset = queryset.filter(cohort__teacher_id=teacher_id)
    
    return queryset


def recording_get(*, recording_id: str) -> Optional[Recording]:
    """
    Get a recording by ID.
    
    Args:
        recording_id: UUID of the recording
    
    Returns:
        Recording if found, None otherwise
    """
    try:
        return Recording.objects.get(id=recording_id)
    except Recording.DoesNotExist:
        return None


def recording_get_by_assessment(*, assessment_id: str) -> Optional[Recording]:
    """
    Get the recording for a specific assessment.
    
    Args:
        assessment_id: UUID of the assessment
    
    Returns:
        Recording if found, None otherwise
    """
    try:
        return Recording.objects.get(assessment_id=assessment_id)
    except Recording.DoesNotExist:
        return None
