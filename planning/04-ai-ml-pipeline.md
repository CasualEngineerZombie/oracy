# AI/ML Pipeline

## Overview

The Oracy AI assessment pipeline consists of 5 sequential stages, transforming raw video/audio into structured, teacher-verifiable assessment reports. Each stage is modular and can be independently versioned, scaled, or replaced.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           AI PIPELINE FLOW                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐ │
│   │   STT    │────▶│ Feature  │────▶│ Benchmark│────▶│ Evidence │────▶│  LLM     │ │
│   │  Step 1  │     │ Extract  │     │  Layer   │     │   Gen    │     │ Scoring  │ │
│   │          │     │  Step 2  │     │  Step 3  │     │  Step 4  │     │  Step 5  │ │
│   └──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘ │
│        │                 │               │               │               │        │
│        ▼                 ▼               ▼               ▼               ▼        │
│   ┌──────────────────────────────────────────────────────────────────────────┐   │
│   │                     OUTPUT: Draft Report                                  │   │
│   │  • Per-strand scores (Emerging/Expected/Exceeding)                       │   │
│   │  • 3-8 timestamped evidence clips per strand                             │   │
│   │  • 3 strengths + 3 next steps (mode-specific)                            │   │
│   │  • 1-2 student-friendly practice goals                                   │   │
│   │  • Confidence indicators per strand                                      │   │
│   └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Speech-to-Text (STT)

### Purpose
Generate a timestamped transcript from the audio track with word-level or segment-level timestamps.

### Input
- Audio file (WAV or MP4 audio track)
- Recording ID for correlation

### Output
```json
{
  "assessment_id": "uuid",
  "language": "en-GB",
  "duration_seconds": 124.5,
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 4.2,
      "text": "Today I'm going to explain photosynthesis.",
      "words": [
        {"word": "Today", "start": 0.0, "end": 0.4, "confidence": 0.98},
        {"word": "I'm", "start": 0.5, "end": 0.7, "confidence": 0.95},
        {"word": "going", "start": 0.8, "end": 1.0, "confidence": 0.97}
      ]
    }
  ],
  "full_text": "Today I'm going to explain photosynthesis...",
  "confidence_overall": 0.94
}
```

### Implementation Options

#### Option A: OpenAI Whisper API (Recommended for MVP)

```python
import openai

class WhisperSTTService:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    def transcribe(self, audio_path: str) -> Transcript:
        with open(audio_path, 'rb') as audio_file:
            response = self.client.audio.transcriptions.create(
                model="gpt-4o-transcribe",  # or "whisper-1"
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"]
            )
        
        return self._parse_response(response)
    
    def _parse_response(self, response) -> Transcript:
        # Convert OpenAI format to internal format
        return Transcript(
            segments=[
                Segment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                    words=[
                        Word(start=w.start, end=w.end, word=w.word, confidence=w.probability)
                        for w in seg.words
                    ]
                )
                for seg in response.segments
            ],
            confidence_overall=response.avg_logprob
        )
```

**Pros:**
- High accuracy across accents and ages
- Built-in timestamp support
- Cost-effective
- No infrastructure to manage

**Cons:**
- External dependency
- Data leaves AWS (consider for GDPR)

#### Option B: AWS Transcribe (Alternative)

```python
import boto3

class AWSTranscribeService:
    def __init__(self):
        self.client = boto3.client('transcribe')
    
    def transcribe(self, audio_s3_uri: str, job_name: str) -> str:
        # Start async transcription job
        self.client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': audio_s3_uri},
            MediaFormat='mp4',
            LanguageCode='en-GB',
            OutputBucketName='oracy-transcripts',
            Settings={
                'ShowSpeakerLabels': False,
                'ChannelIdentification': False
            }
        )
        
        # Poll for completion (in Celery task)
        return job_name
```

**Pros:**
- Native AWS integration
- HIPAA eligible
- Speaker diarization (future)

**Cons:**
- Async only (adds latency)
- Higher cost for short files
- Less accurate for child voices

#### Option C: Self-Hosted Whisper (Future)

