"""
Assessment services for the Oracy AI platform.

Following Django Styleguide - Services contain business logic for writing to the database.

Naming conventions:
- assessment_create(*, student_id: str, ...) -> Assessment
- assessment_update(*, assessment: Assessment, ...) -> Assessment
- assessment_upload_recording(*, assessment: Assessment, ...) -> Recording
- assessment_start_processing(*, assessment: Assessment) -> None
- assessment_sign_off(*, assessment: Assessment, ...) -> SignedReport
"""

import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.reports.models import DraftReport, SignedReport

from .models import Assessment, Recording

logger = logging.getLogger(__name__)


def assessment_create(
    *,
    student_id: str,
    cohort_id: str,
    mode: str,
    prompt: str,
    time_limit_seconds: int = 180,
    created_by: Optional[settings.AUTH_USER_MODEL] = None,
) -> Assessment:
    """
    Create a new assessment.
    
    Args:
        student_id: UUID of the student
        cohort_id: UUID of the cohort
        mode: Assessment mode (presenting, explaining, persuading)
        prompt: The prompt or topic given to the student
        time_limit_seconds: Time limit in seconds (30-600)
        created_by: User who created the assessment
    
    Returns:
        The created Assessment instance
    """
    assessment = Assessment(
        student_id=student_id,
        cohort_id=cohort_id,
        mode=mode,
        prompt=prompt,
        time_limit_seconds=time_limit_seconds,
    )
    assessment.full_clean()
    assessment.save()
    
    # Log creation
    if created_by:
        AuditLog.log_assessment_creation(created_by, assessment)
    
    return assessment


@transaction.atomic
def assessment_upload_recording(
    *,
    assessment: Assessment,
    uploaded_file: UploadedFile,
    uploaded_by: settings.AUTH_USER_MODEL,
) -> Recording:
    """
    Upload a recording for an assessment.
    
    Args:
        assessment: The assessment to upload recording for
        uploaded_file: The uploaded video file
        uploaded_by: User uploading the file
    
    Returns:
        The created Recording instance
    
    Raises:
        ValueError: If assessment is not in valid state for upload
        ClientError: If S3 upload fails
    """
    # Validate assessment state
    if assessment.status not in ["pending", "uploading"]:
        raise ValueError(
            f"Assessment is not in a valid state for upload. Current status: {assessment.status}"
        )
    
    # Generate S3 key
    s3_key = f"recordings/{assessment.id}/{uploaded_file.name}"
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    
    # Upload to S3
    s3 = boto3.client("s3")
    s3.upload_fileobj(
        uploaded_file,
        bucket,
        s3_key,
        ExtraArgs={
            "ContentType": uploaded_file.content_type,
        }
    )
    
    # Create recording record
    recording = Recording.objects.create(
        assessment=assessment,
        original_filename=uploaded_file.name,
        file_size_bytes=uploaded_file.size,
        s3_bucket=bucket,
        s3_key=s3_key,
    )
    
    # Update assessment status
    assessment.status = "uploading"
    assessment.uploaded_at = timezone.now()
    assessment.save()
    
    # Log upload
    AuditLog.objects.create(
        action="assessment_uploaded",
        user=uploaded_by,
        object_type="Assessment",
        object_id=str(assessment.id),
        description=f"Recording uploaded: {uploaded_file.name}",
    )
    
    return recording


def assessment_start_processing(
    *,
    assessment: Assessment,
    started_by: settings.AUTH_USER_MODEL,
) -> None:
    """
    Start processing an assessment through the AI pipeline.
    
    Args:
        assessment: The assessment to process
        started_by: User who started processing
    
    Raises:
        ValueError: If assessment is not in valid state for processing
        ValueError: If no recording is uploaded
    """
    # Validate assessment state
    if assessment.status not in ["uploading", "error"]:
        raise ValueError(
            f"Cannot start processing from status: {assessment.status}"
        )
    
    # Check for recording
    if not assessment.has_recording:
        raise ValueError("No recording uploaded")
    
    # Start async processing
    from apps.analysis.tasks import process_assessment
    process_assessment.delay(str(assessment.id))
    
    # Update status
    assessment.status = "processing"
    assessment.save()


def assessment_mark_error(
    *,
    assessment: Assessment,
    error_message: str,
) -> None:
    """
    Mark an assessment as having an error.
    
    Args:
        assessment: The assessment to mark
        error_message: Description of the error
    """
    assessment.status = "error"
    assessment.status_message = error_message
    assessment.save()


def assessment_mark_draft_ready(
    *,
    assessment: Assessment,
    draft_report: DraftReport,
) -> None:
    """
    Mark an assessment as draft ready.
    
    Args:
        assessment: The assessment
        draft_report: The generated draft report
    """
    assessment.status = "draft_ready"
    assessment.completed_at = timezone.now()
    assessment.save()


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


def assessment_update_consent(
    *,
    assessment: Assessment,
    consent_obtained: bool,
    updated_by,
) -> None:
    """
    Update consent status for an assessment.
    
    Args:
        assessment: The assessment to update
        consent_obtained: Whether consent is obtained
        updated_by: User updating the consent
    """
    assessment.consent_obtained = consent_obtained
    if consent_obtained:
        assessment.consent_date = timezone.now()
    else:
        assessment.consent_date = None
    
    assessment.save()
    
    # Log the consent update
    AuditLog.objects.create(
        action="consent_updated",
        user=updated_by,
        object_type="Assessment",
        object_id=str(assessment.id),
        description=f"Consent updated to: {consent_obtained}"
    )
