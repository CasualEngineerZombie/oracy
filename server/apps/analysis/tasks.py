"""
Celery tasks for the assessment processing pipeline.

Orchestrates the full AI pipeline:
1. Extract audio from video
2. Speech-to-text transcription
3. Feature extraction
4. Evidence candidate generation
5. LLM scoring
6. Report generation
"""

import logging
import os
import tempfile
from typing import Optional

from celery import chain, chord, group, shared_task
from django.conf import settings

from apps.assessments.models import Assessment
from apps.audit.models import AuditLog
from apps.benchmarks.models import BenchmarkVersion

from .models import EvidenceCandidate, FeatureSignals, Transcript
from .services import (
    EvidenceCandidateGenerator,
    FeatureExtractionService,
    LLMScoringService,
    STTService,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_assessment(self, assessment_id: str):
    """
    Main task to process an assessment through the full pipeline.
    
    This orchestrates the entire AI pipeline asynchronously.
    """
    logger.info(f"Starting assessment processing: {assessment_id}")
    
    try:
        assessment = Assessment.objects.select_related(
            'student', 'recording'
        ).get(id=assessment_id)
        
        # Update status
        assessment.status = "processing"
        assessment.save()
        
        # Log processing start
        AuditLog.log_processing_event(
            assessment,
            "processing_started",
            "Assessment processing pipeline initiated"
        )
        
        # Start the pipeline
        pipeline = chain(
            extract_audio.s(assessment_id),
            transcribe_audio.s(assessment_id),
            extract_features.s(assessment_id),
            generate_evidence_candidates.s(assessment_id),
            generate_draft_report.s(assessment_id),
            finalize_processing.s(assessment_id)
        )
        
        pipeline.apply_async()
        
        return {"status": "pipeline_started", "assessment_id": assessment_id}
        
    except Assessment.DoesNotExist:
        logger.error(f"Assessment not found: {assessment_id}")
        raise self.retry(countdown=60)
    except Exception as e:
        logger.error(f"Failed to start processing: {e}")
        _mark_assessment_error(assessment_id, str(e))
        raise


@shared_task(bind=True, max_retries=2)
def extract_audio(self, assessment_id: str):
    """Extract audio from video recording."""
    logger.info(f"Extracting audio for assessment: {assessment_id}")
    
    try:
        assessment = Assessment.objects.select_related('recording').get(id=assessment_id)
        recording = assessment.recording
        
        if not recording:
            raise ValueError("No recording found for assessment")
        
        # Download video from S3
        video_path = _download_from_s3(recording.s3_bucket, recording.s3_key)
        
        # Extract audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_path = tmp.name
        
        STTService.extract_audio_from_video(video_path, audio_path)
        
        # Upload audio to S3
        audio_key = f"audio/{assessment_id}/audio.wav"
        _upload_to_s3(recording.s3_bucket, audio_key, audio_path)
        
        # Update recording
        recording.audio_extracted = True
        recording.audio_s3_key = audio_key
        recording.save()
        
        # Cleanup
        os.unlink(video_path)
        os.unlink(audio_path)
        
        logger.info(f"Audio extraction complete for assessment: {assessment_id}")
        return {"status": "audio_extracted", "assessment_id": assessment_id}
        
    except Exception as e:
        logger.error(f"Audio extraction failed: {e}")
        raise self.retry(countdown=30)


@shared_task(bind=True, max_retries=2)
def transcribe_audio(self, prev_result: dict, assessment_id: str):
    """Transcribe audio using STT service."""
    logger.info(f"Transcribing audio for assessment: {assessment_id}")
    
    try:
        assessment = Assessment.objects.select_related('recording').get(id=assessment_id)
        recording = assessment.recording
        
        # Download audio from S3
        audio_path = _download_from_s3(recording.s3_bucket, recording.audio_s3_key)
        
        # Transcribe
        stt_service = STTService()
        result = stt_service.transcribe(audio_path)
        
        # Convert to model format
        segments_data = []
        for seg in result.segments:
            segments_data.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "words": [
                    {
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "confidence": w.confidence
                    }
                    for w in seg.words
                ]
            })
        
        # Save transcript
        Transcript.objects.create(
            assessment=assessment,
            segments=segments_data,
            full_text=result.full_text,
            language=result.language,
            confidence=result.confidence,
            provider=result.provider,
            model_version=result.model_version,
            processing_time_seconds=result.processing_time
        )
        
        # Log
        AuditLog.log_processing_event(
            assessment,
            "transcription_complete",
            f"Transcription complete: {len(segments_data)} segments"
        )
        
        # Cleanup
        os.unlink(audio_path)
        
        logger.info(f"Transcription complete for assessment: {assessment_id}")
        return {"status": "transcribed", "assessment_id": assessment_id}
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise self.retry(countdown=30)


@shared_task(bind=True, max_retries=2)
def extract_features(self, prev_result: dict, assessment_id: str):
    """Extract features from transcript and audio."""
    logger.info(f"Extracting features for assessment: {assessment_id}")
    
    try:
        assessment = Assessment.objects.select_related(
            'recording', 'transcript'
        ).get(id=assessment_id)
        
        transcript = assessment.transcript
        recording = assessment.recording
        
        # Get duration
        duration = recording.duration_seconds if recording else None
        
        # Extract features
        extractor = FeatureExtractionService()
        features = extractor.extract_from_transcript(
            segments=transcript.segments,
            full_text=transcript.full_text,
            prompt=assessment.prompt,
            duration_seconds=duration
        )
        
        # Try to extract audio features
        audio_features = {}
        if recording and recording.audio_s3_key:
            try:
                audio_path = _download_from_s3(recording.s3_bucket, recording.audio_s3_key)
                audio_features = extractor.extract_from_audio(
                    audio_path,
                    transcript.segments
                )
                os.unlink(audio_path)
            except Exception as e:
                logger.warning(f"Could not extract audio features: {e}")
        
        # Save to database
        extractor.save_to_model(assessment_id, features, audio_features)
        
        logger.info(f"Feature extraction complete for assessment: {assessment_id}")
        return {"status": "features_extracted", "assessment_id": assessment_id}
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise self.retry(countdown=30)


