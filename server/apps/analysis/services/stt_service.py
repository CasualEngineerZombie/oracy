"""
Speech-to-Text Service for the Oracy AI platform.

Per MVP Section 2.1: Step 1 – Speech-to-Text (Timestamped)

Abstracts STT behind a service interface for easy vendor swapping.
Supports OpenAI, AWS Transcribe, and local WhisperX.
"""

import logging
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Protocol

import httpx
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class WordTimestamp:
    """Word-level timestamp."""
    word: str
    start: float
    end: float
    confidence: Optional[float] = None


@dataclass
class TranscriptSegment:
    """Segment of transcript with timing."""
    start: float
    end: float
    text: str
    words: List[WordTimestamp]


@dataclass
class STTResult:
    """Result from STT processing."""
    segments: List[TranscriptSegment]
    full_text: str
    language: str
    confidence: Optional[float]
    provider: str
    model_version: str
    processing_time: Optional[float] = None


class STTProvider(Protocol):
    """Protocol for STT providers."""
    
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> STTResult:
        ...


class OpenAIProvider:
    """
    OpenAI Whisper API provider.
    Recommended for MVP - high accuracy with timestamps.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "whisper-1"  # Can upgrade to gpt-4o-transcribe
    
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> STTResult:
        """Transcribe audio using OpenAI Whisper API."""
        import time
        
        start_time = time.time()
        
        try:
            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=language or "en",
                    response_format="verbose_json",
                    timestamp_granularities=["word", "segment"]
                )
            
            processing_time = time.time() - start_time
            
            # Parse word-level timestamps
            words = []
            if hasattr(response, 'words') and response.words:
                for word_data in response.words:
                    words.append(WordTimestamp(
                        word=word_data.word,
                        start=word_data.start,
                        end=word_data.end,
                        confidence=getattr(word_data, 'confidence', None)
                    ))
            
            # Parse segments
            segments = []
            if hasattr(response, 'segments') and response.segments:
                for seg in response.segments:
                    # Find words within this segment
                    seg_words = [
                        w for w in words
                        if w.start >= seg.start and w.end <= seg.end
                    ]
                    segments.append(TranscriptSegment(
                        start=seg.start,
                        end=seg.end,
                        text=seg.text.strip(),
                        words=seg_words
                    ))
            
            # Calculate overall confidence
            confidences = [w.confidence for w in words if w.confidence is not None]
            avg_confidence = sum(confidences) / len(confidences) if confidences else None
            
            return STTResult(
                segments=segments,
                full_text=response.text.strip(),
                language=detected_language if (detected_language := getattr(response, 'language', None)) else (language or "en"),
                confidence=avg_confidence,
                provider="openai",
                model_version=self.model,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            raise STTError(f"OpenAI transcription failed: {e}")


class WhisperXLocalProvider:
    """
    Local WhisperX provider for development/testing.
    Requires whisperx package and GPU for good performance.
    """
    
    def __init__(self):
        self.device = settings.WHISPER_DEVICE
        self.compute_type = settings.WHISPER_COMPUTE_TYPE
        self.model_size = settings.WHISPER_MODEL
        self._model = None
    
    def _load_model(self):
        """Lazy load the WhisperX model."""
        if self._model is None:
            import whisperx
            self._model = whisperx.load_model(
                self.model_size,
                self.device,
                compute_type=self.compute_type
            )
        return self._model
    
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> STTResult:
        """Transcribe audio using local WhisperX."""
        import time
        import whisperx
        
        start_time = time.time()
        
        try:
            # Load audio
            audio = whisperx.load_audio(audio_path)
            
            # Transcribe
            model = self._load_model()
            result = model.transcribe(audio, batch_size=16, language=language)
            
            # Align words if model supports it
            model_a, metadata = whisperx.load_align_model(
                language_code=result["language"],
                device=self.device
            )
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                self.device,
                return_char_alignments=False
            )
            
            processing_time = time.time() - start_time
            
            # Parse segments
            segments = []
            for seg in result["segments"]:
                words = []
                for word_data in seg.get("words", []):
                    words.append(WordTimestamp(
                        word=word_data["word"],
                        start=word_data["start"],
                        end=word_data["end"],
                        confidence=word_data.get("score")
                    ))
                
                segments.append(TranscriptSegment(
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"].strip(),
                    words=words
                ))
            
            full_text = " ".join(seg.text for seg in segments)
            
            # Calculate confidence
            all_confidences = [
                w.confidence for seg in segments for w in seg.words
                if w.confidence is not None
            ]
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else None
            
            return STTResult(
                segments=segments,
                full_text=full_text,
                language=result["language"],
                confidence=avg_confidence,
                provider="whisperx-local",
                model_version=self.model_size,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"WhisperX transcription failed: {e}")
            raise STTError(f"WhisperX transcription failed: {e}")


class STTError(Exception):
    """Exception for STT errors."""
    pass


class STTService:
    """
    Main STT service that abstracts provider selection.
    
    Usage:
        service = STTService()
        result = await service.transcribe("/path/to/audio.wav")
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize STT service.
        
        Args:
            provider: 'openai', 'whisperx', or None (uses default)
        """
        self.provider_name = provider or getattr(settings, 'STT_PROVIDER', 'openai')
        self._provider = self._get_provider()
    
    def _get_provider(self) -> STTProvider:
        """Get the configured provider instance."""
        if self.provider_name == "openai":
            return OpenAIProvider()
        elif self.provider_name == "whisperx":
            return WhisperXLocalProvider()
        else:
            raise ValueError(f"Unknown STT provider: {self.provider_name}")
    
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        retry_with_backup: bool = True
    ) -> STTResult:
        """
        Transcribe audio file.
        
        Args:
            audio_path: Path to audio file
            language: Expected language code (e.g., 'en', 'es')
            retry_with_backup: If True, retry with backup provider on failure
            
        Returns:
            STTResult with segments and metadata
            
        Raises:
            STTError: If transcription fails
        """
        try:
            logger.info(f"Starting transcription with {self.provider_name}")
            result = await self._provider.transcribe(audio_path, language)
            logger.info(f"Transcription complete: {len(result.segments)} segments")
            return result
            
        except STTError as e:
            logger.error(f"Primary provider failed: {e}")
            
            # Retry with backup if configured
            if retry_with_backup and hasattr(settings, 'STT_BACKUP_PROVIDER'):
                backup_name = settings.STT_BACKUP_PROVIDER
                logger.info(f"Retrying with backup provider: {backup_name}")
                
                backup_provider = self._get_backup_provider(backup_name)
                return await backup_provider.transcribe(audio_path, language)
            
            raise
    
    def _get_backup_provider(self, name: str) -> STTProvider:
        """Get backup provider instance."""
        if name == "openai":
            return OpenAIProvider()
        elif name == "whisperx":
            return WhisperXLocalProvider()
        else:
            raise ValueError(f"Unknown backup provider: {name}")
    
    @staticmethod
    def extract_audio_from_video(video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio track from video file.
        
        Args:
            video_path: Path to video file
            output_path: Optional output path (uses temp file if not provided)
            
        Returns:
            Path to extracted audio file
        """
        import subprocess
        
        if output_path is None:
            import tempfile
            output_path = tempfile.mktemp(suffix=".wav")
        
        try:
            # Use ffmpeg to extract audio
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit
                "-ar", "16000",  # 16kHz (Whisper optimal)
                "-ac", "1",  # Mono
                "-y",  # Overwrite output
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Audio extracted to {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio extraction failed: {e}")
            raise STTError(f"Failed to extract audio: {e}")
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg.")
            raise STTError("ffmpeg not found. Please install ffmpeg.")