Use `faster-whisper` or `whisper.cpp` on ECS GPU instances for:
- Full data sovereignty
- Predictable costs at scale
- Custom fine-tuning

### Service Interface

Abstract STT behind an interface for easy swapping:

```python
from abc import ABC, abstractmethod
from typing import Protocol

class STTService(Protocol):
    @abstractmethod
    def transcribe(self, audio_path: str) -> Transcript:
        """Generate timestamped transcript."""
        ...
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether real-time transcription is supported."""
        ...

# Usage
stt_service: STTService = WhisperSTTService(api_key)  # or AWSTranscribeService()
transcript = stt_service.transcribe(audio_path)
```

---

## Step 2: Deterministic Feature Extraction

### Purpose
Extract measurable, objective signals from audio and transcript WITHOUT using LLMs. These features serve as inputs to the benchmarking layer.

### Philosophy
- **Do NOT use LLMs for raw signal measurement**
- Use established audio processing and NLP libraries
- Store all extracted features for auditability and future model training

### Physical Features (Audio)

| Feature | Method | Library |
|---------|--------|---------|
| Words per minute (WPM) | Word count / duration | librosa + transcript |
| Pause ratio | Silence detection / total duration | webrtcvad |
| Filler word frequency | Regex matching on transcript | re (built-in) |
| Volume variability | RMS energy variance | librosa |
| Rhythm stability | Tempo estimation variance | librosa.beat |
| Pitch variation | F0 (fundamental frequency) std | librosa |

```python
import librosa
import numpy as np
from pydub import AudioSegment
import webrtcvad

class PhysicalFeatureExtractor:
    def __init__(self):
        self.vad = webrtcvad.Vad(2)  # Aggressiveness 0-3
        self.filler_words = {'um', 'uh', 'er', 'ah', 'like', 'you know'}
    
    def extract(self, audio_path: str, transcript: Transcript) -> PhysicalFeatures:
        # Load audio
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Words per minute
        word_count = len(transcript.all_words())
        wpm = (word_count / duration) * 60
        
        # Pause analysis using VAD
        pauses = self._detect_pauses(y, sr)
        pause_ratio = sum(p['duration'] for p in pauses) / duration
        
        # Filler words
        filler_count = sum(
            1 for word in transcript.all_words() 
            if word.lower() in self.filler_words
        )
        filler_frequency = filler_count / duration  # per second
        
        # Volume variability (RMS energy)
        rms = librosa.feature.rms(y=y)[0]
        volume_variance = np.var(rms)
        
        # Rhythm/tempo stability
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_intervals = np.diff(librosa.frames_to_time(beat_frames, sr=sr))
        rhythm_stability = 1.0 / (np.std(beat_intervals) + 1e-6)
        
        return PhysicalFeatures(
            wpm=wpm,
            pause_ratio=pause_ratio,
            filler_frequency=filler_frequency,
            volume_variance=volume_variance,
            rhythm_stability=rhythm_stability
        )
    
    def _detect_pauses(self, y: np.ndarray, sr: int) -> List[Pause]:
        # Convert to pcm16 for webrtcvad
        pcm_data = (y * 32767).astype(np.int16).tobytes()
        
        # Frame duration must be 10, 20, or 30ms
        frame_duration_ms = 30
        frame_length = int(sr * frame_duration_ms / 1000)
        
        pauses = []
        is_speech = False
        pause_start = 0
        
        for i in range(0, len(pcm_data), frame_length * 2):  # 2 bytes per sample
            frame = pcm_data[i:i + frame_length * 2]
            if len(frame) < frame_length * 2:
                break
            
            try:
                speech = self.vad.is_speech(frame, sr)
            except:
                speech = False
            
            if not speech and is_speech:
                pause_start = i / (sr * 2)  # Convert to seconds
                is_speech = False
            elif speech and not is_speech:
                pause_end = i / (sr * 2)
                if pause_end - pause_start > 0.5:  # Minimum 500ms pause
                    pauses.append(Pause(start=pause_start, end=pause_end))
                is_speech = True
        
        return pauses
```

