"""
Views for the assessments app.

Refactored to follow Django Styleguide:
- Business logic moved to services
- Data fetching moved to selectors
- Views are thin and only handle HTTP concerns
"""

import logging

from botocore.exceptions import ClientError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.core.permissions import IsAdmin, IsAdminOrTeacher, IsTeacherOfStudent
from apps.reports.models import DraftReport, SignedReport

from .models import Assessment
from .selectors import (
    assessment_list,
    assessment_list_for_student,
    assessment_list_for_teacher,
)
from .serializers import (
    AssessmentCreateSerializer,
    AssessmentDetailSerializer,
    AssessmentListSerializer,
    AssessmentSignOffSerializer,
    RecordingUploadSerializer,
)
from .services import (
    assessment_mark_error,
    assessment_start_processing,
    assessment_upload_recording,
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
    
    Uses selectors for data fetching and services for business logic.
    """
    
    def get_queryset(self):
        """Filter assessments based on user role using selectors."""
        user = self.request.user
        
        if user.role == "admin":
            return assessment_list()
        elif user.role == "teacher":
            return assessment_list_for_teacher(teacher_id=str(user.id))
        else:
            return assessment_list_for_student(student_id=str(user.id))
    
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
        if self.action == "create":
            return [IsAdminOrTeacher()]
        elif self.action in ["destroy"]:
            return [IsAdmin()]
        elif self.action in ["upload_recording", "sign_off"]:
            return [IsAdminOrTeacher()]
        
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Create assessment using service and log the action."""
        from .services import assessment_create
        
        assessment = assessment_create(
            student_id=str(serializer.validated_data["student"].id),
            cohort_id=str(serializer.validated_data["cohort"].id),
            mode=serializer.validated_data["mode"],
            prompt=serializer.validated_data["prompt"],
            time_limit_seconds=serializer.validated_data.get("time_limit_seconds", 180),
            created_by=self.request.user,
        )
        
        return assessment
    
    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload_recording(self, request, pk=None):
        """
        Upload a video recording for an assessment.
        Uses assessment_upload_recording service.
        
        POST /api/v1/assessments/{id}/upload_recording/
        
        Form data:
            - file: Video file (mp4, mov, avi)
        """
        assessment = self.get_object()
        
        serializer = RecordingUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uploaded_file = serializer.validated_data["file"]
        
        try:
            # Use service for upload logic
            recording = assessment_upload_recording(
                assessment=assessment,
                uploaded_file=uploaded_file,
                uploaded_by=request.user,
            )
            
            return Response({
                "message": "Recording uploaded successfully",
                "recording_id": str(recording.id),
                "status": "uploading"
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
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
        Uses assessment_start_processing service.
        
        POST /api/v1/assessments/{id}/process/
        """
        assessment = self.get_object()
        
        try:
            # Use service for processing logic
            assessment_start_processing(
                assessment=assessment,
                started_by=request.user,
            )
            
            return Response({
                "message": "Processing started",
                "status": "processing"
            })
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
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
        Delegates to reports app service.
        
        POST /api/v1/assessments/{id}/sign_off/
        """
        from apps.reports.services import signed_report_create_from_draft
        
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
        
        # Build modifications from request data
        modifications = {}
        
        # Build strand scores
        for strand in ['physical', 'linguistic', 'cognitive', 'social_emotional']:
            band_key = f"{strand}_band"
            clips_key = f"{strand}_clips"
            
            if band_key in data:
                draft_score = getattr(draft, f"{strand}_score")
                modifications[f"{strand}_score"] = {
                    "band": data[band_key],
                    "confidence": draft_score.get("confidence", 0.7),
                    "evidence_clips": data.get(clips_key, []),
                    "justification": draft_score.get("justification", ""),
                    "subskills": draft_score.get("subskills", {}),
                }
        
        # Build feedback modification
        feedback_data = {}
        if "feedback_strengths" in data:
            feedback_data["strengths"] = data["feedback_strengths"]
        if "feedback_next_steps" in data:
            feedback_data["next_steps"] = data["feedback_next_steps"]
        if "feedback_goals" in data:
            feedback_data["goals"] = data["feedback_goals"]
        
        if feedback_data:
            modifications["feedback"] = {
                "strengths": feedback_data.get("strengths", draft.feedback.get("strengths", [])),
                "next_steps": feedback_data.get("next_steps", draft.feedback.get("next_steps", [])),
                "goals": feedback_data.get("goals", draft.feedback.get("goals", [])),
            }
        
        # Use reports service for sign-off
        signed_report = signed_report_create_from_draft(
            draft=draft,
            signed_by=request.user,
            modifications=modifications,
            teacher_notes=data.get("teacher_notes", ""),
        )
        
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
        Uses service for consent update logic.
        
        POST /api/v1/assessments/{id}/update_consent/
        
        Request body:
            {
                "consent_obtained": true
            }
        """
        from .services import assessment_update_consent
        
        assessment = self.get_object()
        
        consent = request.data.get("consent_obtained")
        if consent is None:
            return Response(
                {"error": "consent_obtained is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Use service for consent update
            assessment_update_consent(
                assessment=assessment,
                consent_obtained=consent,
                updated_by=request.user,
            )
            
            return Response({
                "message": "Consent updated",
                "consent_obtained": assessment.consent_obtained
            })
            
        except Exception as e:
            logger.error(f"Consent update failed: {e}")
            return Response(
                {"error": "Failed to update consent"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