@shared_task(bind=True, max_retries=2)
def generate_evidence_candidates(self, prev_result: dict, assessment_id: str):
    """Generate evidence clip candidates."""
    logger.info(f"Generating evidence candidates for assessment: {assessment_id}")
    
    try:
        assessment = Assessment.objects.select_related(
            'transcript', 'feature_signals'
        ).get(id=assessment_id)
        
        transcript = assessment.transcript
        feature_signals = assessment.feature_signals
        
        # Convert feature signals to dict
        signals_dict = {
            f.name: getattr(feature_signals, f.name)
            for f in feature_signals._meta.fields
            if f.name not in ['id', 'assessment', 'created_at', 'updated_at']
        }
        
        # Generate candidates
        generator = EvidenceCandidateGenerator()
        candidates = generator.generate_candidates(
            segments=transcript.segments,
            feature_signals=signals_dict,
            prompt=assessment.prompt
        )
        
        # Save candidates
        generator.save_candidates(assessment_id, candidates)
        
        logger.info(f"Generated {len(candidates)} evidence candidates for assessment: {assessment_id}")
        return {
            "status": "candidates_generated",
            "assessment_id": assessment_id,
            "candidate_count": len(candidates)
        }
        
    except Exception as e:
        logger.error(f"Evidence generation failed: {e}")
        raise self.retry(countdown=30)


@shared_task(bind=True, max_retries=2)
def generate_draft_report(self, prev_result: dict, assessment_id: str):
    """Generate draft report using LLM scoring."""
    logger.info(f"Generating draft report for assessment: {assessment_id}")
    
    try:
        assessment = Assessment.objects.select_related(
            'student', 'transcript', 'feature_signals'
        ).prefetch_related('evidence_candidates').get(id=assessment_id)
        
        # Get benchmark
        benchmark = BenchmarkVersion.get_active_benchmark(
            age_band=assessment.student.age_band,
            mode=assessment.mode
        )
        
        if not benchmark:
            raise ValueError(f"No benchmark found for {assessment.student.age_band} / {assessment.mode}")
        
        # Get evidence candidates
        candidates = list(assessment.evidence_candidates.all())
        
        # Convert feature signals to dict
        feature_signals = {
            f.name: getattr(assessment.feature_signals, f.name)
            for f in assessment.feature_signals._meta.fields
            if f.name not in ['id', 'assessment', 'created_at', 'updated_at']
        }
        
        # Score using LLM
        scorer = LLMScoringService()
        result = scorer.score_assessment(
            assessment_id=str(assessment.id),
            transcript_segments=assessment.transcript.segments,
            feature_signals=feature_signals,
            evidence_candidates=candidates,
            benchmark_definition=benchmark.definition,
            prompt=assessment.prompt,
            is_eal=assessment.student.eal
        )
        
        # Save report
        report = scorer.save_report(
            assessment_id=str(assessment.id),
            result=result,
            benchmark_version=benchmark.version,
            ai_model=scorer.model
        )
        
        # Log
        AuditLog.log_processing_event(
            assessment,
            "draft_generated",
            f"Draft report generated with confidence: {result.overall_confidence}"
        )
        
        logger.info(f"Draft report generated for assessment: {assessment_id}")
        return {
            "status": "draft_generated",
            "assessment_id": assessment_id,
            "report_id": str(report.id)
        }
        
    except Exception as e:
        logger.error(f"Draft report generation failed: {e}")
        raise self.retry(countdown=60)


@shared_task
def finalize_processing(prev_result: dict, assessment_id: str):
    """Finalize assessment processing."""
    logger.info(f"Finalizing assessment: {assessment_id}")
    
    try:
        assessment = Assessment.objects.get(id=assessment_id)
        
        assessment.status = "draft_ready"
        assessment.save()
        
        AuditLog.log_processing_event(
            assessment,
            "processing_complete",
            "Assessment processing complete - draft ready for review"
        )
        
        logger.info(f"Assessment processing complete: {assessment_id}")
        return {"status": "complete", "assessment_id": assessment_id}
        
    except Exception as e:
        logger.error(f"Finalization failed: {e}")
        _mark_assessment_error(assessment_id, str(e))
        raise


def _mark_assessment_error(assessment_id: str, error_message: str):
    """Mark assessment as error state."""
    try:
        assessment = Assessment.objects.get(id=assessment_id)
        assessment.status = "error"
        assessment.status_message = error_message[:500]  # Truncate
        assessment.save()
        
        AuditLog.log_processing_event(
            assessment,
            "processing_error",
            error_message
        )
    except Exception as e:
        logger.error(f"Could not mark assessment error: {e}")


def _download_from_s3(bucket: str, key: str) -> str:
    """Download file from S3 to temporary location."""
    import boto3
    
    s3 = boto3.client('s3')
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        s3.download_file(bucket, key, tmp.name)
        return tmp.name


def _upload_to_s3(bucket: str, key: str, file_path: str):
    """Upload file to S3."""
    import boto3
    
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket, key)


# Convenience function to start processing
def start_assessment_processing(assessment_id: str):
    """
    Start the assessment processing pipeline.
    
    Usage:
        from apps.analysis.tasks import start_assessment_processing
        start_assessment_processing(str(assessment.id))
    """
    process_assessment.delay(assessment_id)