### Linguistic Features (Transcript)

| Feature | Method | Library |
|---------|--------|---------|
| Sentence length variance | Parse sentences, calculate std | spaCy |
| Vocabulary diversity | Type-Token Ratio (TTR) | spaCy |
| Prompt relevance | TF-IDF cosine similarity | scikit-learn |
| Clarity markers | Flesch Reading Ease score | textstat |
| Register formality | Formality index | Custom rules |

```python
import spacy
from textstat import flesch_reading_ease
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class LinguisticFeatureExtractor:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.vectorizer = TfidfVectorizer(stop_words='english')
    
    def extract(self, transcript: Transcript, prompt: str) -> LinguisticFeatures:
        full_text = transcript.full_text
        doc = self.nlp(full_text)
        
        # Sentence length variance
        sentences = list(doc.sents)
        sent_lengths = [len(sent) for sent in sentences]
        sentence_length_variance = np.var(sent_lengths) if len(sent_lengths) > 1 else 0
        
        # Vocabulary diversity (TTR)
        tokens = [token.text.lower() for token in doc if not token.is_punct]
        unique_tokens = set(tokens)
        ttr = len(unique_tokens) / len(tokens) if tokens else 0
        
        # Prompt relevance
        prompt_relevance = self._calculate_relevance(full_text, prompt)
        
        # Clarity (Flesch Reading Ease)
        # Higher = easier to read
        clarity_score = flesch_reading_ease(full_text)
        
        # Register detection (simple heuristic)
        formal_markers = ['furthermore', 'however', 'therefore', 'consequently']
        informal_markers = ['like', 'yeah', 'gonna', 'wanna']
        
        formal_count = sum(1 for m in formal_markers if m in full_text.lower())
        informal_count = sum(1 for m in informal_markers if m in full_text.lower())
        register_score = (formal_count - informal_count) / len(sentences) if sentences else 0
        
        return LinguisticFeatures(
            sentence_length_variance=sentence_length_variance,
            vocabulary_diversity=ttr,
            prompt_relevance=prompt_relevance,
            clarity_score=clarity_score,
            register_formality=register_score
        )
    
    def _calculate_relevance(self, text: str, prompt: str) -> float:
        # Simple TF-IDF cosine similarity
        try:
            tfidf = self.vectorizer.fit_transform([text, prompt])
            return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
        except:
            return 0.5  # Neutral if calculation fails
```

### Cognitive Features (Transcript)

| Feature | Method | Markers |
|---------|--------|---------|
| Reason markers | Keyword frequency | "because", "for example", "such as" |
| Structure signals | Section detection | Intro/body/conclusion markers |
| Counterpoint markers | Keyword frequency | "however", "although", "on the other hand" |
| Logical connectors | Keyword frequency | "firstly", "then", "finally", "therefore" |
| Coherence | Entity chain analysis | spaCy coreference |

```python
class CognitiveFeatureExtractor:
    REASON_MARKERS = ['because', 'since', 'as', 'for example', 'such as', 'like']
    COUNTERPOINT_MARKERS = ['however', 'although', 'though', 'but', 'yet', 'on the other hand', 'nevertheless']
    LOGICAL_CONNECTORS = ['first', 'firstly', 'second', 'secondly', 'then', 'next', 'finally', 'therefore', 'thus', 'so']
    STRUCTURE_MARKERS = {
        'intro': ['today', "i'm going to", "i will", "let me explain", "i'd like to"],
        'conclusion': ['in conclusion', 'to summarize', 'in summary', 'finally', 'overall']
    }
    
    def extract(self, transcript: Transcript) -> CognitiveFeatures:
        text_lower = transcript.full_text.lower()
        word_count = len(transcript.all_words())
        
        # Reason density
        reason_count = sum(text_lower.count(m) for m in self.REASON_MARKERS)
        reason_density = reason_count / word_count if word_count > 0 else 0
        
        # Counterpoint usage
        counterpoint_count = sum(text_lower.count(m) for m in self.COUNTERPOINT_MARKERS)
        counterpoint_density = counterpoint_count / word_count if word_count > 0 else 0
        
        # Logical connector usage
        connector_count = sum(text_lower.count(m) for m in self.LOGICAL_CONNECTORS)
        connector_density = connector_count / word_count if word_count > 0 else 0
        
        # Structure detection
        has_intro = any(m in text_lower for m in self.STRUCTURE_MARKERS['intro'])
        has_conclusion = any(m in text_lower for m in self.STRUCTURE_MARKERS['conclusion'])
        structure_score = (int(has_intro) + int(has_conclusion)) / 2
        
        return CognitiveFeatures(
            reason_density=reason_density,
            counterpoint_density=counterpoint_density,
            logical_connector_density=connector_density,
            structure_completeness=structure_score
        )
```

