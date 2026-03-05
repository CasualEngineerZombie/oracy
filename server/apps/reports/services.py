"""
Report services for the Oracy AI platform.

Following Django Styleguide - Services contain business logic for writing to the database.

Naming conventions:
- draft_report_get(*, draft_id: str) -> Optional[DraftReport]
- draft_report_update(*, draft: DraftReport, ...) -> DraftReport
- signed_report_create(*, draft: DraftReport, ...) -> SignedReport
- signed_report_generate_pdf(*, report: SignedReport, ...) -> bytes
"""

import logging
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.core.permissions import IsTeacherOfStudent
from apps.reports.services.pdf_export import PDFExportService

from .models import DraftReport, SignedReport

logger = logging.getLogger(__name__)


def draft_report_get(*, draft_id: str) -> Optional[DraftReport]:
    """
    Get a draft report by ID.
    
    Args:
        draft_id: UUID of the draft report
    
    Returns:
        DraftReport if found, None otherwise
    """
    try:
        return DraftReport.objects.get(id=draft_id)
    except DraftReport.DoesNotExist:
        return None


def signed_report_get(*, report_id: str) -> Optional[SignedReport]:
    """
    Get a signed report by ID.
    
    Args:
        report_id: UUID of the signed report
    
    Returns:
        SignedReport if found, None otherwise
    """
    try:
        return SignedReport.objects.get(id=report_id)
    except SignedReport.DoesNotExist:
        return None


def _calculate_changes(draft: DraftReport, modifications: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate the changes summary between draft and modifications.
    
    Args:
        draft: The original draft report
        modifications: Dictionary of modified fields
    
    Returns:
        Dictionary describing changes
    """
    changes = {}
    
    for field_name, new_value in modifications.items():
        old_value = getattr(draft, field_name)
        if old_value != new_value:
            changes[field_name] = {
                'old': old_value,
                'new': new_value,
            }
    
    return changes


@transaction.atomic
def signed_report_create_from_draft(
    *,
    draft: DraftReport,
    signed_by,
    modifications: Optional[Dict[str, Any]] = None,
    teacher_notes: str = "",
) -> SignedReport:
    """
    Create a signed report from a draft report.
    
    This handles the sign-off process, including applying modifications
    and calculating a changes summary.
    
    Args:
        draft: The draft report to sign off
        signed_by: User signing off the report
        modifications: Optional dictionary of score/feedback modifications
        teacher_notes: Optional private notes from the teacher
    
    Returns:
        The created SignedReport instance
    """
    modifications = modifications or {}
    
    # Calculate changes summary
    changes_summary = _calculate_changes(draft, modifications)
    
    # Prepare signed report data
    signed_data = {
        'assessment': draft.assessment,
        'draft_report': draft,
        'signed_by': signed_by,
        'signed_at': timezone.now(),
        'teacher_notes': teacher_notes,
        'changes_summary': changes_summary,
    }
    
    # Apply scores (modified or draft)
    for strand in ['physical', 'linguistic', 'cognitive', 'social_emotional']:
        field_name = f'{strand}_score'
        if field_name in modifications:
            signed_data[field_name] = modifications[field_name]
        else:
            signed_data[field_name] = getattr(draft, field_name)
    
    # Apply feedback (modified or draft)
    if 'feedback' in modifications:
        signed_data['feedback'] = modifications['feedback']
    else:
        signed_data['feedback'] = draft.feedback
    
    # Create the signed report
    signed_report = SignedReport.objects.create(**signed_data)
    
    # Update draft status
    draft.is_reviewed = True
    draft.reviewed_by = signed_by
    draft.reviewed_at = timezone.now()
    draft.save()
    
    # Update assessment status
    assessment = draft.assessment
    assessment.status = 'signed_off'
    assessment.save()
    
    # Log the sign-off
    AuditLog.objects.create(
        action='report_signed_off',
        user=signed_by,
        object_type='SignedReport',
        object_id=str(signed_report.id),
        description=f'Report signed off for assessment {assessment.id}',
        metadata={
            'draft_id': str(draft.id),
            'has_modifications': bool(changes_summary),
        }
    )
    
    return signed_report


def signed_report_generate_pdf(
    *,
    report: SignedReport,
    include_evidence: bool = True,
    simplified: bool = False,
) -> bytes:
    """
    Generate a PDF for a signed report.
    
    Args:
        report: The signed report to generate PDF for
        include_evidence: Whether to include evidence clips
        simplified: Whether to generate parent-friendly version
    
    Returns:
        PDF content as bytes
    """
    service = PDFExportService()
    pdf_buffer = service.generate_assessment_report(
        report=report,
        include_evidence=include_evidence,
        simplified=simplified,
    )
    
    return pdf_buffer.getvalue()


def signed_report_mark_exported(
    *,
    report: SignedReport,
    exported_by,
    export_format: str = 'pdf',
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Mark a signed report as exported.
    
    Args:
        report: The signed report
        exported_by: User who exported the report
        export_format: Format of export (e.g., 'pdf')
        metadata: Optional export metadata
    """
    # Update export tracking
    report.exported_at = timezone.now()
    report.export_format = export_format
    report.save(update_fields=['exported_at', 'export_format'])
    
    # Log export
    AuditLog.objects.create(
        action='export_generated',
        user=exported_by,
        object_type='SignedReport',
        object_id=str(report.id),
        description=f'PDF export generated ({export_format})',
        metadata=metadata or {},
    )
