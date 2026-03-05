"""
Feature Extraction Service for the Oracy AI platform.

Per MVP Section 2.2: Step 2 – Deterministic Feature Extraction

Extracts measurable proxies from transcript and audio:
- Physical: pace, pauses, fillers, volume, rhythm
- Linguistic: sentence complexity, vocabulary, clarity, register
- Cognitive: reason markers, structure, counterpoints, coherence
- Social-Emotional: audience reference, intention clarity, tone
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from django.conf import settings

from ..models import FeatureSignals

logger = logging.getLogger(__name__)


@dataclass
class ExtractedFeatures:
    """Container for all extracted features."""
    
    # Physical
    wpm: Optional[float] = None
    pause_ratio: Optional[float] = None
    pause_count: Optional[int] = None
    filler_frequency: Optional[float] = None
    filler_count: Optional[int] = None
    volume_variance: Optional[float] = None
    volume_mean: Optional[float] = None
    rhythm_stability: Optional[float] = None
    speech_rate_variance: Optional[float] = None
    
    # Linguistic
    sentence_count: Optional[int] = None
    sentence_length_mean: Optional[float] = None
    sentence_length_variance: Optional[float] = None
    vocabulary_diversity: Optional[float] = None
    unique_word_count: Optional[int] = None
    prompt_relevance: Optional[float] = None
    clarity_score: Optional[float] = None
    register_formality: Optional[float] = None
    
    # Cognitive
    reason_marker_count: Optional[int] = None
    reason_density: Optional[float] = None
    has_introduction: Optional[bool] = None
    has_conclusion: Optional[bool] = None
    structure_completeness: Optional[float] = None
    counterpoint_count: Optional[int] = None
    counterpoint_density: Optional[float] = None
    logical_connector_count: Optional[int] = None
    logical_connector_density: Optional[float] = None
    evidence_marker_count: Optional[int] = None
    evidence_density: Optional[float] = None
    coherence_score: Optional[float] = None
    
    # Social-Emotional
    audience_reference_count: Optional[int] = None
    audience_reference_frequency: Optional[float] = None
    intention_clarity: Optional[float] = None
    sentiment_positive: Optional[float] = None
    sentiment_negative: Optional[float] = None
    sentiment_neutral: Optional[float] = None
    sentiment_compound: Optional[float] = None
    confidence_score: Optional[float] = None
    
    # Quality
    quality_flag: str = "good"


class FeatureExtractionService:
    """
    Service for extracting features from transcripts and audio.
    
    Does NOT use LLM - uses deterministic analysis.
    """
    
    # Marker words for cognitive analysis
    REASON_MARKERS = [
        "because", "since", "as", "due to", "owing to", "given that",
        "the reason", "this is why", "that's why", "for example",
        "for instance", "such as", "like", "e.g.", "namely"
    ]
    
    COUNTERPOINT_MARKERS = [
        "however", "although", "though", "even though", "while",
        "whereas", "nevertheless", "nonetheless", "despite",
        "in spite of", "but", "yet", "on the other hand",
        "conversely", "alternatively"
    ]
    
    LOGICAL_CONNECTORS = [
        "therefore", "thus", "hence", "consequently", "as a result",
        "so", "accordingly", "because of this", "this means",
        "first", "second", "third", "firstly", "secondly", "thirdly",
        "next", "then", "finally", "lastly", "in conclusion",
        "to conclude", "in summary", "overall", "in addition",
        "furthermore", "moreover", "also", "besides", "similarly"
    ]
    
    EVIDENCE_MARKERS = [
        "evidence", "research", "study", "studies", "data",
        "statistics", "according to", "shows that", "demonstrates",
        "proves", "indicates", "suggests", "found that",
        "discovered", "reported"
    ]
    
    FILLER_WORDS = [
        "um", "uh", "er", "ah", "like", "you know", "sort of",
        "kind of", "basically", "literally", "actually", "so",
        "well", "right", "okay"
    ]
    
    AUDIENCE_REFERENCES = [
        "you", "your", "we", "our", "us", "everyone",
        "everybody", "listeners", "audience", "viewers"
    ]
    
    INTRODUCTION_MARKERS = [
        "today", "i'm going to", "i will", "let me", "i'd like to",
        "my topic", "i want to talk about", "this is about"
    ]
    
    CONCLUSION_MARKERS = [
        "in conclusion", "to conclude", "in summary", "to summarize",
        "finally", "lastly", "in closing", "overall"
    ]
    
    def __init__(self):
        self._sentiment_analyzer = None
        self._spacy_nlp = None
    
    def _get_spacy(self):
        """Lazy load spaCy model."""
        if self._spacy_nlp is None:
            try:
                import spacy
                self._spacy_nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found. Some features will be limited.")
                self._spacy_nlp = False
        return self._spacy_nlp if self._spacy_nlp else None
    
    def _get_sentiment_analyzer(self):
        """Lazy load sentiment analyzer."""
        if self._sentiment_analyzer is None:
            try:
                from nltk.sentiment import SentimentIntensityAnalyzer
                import nltk
                try:
                    nltk.data.find('vader_lexicon')
                except LookupError:
                    nltk.download('vader_lexicon')
                self._sentiment_analyzer = SentimentIntensityAnalyzer()
            except Exception as e:
                logger.warning(f"Could not load sentiment analyzer: {e}")
                self._sentiment_analyzer = False
        return self._sentiment_analyzer if self._sentiment_analyzer else None
    
    def extract_from_transcript(
        self,
        segments: List[Dict],
        full_text: str,
        prompt: str = "",
        duration_seconds: Optional[float] = None
    ) -> ExtractedFeatures:
        """
        Extract all features from transcript data.
        
        Args:
            segments: List of transcript segments with words/timings
            full_text: Complete transcript text
            prompt: The original prompt/topic
            duration_seconds: Total duration of recording
            
        Returns:
            ExtractedFeatures with all computed values
        """
        features = ExtractedFeatures()
        
        try:
            # Physical features
            physical = self._extract_physical_features(segments, duration_seconds)
            features.__dict__.update(physical)
            
            # Linguistic features
            linguistic = self._extract_linguistic_features(full_text)
            features.__dict__.update(linguistic)
            
            # Cognitive features
            cognitive = self._extract_cognitive_features(full_text)
            features.__dict__.update(cognitive)
            
            # Social-emotional features
            social = self._extract_social_emotional_features(full_text)
            features.__dict__.update(social)
            
            # Quality assessment
            features.quality_flag = self._assess_quality(features)
            
            logger.info(f"Feature extraction complete: {len(full_text.split())} words")
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            features.quality_flag = "poor"
        
        return features
    
    def _extract_physical_features(
        self,
        segments: List[Dict],
        duration_seconds: Optional[float]
    ) -> Dict:
        """Extract physical delivery features."""
        features = {}
        
        if not segments:
            return features
        
        # Flatten words list
        all_words = []
        for seg in segments:
            all_words.extend(seg.get("words", []))
        
        if not all_words:
            return features
        
        word_count = len(all_words)
        
        # Calculate duration from last word if not provided
        if duration_seconds is None and all_words:
            duration_seconds = all_words[-1].get("end", 0)
        
        if duration_seconds and duration_seconds > 0:
            # Words per minute
            features["wpm"] = round((word_count / duration_seconds) * 60, 2)
            
            # Calculate pauses
            pauses = []
            for i in range(1, len(all_words)):
                gap = all_words[i]["start"] - all_words[i-1]["end"]
                if gap > 0.5:  # Pause threshold: 0.5 seconds
                    pauses.append(gap)
            
            features["pause_count"] = len(pauses)
            pause_time = sum(pauses)
            features["pause_ratio"] = round(pause_time / duration_seconds, 4)
        
        # Filler words
        filler_count = 0
        for word_data in all_words:
            word = word_data.get("word", "").lower().strip(".,!?;")
            if word in self.FILLER_WORDS:
                filler_count += 1
        
        features["filler_count"] = filler_count
        if duration_seconds and duration_seconds > 0:
            features["filler_frequency"] = round((filler_count / duration_seconds) * 60, 2)
        
        # Rhythm stability (variance in inter-word intervals)
        if len(all_words) > 1:
            intervals = []
            for i in range(1, len(all_words)):
                interval = all_words[i]["start"] - all_words[i-1]["start"]
                intervals.append(interval)
            
            if intervals:
                mean_interval = np.mean(intervals)
                std_interval = np.std(intervals)
                # Stability: lower coefficient of variation = more stable
                if mean_interval > 0:
                    cv = std_interval / mean_interval
                    features["rhythm_stability"] = round(max(0, 1 - cv), 4)
        
        return features
    
    def _extract_linguistic_features(self, text: str) -> Dict:
        """Extract linguistic features."""
        features = {}
        
        # Clean text
        clean_text = text.lower()
        
        # Sentence tokenization (simple approach)
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        features["sentence_count"] = len(sentences)
        
        if sentences:
            # Sentence lengths
            sent_lengths = [len(s.split()) for s in sentences]
            features["sentence_length_mean"] = round(np.mean(sent_lengths), 2)
            features["sentence_length_variance"] = round(np.var(sent_lengths), 4)
        
        # Vocabulary diversity (Type-Token Ratio)
        words = re.findall(r'\b\w+\b', clean_text)
        unique_words = set(words)
        features["unique_word_count"] = len(unique_words)
        
        if words:
            features["vocabulary_diversity"] = round(len(unique_words) / len(words), 4)
        
        # Register/formality (simple heuristic based on word choice)
        formal_markers = [
            "furthermore", "moreover", "therefore", "consequently",
            "however", "nevertheless", "although", "whereas"
        ]
        informal_markers = [
            "like", "you know", "sort of", "kind of", "basically",
            "literally", "actually", "stuff", "things"
        ]
        
        formal_count = sum(1 for m in formal_markers if m in clean_text)
        informal_count = sum(1 for m in informal_markers if m in clean_text)
        total = formal_count + informal_count
        
        if total > 0:
            features["register_formality"] = round(formal_count / total, 4)
        else:
            features["register_formality"] = 0.5  # Neutral
        
        # Clarity score (inverse of filler density + sentence complexity)
        filler_density = features.get("filler_frequency", 0) / 100 if features.get("filler_frequency") else 0
        complexity = features.get("sentence_length_variance", 0) / 100 if features.get("sentence_length_variance") else 0
        features["clarity_score"] = round(max(0, 1 - filler_density - complexity), 4)
        
        return features
    
    def _extract_cognitive_features(self, text: str) -> Dict:
        """Extract cognitive features."""
        features = {}
        clean_text = text.lower()
        words = re.findall(r'\b\w+\b', clean_text)
        word_count = len(words) if words else 1
        
        # Reason markers
        reason_count = sum(1 for marker in self.REASON_MARKERS if marker in clean_text)
        features["reason_marker_count"] = reason_count
        features["reason_density"] = round((reason_count / word_count) * 100, 4)
        
        # Counterpoints
        counter_count = sum(1 for marker in self.COUNTERPOINT_MARKERS if marker in clean_text)
        features["counterpoint_count"] = counter_count
        features["counterpoint_density"] = round((counter_count / word_count) * 100, 4)
        
        # Logical connectors
        connector_count = sum(1 for marker in self.LOGICAL_CONNECTORS if marker in clean_text)
        features["logical_connector_count"] = connector_count
        features["logical_connector_density"] = round((connector_count / word_count) * 100, 4)
        
        # Evidence markers
        evidence_count = sum(1 for marker in self.EVIDENCE_MARKERS if marker in clean_text)
        features["evidence_marker_count"] = evidence_count
        features["evidence_density"] = round((evidence_count / word_count) * 100, 4)
        
        # Structure detection
        features["has_introduction"] = any(
            marker in clean_text[:200].lower()  # Check first 200 chars
            for marker in self.INTRODUCTION_MARKERS
        )
        features["has_conclusion"] = any(
            marker in clean_text[-200:].lower()  # Check last 200 chars
            for marker in self.CONCLUSION_MARKERS
        )
        
        # Structure completeness score
        structure_points = 0
        if features["has_introduction"]:
            structure_points += 0.3
        if features["has_conclusion"]:
            structure_points += 0.3
        # Add points for logical flow
        structure_points += min(0.4, features["logical_connector_density"] / 10)
        features["structure_completeness"] = round(structure_points, 4)
        
        # Coherence (based on connector density and structure)
        features["coherence_score"] = round(
            min(1.0, features["structure_completeness"] * 0.5 + 
                min(0.5, features["logical_connector_density"] / 5)),
            4
        )
        
        return features
    
    def _extract_social_emotional_features(self, text: str) -> Dict:
        """Extract social-emotional features."""
        features = {}
        clean_text = text.lower()
        words = re.findall(r'\b\w+\b', clean_text)
        word_count = len(words) if words else 1
        
        # Audience references
        audience_count = sum(1 for ref in self.AUDIENCE_REFERENCES if ref in clean_text)
        features["audience_reference_count"] = audience_count
        features["audience_reference_frequency"] = round((audience_count / word_count) * 100, 4)
        
        # Intention clarity (based on introduction markers + direct statements)
        intention_markers = ["i want", "i will", "my goal", "i aim", "the purpose"]
        intention_count = sum(1 for m in intention_markers if m in clean_text[:300])
        features["intention_clarity"] = round(min(1.0, intention_count * 0.3 + 0.2), 4)
        
        # Sentiment analysis
        sentiment = self._analyze_sentiment(text)
        features.update(sentiment)
        
        # Confidence score (based on hedging words inverse)
        hedging_words = ["maybe", "perhaps", "i think", "i guess", "possibly", "might"]
        hedge_count = sum(1 for h in hedging_words if h in clean_text)
        hedge_density = hedge_count / word_count
        features["confidence_score"] = round(max(0, 1 - hedge_density * 5), 4)
        
        return features
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text."""
        analyzer = self._get_sentiment_analyzer()
        
        if analyzer:
            scores = analyzer.polarity_scores(text)
            return {
                "sentiment_positive": round(scores["pos"], 4),
                "sentiment_negative": round(scores["neg"], 4),
                "sentiment_neutral": round(scores["neu"], 4),
                "sentiment_compound": round(scores["compound"], 4),
            }
        else:
            return {
                "sentiment_positive": None,
                "sentiment_negative": None,
                "sentiment_neutral": None,
                "sentiment_compound": None,
            }
    
    def _assess_quality(self, features: ExtractedFeatures) -> str:
        """Assess overall media/quality based on extracted features."""
        quality_issues = 0
        
        # Check for red flags
        if features.wpm and (features.wpm < 50 or features.wpm > 200):
            quality_issues += 1
        
        if features.pause_ratio and features.pause_ratio > 0.5:
            quality_issues += 1
        
        if features.filler_frequency and features.filler_frequency > 20:
            quality_issues += 1
        
        if features.clarity_score and features.clarity_score < 0.3:
            quality_issues += 1
        
        if quality_issues >= 2:
            return "poor"
        elif quality_issues == 1:
            return "fair"
        else:
            return "good"
    
    def extract_from_audio(
        self,
        audio_path: str,
        transcript_segments: List[Dict]
    ) -> Dict:
        """
        Extract audio-specific features (volume, etc.).
        
        Args:
            audio_path: Path to audio file
            transcript_segments: Transcript for timing reference
            
        Returns:
            Dict with audio features
        """
        features = {}
        
        try:
            import librosa
            
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Calculate RMS energy (volume) over time
            hop_length = int(sr * 0.025)  # 25ms frames
            rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
            
            features["volume_mean"] = round(float(np.mean(rms)), 6)
            features["volume_variance"] = round(float(np.var(rms)), 6)
            
        except ImportError:
            logger.warning("librosa not available for audio feature extraction")
        except Exception as e:
            logger.error(f"Audio feature extraction failed: {e}")
        
        return features
    
    def save_to_model(
        self,
        assessment_id: str,
        features: ExtractedFeatures,
        audio_features: Optional[Dict] = None
    ) -> FeatureSignals:
        """
        Save extracted features to the database.
        
        Args:
            assessment_id: UUID of the assessment
            features: Extracted features
            audio_features: Optional additional audio features
            
        Returns:
            Saved FeatureSignals instance
        """
        from apps.assessments.models import Assessment
        
        assessment = Assessment.objects.get(id=assessment_id)
        
        # Merge audio features
        feature_dict = features.__dict__.copy()
        if audio_features:
            feature_dict.update(audio_features)
        
        # Remove internal fields
        feature_dict.pop('_sentiment_analyzer', None)
        feature_dict.pop('_spacy_nlp', None)
        
        # Create or update FeatureSignals
        signals, created = FeatureSignals.objects.update_or_create(
            assessment=assessment,
            defaults=feature_dict
        )
        
        logger.info(f"Feature signals {'created' if created else 'updated'} for assessment {assessment_id}")
        
        return signals