### Social-Emotional Features (Solo Mode)

| Feature | Method | Markers |
|---------|--------|---------|
| Audience reference | Keyword frequency | "you", "your", "we", "our" |
| Intention clarity | Confidence markers | "I believe", "I think", "definitely" |
| Tone markers | Sentiment + intensity | spaCy sentiment or VADER |

```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class SocialEmotionalFeatureExtractor:
    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def extract(self, transcript: Transcript) -> SocialEmotionalFeatures:
        text = transcript.full_text.lower()
        word_count = len(transcript.all_words())
        
        # Audience reference frequency
        audience_refs = ['you', 'your', 'we', 'our', 'us']
        audience_count = sum(text.count(f' {ref} ') + text.count(f' {ref}.') for ref in audience_refs)
        audience_reference_frequency = audience_count / word_count if word_count > 0 else 0
        
        # Intention clarity (confidence markers)
        confidence_markers = ['definitely', 'certainly', 'absolutely', 'clearly', 'obviously']
        hedging_markers = ['maybe', 'perhaps', 'possibly', 'might', 'could be']
        
        confidence_count = sum(text.count(m) for m in confidence_markers)
        hedging_count = sum(text.count(m) for m in hedging_markers)
        intention_clarity = (confidence_count - hedging_count) / word_count if word_count > 0 else 0
        
        # Tone analysis
        sentiment = self.sentiment_analyzer.polarity_scores(transcript.full_text)
        
        return SocialEmotionalFeatures(
            audience_reference_frequency=audience_reference_frequency,
            intention_clarity=intention_clarity,
            sentiment_positive=sentiment['pos'],
            sentiment_negative=sentiment['neg'],
            sentiment_neutral=sentiment['neu'],
            sentiment_compound=sentiment['compound']
        )
```

### Feature Storage

All extracted features stored in database:

```python
class FeatureSignals(models.Model):
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE)
    
    # Physical
    wpm = models.FloatField()
    pause_ratio = models.FloatField()
    filler_frequency = models.FloatField()
    volume_variance = models.FloatField()
    rhythm_stability = models.FloatField()
    
    # Linguistic
    sentence_length_variance = models.FloatField()
    vocabulary_diversity = models.FloatField()
    prompt_relevance = models.FloatField()
    clarity_score = models.FloatField()
    register_formality = models.FloatField()
    
    # Cognitive
    reason_density = models.FloatField()
    counterpoint_density = models.FloatField()
    logical_connector_density = models.FloatField()
    structure_completeness = models.FloatField()
    
    # Social-emotional
    audience_reference_frequency = models.FloatField()
    intention_clarity = models.FloatField()
    sentiment_compound = models.FloatField()
    
    # Metadata
    extracted_at = models.DateTimeField(auto_now_add=True)
    quality_flag = models.CharField(max_length=20)  # 'good', 'fair', 'poor'
```

---

## Step 3: Benchmarking Layer (Core IP)

### Purpose
The Benchmarking Layer is the core intellectual property of Oracy AI. It translates extracted features into band levels (Emerging/Expected/Exceeding) based on age-appropriate, mode-specific rubrics.

### Benchmark Definition Language (BDL)

JSON-based structured format for rubric definitions:

