"""
PDF Export Service for the Oracy AI platform.

Generates inspection-grade PDF reports for:
- Individual student assessments (teacher and parent versions)
- Cohort/school-level summary reports
- Evidence packs

Uses ReportLab for PDF generation with proper formatting,
accessibility considerations, and branding.
"""

import logging
import tempfile
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ReportLab imports
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        Image,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not installed. PDF generation will be unavailable.")


class PDFExportError(Exception):
    """Exception raised when PDF export fails."""
    pass


class PDFExportService:
    """
    Service for generating PDF reports.
    
    Creates professional, inspection-grade PDF documents for
    student assessments and cohort summaries.
    """
    
    # Brand colors
    PRIMARY_COLOR = colors.HexColor('#2563EB')  # Blue
    SECONDARY_COLOR = colors.HexColor('#64748B')  # Slate
    SUCCESS_COLOR = colors.HexColor('#10B981')  # Green
    WARNING_COLOR = colors.HexColor('#F59E0B')  # Amber
    DANGER_COLOR = colors.HexColor('#EF4444')  # Red
    
    # Band colors
    BAND_COLORS = {
        'emerging': colors.HexColor('#FEE2E2'),  # Light red
        'expected': colors.HexColor('#DBEAFE'),  # Light blue
        'exceeding': colors.HexColor('#D1FAE5'),  # Light green
    }
    
    BAND_TEXT_COLORS = {
        'emerging': colors.HexColor('#991B1B'),
        'expected': colors.HexColor('#1E40AF'),
        'exceeding': colors.HexColor('#065F46'),
    }
    
    def __init__(self):
        """Initialize PDF export service."""
        if not REPORTLAB_AVAILABLE:
            raise PDFExportError(
                "ReportLab is required for PDF generation. "
                "Install with: pip install reportlab"
            )
        
        self.styles = self._create_styles()
    
    def _create_styles(self) -> Dict:
        """Create custom paragraph styles for the report."""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection header
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading3'],
            fontSize=13,
            textColor=self.SECONDARY_COLOR,
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
        
        # Normal text
        styles.add(ParagraphStyle(
            name='BodyText',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=8
        ))
        
        # Label style (for metadata)
        styles.add(ParagraphStyle(
            name='Label',
            fontSize=9,
            textColor=self.SECONDARY_COLOR,
            fontName='Helvetica-Oblique'
        ))
        
        # Value style
        styles.add(ParagraphStyle(
            name='Value',
            fontSize=10,
            fontName='Helvetica-Bold'
        ))
        
        # Band badge styles
        for band in ['emerging', 'expected', 'exceeding']:
            styles.add(ParagraphStyle(
                name=f'Band_{band}',
                fontSize=11,
                textColor=self.BAND_TEXT_COLORS[band],
                fontName='Helvetica-Bold',
                alignment=TA_CENTER
            ))
        
        return styles
    
    def generate_assessment_report(
        self,
        report,
        include_evidence: bool = True,
        simplified: bool = False
    ) -> BytesIO:
        """
        Generate PDF for an individual assessment report.
        
        Args:
            report: SignedReport or DraftReport instance
            include_evidence: Whether to include evidence clips section
            simplified: If True, generates parent-friendly simplified version
            
        Returns:
            BytesIO containing the PDF data
        """
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Build content
        story = []
        
        # Header
        story.extend(self._build_header(report, simplified))
        
        # Student info
        story.extend(self._build_student_info(report.assessment))
        
        # Overall summary
        story.extend(self._build_overall_summary(report, simplified))
        
        # Strand scores
        story.extend(self._build_strand_scores(report, simplified))
        
        # Evidence clips (if requested)
        if include_evidence:
            story.extend(self._build_evidence_section(report))
        
        # Feedback
        story.extend(self._build_feedback_section(report, simplified))
        
        # Footer/audit info
        story.extend(self._build_footer(report))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def generate_cohort_report(
        self,
        cohort,
        assessments: List,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> BytesIO:
        """
        Generate PDF summary report for a cohort.
        
        Args:
            cohort: Cohort instance
            assessments: List of assessments to include
            start_date: Optional filter start date
            end_date: Optional filter end date
            
        Returns:
            BytesIO containing the PDF data
        """
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Cohort Assessment Summary", self.styles['ReportTitle']))
        story.append(Spacer(1, 20))
        
        # Cohort info
        story.extend(self._build_cohort_info(cohort, start_date, end_date))
        story.append(Spacer(1, 20))
        
        # Summary statistics
        story.extend(self._build_cohort_statistics(assessments))
        story.append(PageBreak())
        
        # Individual student table
        story.extend(self._build_student_table(assessments))
        
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def _build_header(self, report, simplified: bool) -> List:
        """Build report header section."""
        elements = []
        
        # Title
        title = "Student Assessment Report"
        if simplified:
            title = "Your Child's Speaking Assessment"
        
        elements.append(Paragraph(title, self.styles['ReportTitle']))
        
        # Report type badge
        if hasattr(report, 'signed_by') and report.signed_by:
            status_text = "✓ Teacher Verified"
            status_color = self.SUCCESS_COLOR
        else:
            status_text = "Draft Report"
            status_color = self.WARNING_COLOR
        
        status_para = Paragraph(
            f'<font color="{status_color.hexval()}">{status_text}</font>',
            self.styles['BodyText']
        )
        elements.append(status_para)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_student_info(self, assessment) -> List:
        """Build student information section."""
        elements = []
        
        elements.append(Paragraph("Student Information", self.styles['SectionHeader']))
        
        # Create info table
        student = assessment.student
        data = [
            [Paragraph("Student:", self.styles['Label']), 
             Paragraph(f"{student.first_name} {student.last_name}", self.styles['Value'])],
            [Paragraph("Year Group:", self.styles['Label']),
             Paragraph(student.get_year_group_display() or student.age_band, self.styles['Value'])],
            [Paragraph("Assessment Mode:", self.styles['Label']),
             Paragraph(assessment.get_mode_display(), self.styles['Value'])],
            [Paragraph("Date:", self.styles['Label']),
             Paragraph(assessment.created_at.strftime("%d %B %Y"), self.styles['Value'])],
        ]
        
        if assessment.prompt:
            data.append([
                Paragraph("Topic:", self.styles['Label']),
                Paragraph(assessment.prompt[:200] + ("..." if len(assessment.prompt) > 200 else ""), 
                         self.styles['BodyText'])
            ])
        
        table = Table(data, colWidths=[4*cm, 12*cm])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_overall_summary(self, report, simplified: bool) -> List:
        """Build overall summary section."""
        elements = []
        
        elements.append(Paragraph("Overall Assessment", self.styles['SectionHeader']))
        
        # Calculate overall band
        strands = ['physical', 'linguistic', 'cognitive', 'social_emotional']
        bands = []
        for strand in strands:
            score_data = getattr(report, f'{strand}_score', {})
            band = score_data.get('band', 'expected')
            bands.append(band)
        
        # Simple majority for overall
        band_counts = {'emerging': 0, 'expected': 0, 'exceeding': 0}
        for band in bands:
            band_counts[band] = band_counts.get(band, 0) + 1
        
        overall_band = max(band_counts, key=band_counts.get)
        
        # Create summary box
        band_display = overall_band.capitalize()
        confidence = getattr(report, 'overall_confidence', None)
        
        summary_text = f"""
        <para alignment="center">
        <font size="14" color="{self.BAND_TEXT_COLORS[overall_band].hexval()}">
        <b>Overall Level: {band_display}</b>
        </font>
        </para>
        """
        
        if confidence:
            summary_text += f"""
            <para alignment="center">
            <font size="9" color="{self.SECONDARY_COLOR.hexval()}">
            Assessment Confidence: {int(confidence * 100)}%
            </font>
            </para>
            """
        
        summary_para = Paragraph(summary_text, self.styles['BodyText'])
        
        summary_data = [[summary_para]]
        summary_table = Table(summary_data, colWidths=[16*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.BAND_COLORS[overall_band]),
            ('BOX', (0, 0), (-1, -1), 1, self.BAND_TEXT_COLORS[overall_band]),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_strand_scores(self, report, simplified: bool) -> List:
        """Build strand scores table."""
        elements = []
        
        elements.append(Paragraph("Strand Breakdown", self.styles['SectionHeader']))
        
        # Table header
        headers = ['Strand', 'Level', 'Key Evidence']
        data = [headers]
        
        strands = [
            ('physical', 'Physical Delivery', 'Voice, pace, clarity'),
            ('linguistic', 'Language & Vocabulary', 'Word choices, sentences'),
            ('cognitive', 'Thinking & Structure', 'Reasoning, organisation'),
            ('social_emotional', 'Audience Awareness', 'Engagement, confidence')
        ]
        
        for strand_key, strand_name, strand_desc in strands:
            score_data = getattr(report, f'{strand_key}_score', {})
            band = score_data.get('band', 'expected')
            
            # Get evidence clips
            evidence_clips = score_data.get('evidence_clips', [])
            if evidence_clips:
                evidence_text = f"{len(evidence_clips)} clip(s) identified"
            else:
                evidence_text = "No specific clips"
            
            band_color = self.BAND_TEXT_COLORS[band]
            
            row = [
                Paragraph(f"<b>{strand_name}</b><br/><font size='8' color='{self.SECONDARY_COLOR.hexval()}'>{strand_desc}</font>", 
                         self.styles['BodyText']),
                Paragraph(f"<font color='{band_color.hexval()}'><b>{band.capitalize()}</b></font>",
                         self.styles[f'Band_{band}']),
                Paragraph(evidence_text, self.styles['BodyText'])
            ]
            data.append(row)
        
        table = Table(data, colWidths=[6*cm, 3*cm, 7*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_evidence_section(self, report) -> List:
        """Build evidence clips section."""
        elements = []
        
        elements.append(Paragraph("Evidence Clips", self.styles['SectionHeader']))
        elements.append(Paragraph(
            "The following clips were identified as evidence for the assessment scores:",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 10))
        
        # Get evidence candidates
        assessment = report.assessment
        try:
            candidates = assessment.evidence_candidates.all()
            
            if candidates:
                # Create evidence table
                data = [['Time', 'Strand', 'Description']]
                
                for candidate in candidates[:8]:  # Limit to 8 clips
                    time_str = f"{int(candidate.start_time // 60)}:{int(candidate.start_time % 60):02d}"
                    if candidate.end_time:
                        time_str += f" - {int(candidate.end_time // 60)}:{int(candidate.end_time % 60):02d}"
                    
                    strands = candidate.relevant_strands
                    strand_text = ', '.join(s.replace('_', ' ').title() for s in strands[:2])
                    
                    data.append([
                        time_str,
                        strand_text,
                        candidate.summary[:100] + ('...' if len(candidate.summary) > 100 else '')
                    ])
                
                table = Table(data, colWidths=[3*cm, 4*cm, 9*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.SECONDARY_COLOR),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                
                elements.append(table)
            else:
                elements.append(Paragraph(
                    "No evidence clips available for this assessment.",
                    self.styles['BodyText']
                ))
        except Exception as e:
            logger.warning(f"Could not load evidence candidates: {e}")
            elements.append(Paragraph(
                "Evidence clips unavailable.",
                self.styles['BodyText']
            ))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_feedback_section(self, report, simplified: bool) -> List:
        """Build feedback section."""
        elements = []
        
        elements.append(Paragraph("Feedback", self.styles['SectionHeader']))
        
        feedback = report.feedback or {}
        
        # Strengths
        strengths = feedback.get('strengths', [])
        if strengths:
            elements.append(Paragraph("Strengths:", self.styles['SubsectionHeader']))
            for i, strength in enumerate(strengths[:3], 1):
                text = strength.get('text', '') if isinstance(strength, dict) else str(strength)
                elements.append(Paragraph(f"{i}. {text}", self.styles['BodyText']))
            elements.append(Spacer(1, 10))
        
        # Next steps
        next_steps = feedback.get('next_steps', [])
        if next_steps:
            elements.append(Paragraph("Next Steps:", self.styles['SubsectionHeader']))
            for i, step in enumerate(next_steps[:3], 1):
                text = step.get('text', '') if isinstance(step, dict) else str(step)
                elements.append(Paragraph(f"{i}. {text}", self.styles['BodyText']))
            elements.append(Spacer(1, 10))
        
        # Goals
        goals = feedback.get('goals', [])
        if goals:
            elements.append(Paragraph("Practice Goals:", self.styles['SubsectionHeader']))
            for goal in goals[:2]:
                elements.append(Paragraph(f"• {goal}", self.styles['BodyText']))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_footer(self, report) -> List:
        """Build report footer with audit info."""
        elements = []
        
        elements.append(Spacer(1, 30))
        
        # Separator line
        separator = Table([['']], colWidths=[16*cm])
        separator.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.grey),
        ]))
        elements.append(separator)
        elements.append(Spacer(1, 10))
        
        # Footer text
        footer_parts = []
        
        if hasattr(report, 'signed_by') and report.signed_by:
            footer_parts.append(f"Verified by: {report.signed_by.get_full_name()}")
            if report.signed_at:
                footer_parts.append(f"on {report.signed_at.strftime('%d %B %Y')}")
        
        if hasattr(report, 'generated_at') and report.generated_at:
            footer_parts.append(f"| Generated: {report.generated_at.strftime('%d %B %Y')}")
        
        if hasattr(report, 'benchmark_version') and report.benchmark_version:
            footer_parts.append(f"| Benchmark: {report.benchmark_version}")
        
        footer_text = ' '.join(footer_parts)
        
        elements.append(Paragraph(
            f'<font size="8" color="{self.SECONDARY_COLOR.hexval()}">{footer_text}</font>',
            ParagraphStyle(name='Footer', alignment=TA_CENTER, fontSize=8)
        ))
        
        # Confidentiality notice
        elements.append(Paragraph(
            f'<font size="7" color="{self.SECONDARY_COLOR.hexval()}">'
            'This report is confidential and intended for educational purposes only.</font>',
            ParagraphStyle(name='Confidential', alignment=TA_CENTER, fontSize=7)
        ))
        
        return elements
    
    def _build_cohort_info(self, cohort, start_date, end_date) -> List:
        """Build cohort information section."""
        elements = []
        
        # Use teacher's school for cohort
        school_name = cohort.teacher.school.name if cohort.teacher and cohort.teacher.school else 'N/A'
        
        info_text = f"""
        <b>Cohort:</b> {cohort.name}<br/>
        <b>School:</b> {school_name}<br/>
        """
        
        if start_date:
            info_text += f"<b>From:</b> {start_date.strftime('%d %B %Y')}<br/>"
        if end_date:
            info_text += f"<b>To:</b> {end_date.strftime('%d %B %Y')}<br/>"
        
        elements.append(Paragraph(info_text, self.styles['BodyText']))
        
        return elements
    
    def _build_cohort_statistics(self, assessments) -> List:
        """Build cohort statistics section."""
        elements = []
        
        elements.append(Paragraph("Summary Statistics", self.styles['SectionHeader']))
        
        # Calculate statistics
        total = len(assessments)
        
        band_counts = {'emerging': 0, 'expected': 0, 'exceeding': 0}
        for assessment in assessments:
            if hasattr(assessment, 'signed_report'):
                report = assessment.signed_report
                # Calculate overall band (simplified)
                bands = []
                for strand in ['physical', 'linguistic', 'cognitive', 'social_emotional']:
                    score = getattr(report, f'{strand}_score', {})
                    bands.append(score.get('band', 'expected'))
                
                # Majority band
                from collections import Counter
                majority = Counter(bands).most_common(1)[0][0]
                band_counts[majority] += 1
        
        # Stats table
        data = [
            ['Total Assessments', str(total)],
            ['Emerging', str(band_counts['emerging'])],
            ['Expected', str(band_counts['expected'])],
            ['Exceeding', str(band_counts['exceeding'])],
        ]
        
        table = Table(data, colWidths=[8*cm, 8*cm])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_student_table(self, assessments) -> List:
        """Build table of individual student assessments."""
        elements = []
        
        elements.append(Paragraph("Individual Assessments", self.styles['SectionHeader']))
        
        # Table data
        data = [['Student', 'Mode', 'Date', 'Overall']]
        
        for assessment in assessments:
            student = assessment.student
            student_name = f"{student.first_name} {student.last_name}"
            mode = assessment.get_mode_display()
            date = assessment.created_at.strftime('%d/%m/%Y')
            
            # Get overall band
            overall = 'N/A'
            if hasattr(assessment, 'signed_report'):
                report = assessment.signed_report
                # Simplified - just use cognitive as indicator
                cog_score = report.cognitive_score or {}
                overall = cog_score.get('band', 'expected').capitalize()
            elif hasattr(assessment, 'draft_report'):
                report = assessment.draft_report
                cog_score = report.cognitive_score or {}
                overall = cog_score.get('band', 'expected').capitalize()
            
            data.append([student_name, mode, date, overall])
        
        table = Table(data, colWidths=[6*cm, 4*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        
        elements.append(table)
        
        return elements
    
    def save_to_file(self, pdf_buffer: BytesIO, filename: str) -> str:
        """
        Save PDF buffer to file.
        
        Args:
            pdf_buffer: BytesIO containing PDF data
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        import os
        
        # Use temp directory or media root
        output_dir = getattr(settings, 'MEDIA_ROOT', tempfile.gettempdir())
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        return filepath
