"""
Views for the assessments app.
"""

import logging

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.reports.models import DraftReport
from apps.audit.models import AuditLog
from apps.core.permissions import IsAdmin, IsAdminOrTeacher, IsTeacherOfStudent
from apps.reports.models import SignedReport

from .models import Assessment, Recording
from .serializers import (
    AssessmentCreateSerializer,
    AssessmentDetailSerializer,
    AssessmentListSerializer,
    AssessmentSignOffSerializer,
    RecordingUploadSerializer,
)

logger = logging.getLogger(__name__)


class AssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for assessment management.
    
    Provides endpoints for:
    - Creating assessments
    - Uploading recordings
    - Viewing assessment status and results
    - Teacher sign-off
    """
    
    def get_queryset(self):
        """Filter assessments based on user role."""
        user = self.request.user
        
        if user.role == "admin":
            return Assessment.objects.all()
        elif user.role == "teacher":
            # Teachers see assessments from their cohorts
            return Assessment.objects.filter(cohort__teacher=user)
        else:
            # Students see only their own assessments
            return Assessment.objects.filter(student__user=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == "create":
            return AssessmentCreateSerializer
        elif self.action == "list":
            return AssessmentListSerializer
        elif self.action in ["retrieve", "update", "partial_update"]:
            return AssessmentDetailSerializer
        return AssessmentDetailSerializer
    
    def get_permissions(self):
        """Custom permissions for different actions."""
        from rest_framework.permissions import IsAuthenticated
        
        if self.action == "create":
            return [IsAdminOrTeacher()]
        elif self.action in ["destroy"]:
            return [IsAdmin()]
        elif self.action in ["upload_recording", "sign_off"]:
            return [IsAdminOrTeacher()]
        
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Create assessment and log the action."""
        assessment = serializer.save()
        
        AuditLog.log_assessment_creation(self.request.user, assessment)
        
        return assessment
    
    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload_recording(self, request, pk=None):
        """
        Upload a video recording for an assessment.
        
        POST /api/v1/assessments/{id}/upload_recording/
        
        Form data:
            - file: Video file (mp4, mov, avi)
        """
        assessment = self.get_object()
        
        # Check assessment is in valid state
        if assessment.status not in ["pending", "uploading"]:
            return Response(
                {"error": "Assessment is not in a valid state for upload"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RecordingUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uploaded_file = serializer.validated_data["file"]
        
        try:
            # Generate S3 key
            s3_key = f"recordings/{assessment.id}/{uploaded_file.name}"
            
            # Upload to S3
            s3 = boto3.client('s3')
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            
            s3.upload_fileobj(
                uploaded_file,
                bucket,
                s3_key,
                ExtraArgs={
                    'ContentType': uploaded_file.content_type,
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
            
            AuditLog.objects.create(
                action="assessment_uploaded",
                user=request.user,
                object_type="Assessment",
                object_id=str(assessment.id),
                description=f"Recording uploaded: {uploaded_file.name}"
            )
            
            return Response({
                "message": "Recording uploaded successfully",
                "recording_id": str(recording.id),
                "status": "uploading"
            }, status=status.HTTP_201_CREATED)
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return Response(
                {"error": "Failed to upload recording"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return Response(
                {"error": "Failed to process upload"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """
        Start processing the assessment through the AI pipeline.
        
        POST /api/v1/assessments/{id}/process/
        """
        assessment = self.get_object()
        
        if assessment.status not in ["uploading", "error"]:
            return Response(
                {"error": f"Cannot start processing from status: {assessment.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not assessment.has_recording:
            return Response(
                {"error": "No recording uploaded"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start async processing
        from apps.analysis.tasks import process_assessment
        process_assessment.delay(str(assessment.id))
        
        assessment.status = "processing"
        assessment.save()
        
        return Response({
            "message": "Processing started",
            "status": "processing"
        })
    
    @action(detail=True, methods=["get"])
    def transcript(self, request, pk=None):
        """
        Get the transcript for an assessment.
        
        GET /api/v1/assessments/{id}/transcript/
        """
        assessment = self.get_object()
        
        if not hasattr(assessment, 'transcript'):
            return Response(
                {"error": "Transcript not available"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        transcript = assessment.transcript
        return Response({
            "segments": transcript.segments,
            "full_text": transcript.full_text,
            "language": transcript.language,
            "confidence": transcript.confidence,
        })
    
    @action(detail=True, methods=["get"])
    def features(self, request, pk=None):
        """
        Get the extracted feature signals for an assessment.
        
        GET /api/v1/assessments/{id}/features/
        """
        assessment = self.get_object()
        
        if not hasattr(assessment, 'feature_signals'):
            return Response(
                {"error": "Feature signals not available"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        signals = assessment.feature_signals
        
        # Build response with all features
        features = {}
        for field in signals._meta.fields:
            if field.name not in ['id', 'assessment', 'created_at', 'updated_at']:
                value = getattr(signals, field.name)
                if value is not None:
                    features[field.name] = value
        
        return Response(features)
    
    @action(detail=True, methods=["get"])
    def evidence(self, request, pk=None):
        """
        Get the evidence candidates for an assessment.
        
        GET /api/v1/assessments/{id}/evidence/
        """
        assessment = self.get_object()
        
        candidates = assessment.evidence_candidates.all().order_by('start_time')
        
        return Response([
            {
                "candidate_id": c.candidate_id,
                "start_time": c.start_time,
                "end_time": c.end_time,
                "type": c.type,
                "summary": c.summary,
                "transcript_text": c.transcript_text,
                "features": c.features,
                "relevant_strands": c.relevant_strands,
            }
            for c in candidates
        ])
    
    @action(detail=True, methods=["get"])
    def draft_report(self, request, pk=None):
        """
        Get the draft report for an assessment.
        
        GET /api/v1/assessments/{id}/draft_report/
        """
        assessment = self.get_object()
        
        if not hasattr(assessment, 'draft_report'):
            return Response(
                {"error": "Draft report not available"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        report = assessment.draft_report
        
        return Response({
            "id": str(report.id),
            "physical_score": report.physical_score,
            "linguistic_score": report.linguistic_score,
            "cognitive_score": report.cognitive_score,
            "social_emotional_score": report.social_emotional_score,
            "feedback": report.feedback,
            "overall_confidence": report.overall_confidence,
            "warnings": report.warnings,
            "eal_scaffolds": report.eal_scaffolds,
            "is_reviewed": report.is_reviewed,
            "ai_model": report.ai_model,
            "generated_at": report.generated_at,
        })
    
    @action(detail=True, methods=["post"])
    def sign_off(self, request, pk=None):
        """
        Sign off on an assessment report (teacher action).
        
        POST /api/v1/assessments/{id}/sign_off/
        """
        assessment = self.get_object()
        
        if not hasattr(assessment, 'draft_report'):
            return Response(
                {"error": "No draft report available to sign off"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AssessmentSignOffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        draft = assessment.draft_report
        
        # Build final scores from input
        def build_strand_score(band, clips, draft_score):
            return {
                "band": band,
                "confidence": draft_score.get("confidence", 0.7),
                "evidence_clips": clips,
                "justification": draft_score.get("justification", ""),
                "subskills": draft_score.get("subskills", {})
            }
        
        # Build final scores
        physical_score = build_strand_score(
            data["physical_band"],
            data.get("physical_clips", []),
            draft.physical_score
        )
        linguistic_score = build_strand_score(
            data["linguistic_band"],
            data.get("linguistic_clips", []),
            draft.linguistic_score
        )
        cognitive_score = build_strand_score(
            data["cognitive_band"],
            data.get("cognitive_clips", []),
            draft.cognitive_score
        )
        social_emotional_score = build_strand_score(
            data["social_emotional_band"],
            data.get("social_emotional_clips", []),
            draft.social_emotional_score
        )
        
        # Calculate changes from draft
        changes_summary = {
            "scores_modified": [],
            "clips_changed": {}
        }
        for strand, draft_data, final_data in [
            ("physical", draft.physical_score, physical_score),
            ("linguistic", draft.linguistic_score, linguistic_score),
            ("cognitive", draft.cognitive_score, cognitive_score),
            ("social_emotional", draft.social_emotional_score, social_emotional_score),
        ]:
            if draft_data.get("band") != final_data.get("band"):
                changes_summary["scores_modified"].append(strand)
            
            draft_clips = set(draft_data.get("evidence_clips", []))
            final_clips = set(final_data.get("evidence_clips", []))
            if draft_clips != final_clips:
                changes_summary["clips_changed"][strand] = {
                    "removed": list(draft_clips - final_clips),
                    "added": list(final_clips - draft_clips),
                }
        
        # Create signed report
        signed_report = SignedReport.objects.create(
            assessment=assessment,
            draft_report=draft,
            physical_score=physical_score,
            linguistic_score=linguistic_score,
            cognitive_score=cognitive_score,
            social_emotional_score=social_emotional_score,
            feedback={
                "strengths": data.get("feedback_strengths", draft.feedback.get("strengths", [])),
                "next_steps": data.get("feedback_next_steps", draft.feedback.get("next_steps", [])),
                "goals": data.get("feedback_goals", draft.feedback.get("goals", [])),
            },
            teacher_notes=data.get("teacher_notes", ""),
            signed_by=request.user,
            changes_summary=changes_summary
        )
        
        # Update assessment status
        assessment.status = "signed_off"
        assessment.completed_at = timezone.now()
        assessment.save()
        
        # Log the sign-off
        AuditLog.log_sign_off(request.user, signed_report)
        
        return Response({
            "message": "Report signed off successfully",
            "signed_report_id": str(signed_report.id),
            "signed_at": signed_report.signed_at,
        })
    
    @action(detail=True, methods=["get"])
    def signed_report(self, request, pk=None):
        """
        Get the signed-off report for an assessment.
        
        GET /api/v1/assessments/{id}/signed_report/
        """
        assessment = self.get_object()
        
        if not hasattr(assessment, 'signed_report'):
            return Response(
                {"error": "Report has not been signed off yet"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        report = assessment.signed_report
        
        return Response({
            "id": str(report.id),
            "physical_score": report.physical_score,
            "linguistic_score": report.linguistic_score,
            "cognitive_score": report.cognitive_score,
            "social_emotional_score": report.social_emotional_score,
            "feedback": report.feedback,
            "teacher_notes": report.teacher_notes,
            "signed_by": report.signed_by.full_name if report.signed_by else None,
            "signed_at": report.signed_at,
            "changes_summary": report.changes_summary,
        })
    
    @action(detail=True, methods=["post"])
    def update_consent(self, request, pk=None):
        """
        Update consent status for an assessment.
        
        POST /api/v1/assessments/{id}/update_consent/
        
        Request body:
            {
                "consent_obtained": true
            }
        """
        assessment = self.get_object()
        
        consent = request.data.get("consent_obtained")
        if consent is None:
            return Response(
                {"error": "consent_obtained is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assessment.consent_obtained = consent
        if consent:
            assessment.consent_date = timezone.now()
        else:
            assessment.consent_date = None
        
        assessment.save()
        
        AuditLog.objects.create(
            action="consent_updated",
            user=request.user,
            object_type="Assessment",
            object_id=str(assessment.id),
            description=f"Consent updated to: {consent}"
        )
        
        return Response({
            "message": "Consent updated",
            "consent_obtained": assessment.consent_obtained
        })