```json
{
  "version": "1.0.0",
  "age_band": "11-12",
  "mode": "explaining",
  "created_at": "2026-03-01",
  "strands": {
    "physical": {
      "subskills": [
        {
          "name": "pace_and_fluency",
          "weight": 0.4,
          "bands": {
            "emerging": {
              "description": "Frequent pauses, hesitations, or rushed speech that hinders clarity",
              "evidence_conditions": [
                {"feature": "wpm", "operator": "not_between", "values": [100, 160]},
                {"feature": "pause_ratio", "operator": ">", "value": 0.3}
              ],
              "disallowed_shortcuts": ["reading from notes without adaptation"]
            },
            "expected": {
              "description": "Generally steady pace with appropriate pauses for understanding",
              "evidence_conditions": [
                {"feature": "wpm", "operator": "between", "values": [110, 150]},
                {"feature": "pause_ratio", "operator": "between", "values": [0.15, 0.25]}
              ]
            },
            "exceeding": {
              "description": "Varied pace used deliberately for emphasis and engagement",
              "evidence_conditions": [
                {"feature": "wpm", "operator": "between", "values": [120, 160]},
                {"feature": "pause_ratio", "operator": "between", "values": [0.2, 0.3]},
                {"feature": "rhythm_stability", "operator": ">", "value": 0.7}
              ]
            }
          }
        },
        {
          "name": "vocal_clarity",
          "weight": 0.3,
          "bands": { ... }
        },
        {
          "name": "use_of_fillers",
          "weight": 0.3,
          "bands": { ... }
        }
      ]
    },
    "linguistic": { ... },
    "cognitive": { ... },
    "social_emotional": { ... }
  }
}
```

### BDL Interpreter

```python
from typing import Dict, List, Any
import operator

class BenchmarkEngine:
    """Interprets BDL and applies to extracted features."""
    
    OPERATORS = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
        'between': lambda x, vals: vals[0] <= x <= vals[1],
        'not_between': lambda x, vals: not (vals[0] <= x <= vals[1])
    }
    
    def __init__(self, bdl_path: str):
        self.bdl = self._load_bdl(bdl_path)
    
    def evaluate(self, strand: str, features: Dict[str, float]) -> StrandEvaluation:
        """Evaluate a single strand against benchmarks."""
        strand_def = self.bdl['strands'][strand]
        
        subskill_scores = []
        for subskill in strand_def['subskills']:
            band_scores = self._score_subskill(subskill, features)
            best_band = max(band_scores, key=band_scores.get)
            subskill_scores.append({
                'name': subskill['name'],
                'band': best_band,
                'confidence': band_scores[best_band],
                'weight': subskill['weight']
            })
        
        # Weighted aggregation
        band_weights = {'emerging': 1, 'expected': 2, 'exceeding': 3}
        weighted_score = sum(
            band_weights[s['band']] * s['weight'] * s['confidence']
            for s in subskill_scores
        ) / sum(s['weight'] for s in subskill_scores)
        
        # Map back to band
        if weighted_score < 1.5:
            overall_band = 'emerging'
        elif weighted_score < 2.5:
            overall_band = 'expected'
        else:
            overall_band = 'exceeding'
        
        return StrandEvaluation(
            strand=strand,
            band=overall_band,
            confidence=self._calculate_confidence(subskill_scores),
            subskills=subskill_scores
        )
    
    def _score_subskill(self, subskill: Dict, features: Dict) -> Dict[str, float]:
        """Score a subskill against all bands."""
        scores = {}
        for band_name, band_def in subskill['bands'].items():
            score = self._evaluate_conditions(band_def['evidence_conditions'], features)
            scores[band_name] = score
        return scores
    
    def _evaluate_conditions(self, conditions: List[Dict], features: Dict) -> float:
        """Evaluate evidence conditions and return match score (0-1)."""
        if not conditions:
            return 0.5
        
        matches = 0
        for condition in conditions:
            feature_value = features.get(condition['feature'])
            if feature_value is None:
                continue
            
            op = self.OPERATORS[condition['operator']]
            
            if 'values' in condition:
                if op(feature_value, condition['values']):
                    matches += 1
            elif op(feature_value, condition['value']):
                matches += 1
        
        return matches / len(conditions) if conditions else 0.5
```

