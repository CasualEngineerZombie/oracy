"""
Report selectors for the Oracy AI platform.

Following Django Styleguide - Selectors contain business logic for fetching from the database.

Naming conventions:
- draft_report_get(*, draft_id: str) -> Optional[DraftReport]
- draft_report_list(*, filters: dict) -> QuerySet[DraftReport]
- signed_report_get(*, report_id: str) -> Optional[SignedReport]
- signed_report_list(*, filters: dict) -> QuerySet[SignedReport]
"""

from typing import Optional

from django.db.models import QuerySet

from .models import DraftReport, SignedReport


def draft_report_get(*, draft_id: str) -> Optional[DraftReport]:
    """
    Get a draft report by ID.
    
    Args:
        draft_id: The UUID of the draft report
    
    Returns:
        DraftReport if found, None otherwise
    """
    try:
        return DraftReport.objects.get(id=draft_id)
    except DraftReport.DoesNotExist:
        return None


def draft_report_list(
    *,
    assessment_id: Optional[str] = None,
    is_reviewed: Optional[bool] = None,
    reviewed_by_id: Optional[str] = None,
) -> QuerySet[DraftReport]:
    """
    List draft reports with optional filtering.
    
    Args:
        assessment_id: Filter by assessment
        is_reviewed: Filter by review status
        reviewed_by_id: Filter by reviewer
    
    Returns:
        QuerySet of draft reports
    """
    queryset = DraftReport.objects.all()
    
    if assessment_id:
        queryset = queryset.filter(assessment_id=assessment_id)
    if is_reviewed is not None:
        queryset = queryset.filter(is_reviewed=is_reviewed)
    if reviewed_by_id:
        queryset = queryset.filter(reviewed_by_id=reviewed_by_id)
    
    return queryset


def draft_report_list_for_teacher(*, teacher_id: str) -> QuerySet[DraftReport]:
    """
    List draft reports for a teacher's cohorts.
    
    Args:
        teacher_id: UUID of the teacher
    
    Returns:
        QuerySet of draft reports
    """
    return DraftReport.objects.filter(
        assessment__cohort__teacher_id=teacher_id
    )


def signed_report_get(*, report_id: str) -> Optional[SignedReport]:
    """
    Get a signed report by ID.
    
    Args:
        report_id: The UUID of the signed report
    
    Returns:
        SignedReport if found, None otherwise
    """
    try:
        return SignedReport.objects.get(id=report_id)
    except SignedReport.DoesNotExist:
        return None


def signed_report_list(
    *,
    assessment_id: Optional[str] = None,
    signed_by_id: Optional[str] = None,
    student_id: Optional[str] = None,
) -> QuerySet[SignedReport]:
    """
    List signed reports with optional filtering.
    
    Args:
        assessment_id: Filter by assessment
        signed_by_id: Filter by signer
        student_id: Filter by student
    
    Returns:
        QuerySet of signed reports
    """
    queryset = SignedReport.objects.all()
    
    if assessment_id:
        queryset = queryset.filter(assessment_id=assessment_id)
    if signed_by_id:
        queryset = queryset.filter(signed_by_id=signed_by_id)
    if student_id:
        queryset = queryset.filter(assessment__student_id=student_id)
    
    return queryset


def signed_report_list_for_teacher(*, teacher_id: str) -> QuerySet[SignedReport]:
    """
    List signed reports for a teacher's cohorts.
    
    Args:
        teacher_id: UUID of the teacher
    
    Returns:
        QuerySet of signed reports
    """
    return SignedReport.objects.filter(
        assessment__cohort__teacher_id=teacher_id
    )


def signed_report_list_for_student(*, student_id: str) -> QuerySet[SignedReport]:
    """
    List signed reports for a specific student.
    
    Args:
        student_id: UUID of the student
    
    Returns:
        QuerySet of signed reports
    """
    return SignedReport.objects.filter(
        assessment__student_id=student_id
    )


def signed_report_get_for_assessment(*, assessment_id: str) -> Optional[SignedReport]:
    """
    Get the signed report for a specific assessment.
    
    Args:
        assessment_id: UUID of the assessment
    
    Returns:
        SignedReport if found, None otherwise
    """
    try:
        return SignedReport.objects.get(assessment_id=assessment_id)
    except SignedReport.DoesNotExist:
        return None
