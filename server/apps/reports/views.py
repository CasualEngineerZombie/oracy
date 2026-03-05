"""
Views for the reports app.

Provides endpoints for:
- Generating and downloading PDF reports
- Viewing draft and signed reports
- Teacher review and sign-off workflows
"""

import logging
from datetime import datetime

from django.http import FileResponse, HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrTeacher, IsTeacherOfStudent
from apps.audit.models import AuditLog

from .models import DraftReport, SignedReport
from .serializers import DraftReportSerializer, SignedReportSerializer

logger = logging.getLogger(__name__)


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing assessment reports.
    
    Provides read access to draft and signed reports
    with PDF export capabilities.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter reports based on user role."""
        user = self.request.user
        
        if user.role == 'admin':
            return SignedReport.objects.all()
        elif user.role == 'teacher':
            # Teachers see reports from their cohorts
            return SignedReport.objects.filter(
                assessment__cohort__teacher=user
            )
        else:
            # Students see only their own signed reports
            return SignedReport.objects.filter(
                assessment__student__user=user
            )
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        return SignedReportSerializer
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """
        Download report as PDF.
        
        Query params:
            - simplified: bool - Generate parent-friendly version
            - include_evidence: bool - Include evidence clips (default: true)
        """
        try:
            report = self.get_object()
        except SignedReport.DoesNotExist:
            return Response(
                {'error': 'Report not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if not self._can_view_report(request.user, report):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get query params
        simplified = request.query_params.get('simplified', 'false').lower() == 'true'
        include_evidence = request.query_params.get('include_evidence', 'true').lower() == 'true'
        
        try:
            # Generate PDF
            from .services import PDFExportService
            
            service = PDFExportService()
            pdf_buffer = service.generate_assessment_report(
                report=report,
                include_evidence=include_evidence,
                simplified=simplified
            )
            
            # Determine filename
            student_name = report.assessment.student.get_full_name().replace(' ', '_')
            report_type = 'parent' if simplified else 'full'
            filename = f"oracy_report_{student_name}_{report_type}.pdf"
            
            # Create response
            response = HttpResponse(
                pdf_buffer.getvalue(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Log export
            AuditLog.objects.create(
                action='export_generated',
                user=request.user,
                object_type='SignedReport',
                object_id=str(report.id),
                description=f'PDF export generated ({report_type})',
                metadata={
                    'simplified': simplified,
                    'include_evidence': include_evidence
                }
            )
            
            # Update export tracking
            report.exported_at = timezone.now()
            report.export_format = 'pdf'
            report.save(update_fields=['exported_at', 'export_format'])
            
            return response
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _can_view_report(self, user, report) -> bool:
        """Check if user can view the report."""
        if user.role == 'admin':
            return True
        if user.role == 'teacher':
            return report.assessment.cohort.teacher == user
        # Students can only view their own signed reports
        return report.assessment.student.user == user


class DraftReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for draft report management.
    
    Teachers can:
    - View draft reports
    - Edit scores, evidence, feedback
    - Sign off to create final report
    """
    
    permission_classes = [IsAdminOrTeacher]
    serializer_class = DraftReportSerializer
    
    def get_queryset(self):
        """Filter draft reports for teacher's cohorts."""
        user = self.request.user
        
        if user.role == 'admin':
            return DraftReport.objects.all()
        
        return DraftReport.objects.filter(
            assessment__cohort__teacher=user
        )
    
    @action(detail=True, methods=['post'])
    def sign_off(self, request, pk=None):
        """
        Sign off a draft report to create the final version.
        
        This creates a SignedReport from the DraftReport
        and marks it as verified by the teacher.
        
        Request body can include modifications:
            - physical_score: modified score
            - linguistic_score: modified score
            - cognitive_score: modified score
            - social_emotional_score: modified score
            - feedback: modified feedback
            - teacher_notes: private notes
        """
        try:
            draft = self.get_object()
        except DraftReport.DoesNotExist:
            return Response(
                {'error': 'Draft report not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check teacher owns this assessment's cohort
        if not IsTeacherOfStudent().has_object_permission(
            request, self, draft.assessment
        ):
            return Response(
                {'error': 'You do not have permission to sign off this report'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get modified data from request
            modifications = {}
            
            for strand in ['physical', 'linguistic', 'cognitive', 'social_emotional']:
                field_name = f'{strand}_score'
                if field_name in request.data:
                    modifications[field_name] = request.data[field_name]
            
            if 'feedback' in request.data:
                modifications['feedback'] = request.data['feedback']
            
            teacher_notes = request.data.get('teacher_notes', '')
            
            # Calculate changes summary
            changes_summary = self._calculate_changes(draft, modifications)
            
            # Create signed report
            signed_data = {
                'assessment': draft.assessment,
                'draft_report': draft,
                'signed_by': request.user,
                'signed_at': timezone.now(),
                'teacher_notes': teacher_notes,
                'changes_summary': changes_summary,
            }
            
            # Use modified scores or draft scores
            for strand in ['physical', 'linguistic', 'cognitive', 'social_emotional']:
                field_name = f'{strand}_score'
                if field_name in modifications:
                    signed_data[field_name] = modifications[field_name]
                else:
                    signed_data[field_name] = getattr(draft, field_name)
            
            if 'feedback' in modifications:
                signed_data['feedback'] = modifications['feedback']
            else:
                signed_data['feedback'] = draft.feedback
            
            signed_report = SignedReport.objects.create(**signed_data)
            
            # Update draft status
            draft.is_reviewed = True
            draft.reviewed_by = request.user
            draft.reviewed_at = timezone.now()
            draft.save()
            
            # Update assessment status
            draft.assessment.status = 'signed_off'
            draft.assessment.save()
            
            # Log the sign-off
            AuditLog.objects.create(
                action='signed_off',
                user=request.user,
                object_type='SignedReport',
                object_id=str(signed_report.id),
                description='Teacher signed off assessment report',
                new_value={
                    'changes': changes_summary,
                    'has_notes': bool(teacher_notes)
                }
            )
            
            # Return the signed report
            serializer = SignedReportSerializer(signed_report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Sign-off failed: {e}")
            return Response(
                {'error': f'Failed to sign off report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def preview_pdf(self, request, pk=None):
        """
        Preview draft report as PDF before signing off.
        
        This generates a watermarked PDF indicating it's a preview.
        """
        try:
            draft = self.get_object()
        except DraftReport.DoesNotExist:
            return Response(
                {'error': 'Draft report not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            from .services import PDFExportService
            
            service = PDFExportService()
            pdf_buffer = service.generate_assessment_report(
                report=draft,
                include_evidence=True,
                simplified=False
            )
            
            filename = f"preview_{draft.assessment.student.get_full_name().replace(' ', '_')}.pdf"
            
            response = HttpResponse(
                pdf_buffer.getvalue(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"PDF preview failed: {e}")
            return Response(
                {'error': f'Failed to generate preview: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_changes(self, draft, modifications: dict) -> dict:
        """Calculate what was changed from draft to signed report."""
        changes = {
            'scores_modified': [],
            'clips_changed': {},
            'feedback_edited': False,
            'notes_added': False
        }
        
        for strand in ['physical', 'linguistic', 'cognitive', 'social_emotional']:
            field_name = f'{strand}_score'
            if field_name in modifications:
                draft_band = draft.all_strands.get(strand, {}).get('band')
                new_band = modifications[field_name].get('band')
                if draft_band != new_band:
                    changes['scores_modified'].append(strand)
                
                # Check clip changes
                draft_clips = set(draft.all_strands.get(strand, {}).get('evidence_clips', []))
                new_clips = set(modifications[field_name].get('evidence_clips', []))
                if draft_clips != new_clips:
                    changes['clips_changed'][strand] = {
                        'removed': list(draft_clips - new_clips),
                        'added': list(new_clips - draft_clips)
                    }
        
        if 'feedback' in modifications:
            changes['feedback_edited'] = modifications['feedback'] != draft.feedback
        
        return changes


class CohortReportViewSet(viewsets.ViewSet):
    """
    ViewSet for cohort-level reports.
    
    Provides aggregated reports for teachers and administrators.
    """
    
    permission_classes = [IsAdminOrTeacher]
    
    @action(detail=False, methods=['get'])
    def export_cohort_pdf(self, request):
        """
        Export cohort summary report as PDF.
        
        Query params:
            - cohort_id: UUID of cohort
            - start_date: Optional filter (YYYY-MM-DD)
            - end_date: Optional filter (YYYY-MM-DD)
        """
        from apps.students.models import Cohort
        
        cohort_id = request.query_params.get('cohort_id')
        if not cohort_id:
            return Response(
                {'error': 'cohort_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cohort = Cohort.objects.get(id=cohort_id)
        except Cohort.DoesNotExist:
            return Response(
                {'error': 'Cohort not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission
        if request.user.role != 'admin' and cohort.teacher != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Parse dates
        start_date = None
        end_date = None
        
        if request.query_params.get('start_date'):
            start_date = datetime.strptime(
                request.query_params['start_date'],
                '%Y-%m-%d'
            )
        
        if request.query_params.get('end_date'):
            end_date = datetime.strptime(
                request.query_params['end_date'],
                '%Y-%m-%d'
            )
        
        # Get assessments
        assessments = cohort.assessments.filter(
            status='signed_off'
        )
        
        if start_date:
            assessments = assessments.filter(created_at__gte=start_date)
        if end_date:
            assessments = assessments.filter(created_at__lte=end_date)
        
        assessments = assessments.select_related(
            'student', 'signed_report'
        ).order_by('-created_at')
        
        try:
            from .services import PDFExportService
            
            service = PDFExportService()
            pdf_buffer = service.generate_cohort_report(
                cohort=cohort,
                assessments=list(assessments),
                start_date=start_date,
                end_date=end_date
            )
            
            filename = f"cohort_report_{cohort.name.replace(' ', '_')}.pdf"
            
            response = HttpResponse(
                pdf_buffer.getvalue(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Log export
            AuditLog.objects.create(
                action='export_generated',
                user=request.user,
                object_type='Cohort',
                object_id=str(cohort.id),
                description='Cohort PDF report exported',
                metadata={
                    'assessment_count': assessments.count(),
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Cohort PDF generation failed: {e}")
            return Response(
                {'error': f'Failed to generate report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