### Versioning

Benchmarks are versioned and immutable:

```python
class BenchmarkVersion(models.Model):
    version = models.CharField(max_length=20, primary_key=True)
    age_band = models.CharField(max_length=10)
    mode = models.CharField(max_length=20)
    definition = models.JSONField()  # Full BDL
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['age_band', 'mode', 'version']
```

---

## Step 4: Evidence Candidate Generation

### Purpose
Generate 10-30 candidate video segments that COULD serve as evidence for the assessment. The LLM is constrained to choose from these candidates only.

### Candidate Generation Strategy

```python
class EvidenceCandidateGenerator:
    """Generate timestamped evidence candidates from transcript and features."""
    
    def generate(
        self,
        transcript: Transcript,
        features: FeatureSignals,
        target_count: int = 20
    ) -> List[EvidenceCandidate]:
        """Generate diverse evidence candidates."""
        
        candidates = []
        
        # 1. Transcript boundaries (natural breaks)
        boundary_candidates = self._from_transcript_boundaries(transcript)
        candidates.extend(boundary_candidates)
        
        # 2. High reason-density segments
        reason_candidates = self._from_reason_density(transcript)
        candidates.extend(reason_candidates)
        
        # 3. Filler-heavy sections (areas for improvement)
        filler_candidates = self._from_filler_sections(transcript)
        candidates.extend(filler_candidates)
        
        # 4. Volume variance sections (emphasis or uncertainty)
        volume_candidates = self._from_volume_sections(transcript, features)
        candidates.extend(volume_candidates)
        
        # 5. Prompt relevance peaks
        relevance_candidates = self._from_prompt_relevance(transcript)
        candidates.extend(relevance_candidates)
        
        # Remove overlaps and limit
        candidates = self._deduplicate_and_select(candidates, target_count)
        
        return candidates
    
    def _from_transcript_boundaries(self, transcript: Transcript) -> List[EvidenceCandidate]:
        """Generate candidates from natural speech boundaries."""
        candidates = []
        
        for segment in transcript.segments:
            # Only segments of reasonable length (10-30 seconds)
            duration = segment.end - segment.start
            if 10 <= duration <= 30:
                candidates.append(EvidenceCandidate(
                    start=segment.start,
                    end=segment.end,
                    type='transcript_boundary',
                    summary=segment.text[:200],
                    features={'duration': duration, 'word_count': len(segment.words)}
                ))
        
        return candidates
    
    def _from_reason_density(self, transcript: Transcript) -> List[EvidenceCandidate]:
        """Find segments with high reasoning density."""
        reason_markers = ['because', 'for example', 'such as', 'therefore']
        candidates = []
        
        # Sliding window over transcript
        window_size = 20  # words
        stride = 10
        
        words = transcript.all_words()
        for i in range(0, len(words) - window_size, stride):
            window = words[i:i + window_size]
            window_text = ' '.join([w.word for w in window]).lower()
            
            reason_count = sum(window_text.count(m) for m in reason_markers)
            density = reason_count / window_size
            
            if density > 0.15:  # Threshold for high reasoning
                start = window[0].start
                end = window[-1].end
                
                # Expand to make 10-30 second clips
                if end - start < 10:
                    end = min(start + 10, transcript.duration)
                elif end - start > 30:
                    end = start + 30
                
                candidates.append(EvidenceCandidate(
                    start=start,
                    end=end,
                    type='reason_dense',
                    summary=window_text[:200],
                    features={'reason_density': density}
                ))
        
        return candidates
    
    def _deduplicate_and_select(
        self,
        candidates: List[EvidenceCandidate],
        target_count: int
    ) -> List[EvidenceCandidate]:
        """Remove overlapping candidates and select diverse set."""
        # Sort by type to ensure diversity
        by_type = defaultdict(list)
        for c in candidates:
            by_type[c.type].append(c)
        
        selected = []
        type_cycle = cycle(by_type.keys())
        
        while len(selected) < target_count and any(by_type.values()):
            type_key = next(type_cycle)
            if by_type[type_key]:
                candidate = by_type[type_key].pop(0)
                
                # Check for overlap with selected
                overlaps = any(
                    self._segments_overlap(candidate, s)
                    for s in selected
                )
                
                if not overlaps:
                    selected.append(candidate)
        
        return selected
    
    def _segments_overlap(self, a: EvidenceCandidate, b: EvidenceCandidate) -> bool:
        """Check if two segments overlap significantly (>50%)."""
        overlap_start = max(a.start, b.start)
        overlap_end = min(a.end, b.end)
        
        if overlap_start >= overlap_end:
            return False
        
        overlap_duration = overlap_end - overlap_start
        a_duration = a.end - a.start
        b_duration = b.end - b.start
        
        return overlap_duration > min(a_duration, b_duration) * 0.5
```

---

## Step 5: Rubric-Constrained LLM Scoring

### Purpose
Use an LLM to:
1. Map signals + transcript to band per strand
2. Select valid evidence clips (from candidates only)
3. Generate justification text
4. Produce strengths, next steps, and goals

### Constraints
- **MUST NOT invent timestamps** - only use provided candidates
- **MUST use structured JSON output**
- **MUST reference rubric descriptors**
- **MUST output confidence scores**
- **MUST state if insufficient evidence**

### Prompt Engineering

```python
RUBRIC_SCORING_PROMPT = """You are an expert oracy assessor evaluating a student's spoken performance.

## ASSESSMENT CONTEXT
- Student Age Band: {age_band}
- Mode of Talk: {mode}
- Prompt/Topic: {prompt}

## BENCHMARK DEFINITIONS
{benchmark_json}

## EXTRACTED FEATURES
{features_json}

## TRANSCRIPT
{transcript_text}

## EVIDENCE CANDIDATES (MUST select from these ONLY)
{candidates_json}

## SCORING INSTRUCTIONS

For each of the 4 strands (physical, linguistic, cognitive, social-emotional):

1. Evaluate against the benchmark definitions for this age band and mode
2. Assign a band level: "emerging", "expected", or "exceeding"
3. Select 3-8 evidence clip IDs from the candidates above
4. Write a justification (2-3 sentences) referencing specific rubric language
5. Assign a confidence score (0.0-1.0) based on evidence quality

If there is insufficient evidence for a strand, set band to "insufficient_evidence" and explain why.

## MODE-SPECIFIC FEEDBACK

Generate feedback that is SPECIFIC to the {mode} mode:

- 3 strengths with mode-specific language (e.g., for "persuading": "effective use of rhetorical questions")
- 3 next steps tied to mode requirements
- 1-2 student-friendly practice goals

## OUTPUT FORMAT

Respond with ONLY a valid JSON object matching this schema:

{{
  "physical": {{
    "band": "emerging|expected|exceeding|insufficient_evidence",
    "confidence": 0.0-1.0,
    "evidence_clip_ids": ["id1", "id2", ...],
    "justification": "string referencing rubric descriptors"
  }},
  "linguistic": {{ ... }},
  "cognitive": {{ ... }},
  "social_emotional": {{ ... }},
  "feedback": {{
    "strengths": ["string1", "string2", "string3"],
    "next_steps": ["string1", "string2", "string3"],
    "goals": ["string1"]
  }}
}}
"""
```

### Implementation

```python
import json
from openai import OpenAI

class LLMScoringService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def score(
        self,
        assessment: Assessment,
        features: FeatureSignals,
        transcript: Transcript,
        candidates: List[EvidenceCandidate],
        benchmark: BenchmarkVersion
    ) -> DraftReport:
        """Generate AI draft report using LLM."""
        
        # Prepare candidates JSON with IDs
        candidates_json = [
            {
                'id': f'clip_{i}',
                'start': c.start,
                'end': c.end,
                'type': c.type,
                'summary': c.summary
            }
            for i, c in enumerate(candidates)
        ]
        
        prompt = RUBRIC_SCORING_PROMPT.format(
            age_band=assessment.age_band,
            mode=assessment.mode,
            prompt=assessment.prompt,
            benchmark_json=json.dumps(benchmark.definition, indent=2),
            features_json=self._features_to_json(features),
            transcript_text=transcript.full_text[:5000],  # Limit context
            candidates_json=json.dumps(candidates_json, indent=2)
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o",  # or "gpt-4o-2024-08-06"
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise oracy assessment evaluator. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Low temperature for consistency
            max_tokens=4000
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate and map clip IDs back to timestamps
        validated = self._validate_and_map_clips(result, candidates)
        
        return DraftReport(
            assessment=assessment,
            physical_score=validated['physical'],
            linguistic_score=validated['linguistic'],
            cognitive_score=validated['cognitive'],
            social_emotional_score=validated['social_emotional'],
            feedback=validated['feedback'],
            generated_at=timezone.now()
        )
    
    def _validate_and_map_clips(
        self,
        result: Dict,
        candidates: List[EvidenceCandidate]
    ) -> Dict:
        """Validate clip IDs exist and map to actual timestamps."""
        candidates_by_id = {f'clip_{i}': c for i, c in enumerate(candidates)}
        
        for strand in ['physical', 'linguistic', 'cognitive', 'social_emotional']:
            strand_data = result[strand]
            valid_clip_ids = [
                cid for cid in strand_data['evidence_clip_ids']
                if cid in candidates_by_id
            ]
            
            # If LLM hallucinated clip IDs, flag with low confidence
            if len(valid_clip_ids) < len(strand_data['evidence_clip_ids']):
                strand_data['confidence'] *= 0.5
                strand_data['validation_warning'] = 'Some clip IDs were invalid'
            
            strand_data['evidence_clips'] = [
                {
                    'id': cid,
                    'start': candidates_by_id[cid].start,
                    'end': candidates_by_id[cid].end
                }
                for cid in valid_clip_ids
            ]
        
        return result
```

### Fallback/Retry Strategy

```python
class ResilientLLMScorer:
    def __init__(self, primary_key: str, fallback_key: str = None):
        self.primary = LLMScoringService(primary_key)
        self.fallback = LLMScoringService(fallback_key) if fallback_key else None
    
    def score_with_retry(self, *args, **kwargs) -> DraftReport:
        """Attempt scoring with fallback on failure."""
        try:
            return self.primary.score(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}")
            
            if self.fallback:
                return self.fallback.score(*args, **kwargs)
            
            # Return empty draft with error flag
            return DraftReport(
                error=True,
                error_message=str(e)
            )
```

---

## Model Selection Summary

| Component | Primary | Fallback | Future |
|-----------|---------|----------|--------|
| **STT** | OpenAI Whisper API | AWS Transcribe | Self-hosted Whisper |
| **LLM Scoring** | GPT-4o | Claude 3.5 Sonnet | Fine-tuned model |
| **Feature Extraction** | Python libraries | - | - |
| **Benchmarking** | Custom BDL | - | ML-based classifier |

### Cost Estimates (per assessment)

| Component | Cost |
|-----------|------|
| STT (OpenAI) | ~$0.006/minute (~$0.01 for 2-min recording) |
| Feature Extraction | $0 (compute only) |
| LLM Scoring | ~$0.02-0.05 per assessment |
| **Total** | **~$0.03-0.06 per assessment** |

### Quality Assurance

1. **Confidence Thresholds**:
   - confidence >= 0.8: High confidence
   - 0.5 <= confidence < 0.8: Medium confidence (flag for review)
   - confidence < 0.5: Low confidence (require teacher review)

2. **Validation Rules**:
   - Clip timestamps must be within video duration
   - No duplicate clips across strands
   - All scores must map to valid bands

3. **Monitoring**:
   - Track LLM token usage
   - Log model versions used
   - Monitor confidence score distributions
   - Alert on high error rates
