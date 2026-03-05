"""
Evidence Candidate Generator Service for the Oracy AI platform.

Per MVP Section 2.4: Step 4 – Evidence Candidate Generation (Deterministic)

Generates 10-30 candidate segments that the LLM can select from for evidence.
Candidates are generated BEFORE LLM scoring to constrain evidence selection.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from ..models import EvidenceCandidate

logger = logging.getLogger(__name__)


@dataclass
class CandidateSegment:
    """Temporary representation of a candidate segment."""
    start_time: float
    end_time: float
    transcript_text: str
    type: str
    summary: str
    features: Dict
    relevant_strands: List[str]


class EvidenceCandidateGenerator:
    """
    Generates evidence clip candidates deterministically.
    
    The LLM may ONLY choose evidence from these candidates.
    This ensures evidence is grounded in actual transcript segments.
    """
    
    # Minimum and maximum clip duration
    MIN_CLIP_DURATION = 5.0  # seconds
    MAX_CLIP_DURATION = 30.0  # seconds
    
    # Reason density threshold
    REASON_DENSITY_THRESHOLD = 0.02  # 2 reason markers per 100 words
    
    def __init__(self):
        self.reason_markers = [
            "because", "since", "as", "due to", "for example",
            "for instance", "the reason", "this is why"
        ]
        self.filler_words = ["um", "uh", "er", "like", "you know"]
    
    def generate_candidates(
        self,
        segments: List[Dict],
        feature_signals: Dict,
        prompt: str = ""
    ) -> List[CandidateSegment]:
        """
        Generate all candidate segments from transcript.
        
        Args:
            segments: Transcript segments with word-level data
            feature_signals: Extracted feature signals
            prompt: Original assessment prompt
            
        Returns:
            List of CandidateSegment objects
        """
        candidates = []
        
        # Generate candidates from different strategies
        candidates.extend(self._generate_transcript_boundary_candidates(segments))
        candidates.extend(self._generate_reason_dense_candidates(segments))
        candidates.extend(self._generate_filler_heavy_candidates(segments))
        candidates.extend(self._generate_volume_variance_candidates(segments, feature_signals))
        candidates.extend(self._generate_intro_conclusion_candidates(segments))
        candidates.extend(self._generate_example_candidates(segments))
        candidates.extend(self._generate_counterpoint_candidates(segments))
        candidates.extend(self._generate_audience_reference_candidates(segments))
        
        # Remove duplicates and overlaps
        candidates = self._deduplicate_candidates(candidates)
        
        # Sort by start time
        candidates.sort(key=lambda x: x.start_time)
        
        logger.info(f"Generated {len(candidates)} evidence candidates")
        return candidates
    
    def _generate_transcript_boundary_candidates(
        self,
        segments: List[Dict]
    ) -> List[CandidateSegment]:
        """Generate candidates from natural transcript boundaries."""
        candidates = []
        
        for i, seg in enumerate(segments):
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            text = seg.get("text", "").strip()
            
            # Skip if too short or too long
            duration = end - start
            if duration < self.MIN_CLIP_DURATION or duration > self.MAX_CLIP_DURATION:
                continue
            
            candidates.append(CandidateSegment(
                start_time=start,
                end_time=end,
                transcript_text=text,
                type="transcript_boundary",
                summary=f"Segment {i+1}: {text[:100]}...",
                features={"word_count": len(text.split())},
                relevant_strands=self._determine_relevant_strands(text)
            ))
        
        return candidates
    
    def _generate_reason_dense_candidates(
        self,
        segments: List[Dict]
    ) -> List[CandidateSegment]:
        """Generate candidates from reason-dense sections."""
        candidates = []
        
        for seg in segments:
            text = seg.get("text", "").lower()
            words = text.split()
            word_count = len(words)
            
            if word_count < 10:
                continue
            
            # Count reason markers
            reason_count = sum(1 for marker in self.reason_markers if marker in text)
            density = reason_count / word_count if word_count > 0 else 0
            
            if density >= self.REASON_DENSITY_THRESHOLD and reason_count >= 2:
                start = seg.get("start", 0)
                end = seg.get("end", 0)
                
                # Ensure reasonable duration
                duration = end - start
                if duration > self.MAX_CLIP_DURATION:
                    # Try to shorten by focusing on reason-rich part
                    end = min(end, start + self.MAX_CLIP_DURATION)
                
                if duration >= self.MIN_CLIP_DURATION:
                    candidates.append(CandidateSegment(
                        start_time=start,
                        end_time=end,
                        transcript_text=seg.get("text", "").strip(),
                        type="reason_dense",
                        summary=f"Reason-dense section with {reason_count} markers",
                        features={
                            "reason_density": round(density, 4),
                            "reason_count": reason_count,
                            "word_count": word_count
                        },
                        relevant_strands=["cognitive", "linguistic"]
                    ))
        
        return candidates
    
    def _generate_filler_heavy_candidates(
        self,
        segments: List[Dict]
    ) -> List[CandidateSegment]:
        """Generate candidates from filler-heavy sections (for physical strand)."""
        candidates = []
        
        for seg in segments:
            words = seg.get("words", [])
            if len(words) < 20:
                continue
            
            # Count filler words
            filler_count = sum(
                1 for w in words
                if w.get("word", "").lower().strip(".,!?") in self.filler_words
            )
            
            filler_ratio = filler_count / len(words) if words else 0
            
            # Only flag sections with high filler usage
            if filler_ratio > 0.1:  # More than 10% fillers
                start = seg.get("start", 0)
                end = seg.get("end", 0)
                
                duration = end - start
                if duration >= self.MIN_CLIP_DURATION:
                    candidates.append(CandidateSegment(
                        start_time=start,
                        end_time=end,
                        transcript_text=seg.get("text", "").strip(),
                        type="filler_heavy",
                        summary=f"Section with {filler_ratio:.1%} filler words",
                        features={
                            "filler_count": filler_count,
                            "filler_ratio": round(filler_ratio, 4),
                            "word_count": len(words)
                        },
                        relevant_strands=["physical"]
                    ))
        
        return candidates
    
    def _generate_volume_variance_candidates(
        self,
        segments: List[Dict],
        feature_signals: Dict
    ) -> List[CandidateSegment]:
        """Generate candidates based on volume variance (requires audio analysis)."""
        # This would require audio feature data - simplified version
        # In practice, you'd analyze RMS energy within time windows
        candidates = []
        
        # If we have word-level timing, we can infer potential volume sections
        for seg in segments:
            words = seg.get("words", [])
            if len(words) < 10:
                continue
            
            # Look for punctuation that might indicate emphasis
            text = seg.get("text", "")
            if "!" in text or any(w.get("word", "").isupper() for w in words[:5]):
                start = seg.get("start", 0)
                end = seg.get("end", 0)
                duration = end - start
                
                if self.MIN_CLIP_DURATION <= duration <= self.MAX_CLIP_DURATION:
                    candidates.append(CandidateSegment(
                        start_time=start,
                        end_time=end,
                        transcript_text=text.strip(),
                        type="volume_variance",
                        summary="Potential emphasis or volume variation",
                        features={"emphasis_markers": text.count("!")},
                        relevant_strands=["physical", "social_emotional"]
                    ))
        
        return candidates
    
    def _generate_intro_conclusion_candidates(
        self,
        segments: List[Dict]
    ) -> List[CandidateSegment]:
        """Generate candidates for introduction and conclusion."""
        candidates = []
        
        if not segments:
            return candidates
        
        intro_markers = ["today", "i'm going to", "i will", "let me", "i'd like to"]
        conclusion_markers = ["in conclusion", "to conclude", "in summary", "finally"]
        
        # Check first few segments for introduction
        for seg in segments[:3]:
            text = seg.get("text", "").lower()
            if any(marker in text for marker in intro_markers):
                candidates.append(CandidateSegment(
                    start_time=seg.get("start", 0),
                    end_time=seg.get("end", 0),
                    transcript_text=seg.get("text", "").strip(),
                    type="introduction",
                    summary="Introduction section",
                    features={"section": "introduction"},
                    relevant_strands=["cognitive", "social_emotional"]
                ))
                break
        
        # Check last few segments for conclusion
        for seg in segments[-3:]:
            text = seg.get("text", "").lower()
            if any(marker in text for marker in conclusion_markers):
                candidates.append(CandidateSegment(
                    start_time=seg.get("start", 0),
                    end_time=seg.get("end", 0),
                    transcript_text=seg.get("text", "").strip(),
                    type="conclusion",
                    summary="Conclusion section",
                    features={"section": "conclusion"},
                    relevant_strands=["cognitive", "social_emotional"]
                ))
                break
        
        return candidates
    
    def _generate_example_candidates(
        self,
        segments: List[Dict]
    ) -> List[CandidateSegment]:
        """Generate candidates from example-giving sections."""
        candidates = []
        example_markers = ["for example", "for instance", "such as", "like when", "take"]
        
        for seg in segments:
            text = seg.get("text", "").lower()
            
            for marker in example_markers:
                if marker in text:
                    start = seg.get("start", 0)
                    end = seg.get("end", 0)
                    duration = end - start
                    
                    if self.MIN_CLIP_DURATION <= duration <= self.MAX_CLIP_DURATION:
                        candidates.append(CandidateSegment(
                            start_time=start,
                            end_time=end,
                            transcript_text=seg.get("text", "").strip(),
                            type="example_given",
                            summary=f"Example provided: {marker}",
                            features={"example_marker": marker},
                            relevant_strands=["cognitive"]
                        ))
                        break
        
        return candidates
    
    def _generate_counterpoint_candidates(
        self,
        segments: List[Dict]
    ) -> List[CandidateSegment]:
        """Generate candidates from counterpoint sections."""
        candidates = []
        counterpoint_markers = [
            "however", "although", "though", "but", "yet",
            "on the other hand", "conversely", "nevertheless"
        ]
        
        for seg in segments:
            text = seg.get("text", "").lower()
            
            for marker in counterpoint_markers:
                if marker in text:
                    start = seg.get("start", 0)
                    end = seg.get("end", 0)
                    duration = end - start
                    
                    if self.MIN_CLIP_DURATION <= duration <= self.MAX_CLIP_DURATION:
                        candidates.append(CandidateSegment(
                            start_time=start,
                            end_time=end,
                            transcript_text=seg.get("text", "").strip(),
                            type="counterpoint",
                            summary=f"Counterpoint/argumentation: {marker}",
                            features={"counterpoint_marker": marker},
                            relevant_strands=["cognitive"]
                        ))
                        break
        
        return candidates
    
    def _generate_audience_reference_candidates(
        self,
        segments: List[Dict]
    ) -> List[CandidateSegment]:
        """Generate candidates from audience-aware sections."""
        candidates = []
        audience_refs = ["you", "your", "we", "our", "us", "everyone", "listeners"]
        
        for seg in segments:
            text = seg.get("text", "").lower()
            words = text.split()
            
            if len(words) < 10:
                continue
            
            # Count audience references
            ref_count = sum(1 for ref in audience_refs if ref in words)
            ref_ratio = ref_count / len(words) if words else 0
            
            if ref_ratio > 0.05:  # More than 5% audience references
                start = seg.get("start", 0)
                end = seg.get("end", 0)
                duration = end - start
                
                if self.MIN_CLIP_DURATION <= duration <= self.MAX_CLIP_DURATION:
                    candidates.append(CandidateSegment(
                        start_time=start,
                        end_time=end,
                        transcript_text=seg.get("text", "").strip(),
                        type="audience_reference",
                        summary=f"Audience-aware section ({ref_ratio:.1%} references)",
                        features={
                            "audience_ref_count": ref_count,
                            "audience_ref_ratio": round(ref_ratio, 4)
                        },
                        relevant_strands=["social_emotional"]
                    ))
        
        return candidates
    
    def _determine_relevant_strands(self, text: str) -> List[str]:
        """Determine which strands a text segment might be relevant for."""
        text_lower = text.lower()
        strands = []
        
        # Physical: pace, clarity indicators
        physical_markers = ["clearly", "loud", "quiet", "fast", "slow", "paced"]
        if any(m in text_lower for m in physical_markers):
            strands.append("physical")
        
        # Linguistic: vocabulary, structure
        if len(text.split()) > 20:
            strands.append("linguistic")
        
        # Cognitive: reasoning, structure
        cognitive_markers = ["because", "therefore", "example", "reason"]
        if any(m in text_lower for m in cognitive_markers):
            strands.append("cognitive")
        
        # Social-emotional: audience, tone
        social_markers = ["you", "we", "feel", "think", "believe"]
        if any(m in text_lower for m in social_markers):
            strands.append("social_emotional")
        
        # Default to all if no specific markers
        if not strands:
            strands = ["physical", "linguistic", "cognitive", "social_emotional"]
        
        return strands
    
    def _deduplicate_candidates(
        self,
        candidates: List[CandidateSegment]
    ) -> List[CandidateSegment]:
        """Remove overlapping candidates, keeping the most specific ones."""
        if not candidates:
            return candidates
        
        # Sort by type priority and duration
        type_priority = {
            "reason_dense": 1,
            "example_given": 2,
            "counterpoint": 3,
            "introduction": 4,
            "conclusion": 5,
            "audience_reference": 6,
            "filler_heavy": 7,
            "volume_variance": 8,
            "transcript_boundary": 9,
        }
        
        candidates.sort(key=lambda x: (
            x.start_time,
            type_priority.get(x.type, 99)
        ))
        
        filtered = []
        for candidate in candidates:
            # Check for significant overlap with existing candidates
            overlap = False
            for existing in filtered:
                # Calculate overlap
                overlap_start = max(candidate.start_time, existing.start_time)
                overlap_end = min(candidate.end_time, existing.end_time)
                overlap_duration = overlap_end - overlap_start
                
                candidate_duration = candidate.end_time - candidate.start_time
                
                # If overlap is more than 50% of candidate, skip
                if overlap_duration > 0 and overlap_duration > candidate_duration * 0.5:
                    overlap = True
                    break
            
            if not overlap:
                filtered.append(candidate)
        
        return filtered
    
    def save_candidates(
        self,
        assessment_id: str,
        candidates: List[CandidateSegment]
    ) -> List[EvidenceCandidate]:
        """
        Save candidates to the database.
        
        Args:
            assessment_id: UUID of the assessment
            candidates: List of candidate segments
            
        Returns:
            List of saved EvidenceCandidate instances
        """
        from apps.assessments.models import Assessment
        
        assessment = Assessment.objects.get(id=assessment_id)
        
        # Delete existing candidates
        EvidenceCandidate.objects.filter(assessment=assessment).delete()
        
        saved = []
        for i, candidate in enumerate(candidates):
            ec = EvidenceCandidate.objects.create(
                assessment=assessment,
                candidate_id=f"clip_{i}",
                start_time=candidate.start_time,
                end_time=candidate.end_time,
                type=candidate.type,
                summary=candidate.summary,
                transcript_text=candidate.transcript_text,
                features=candidate.features,
                relevant_strands=candidate.relevant_strands
            )
            saved.append(ec)
        
        logger.info(f"Saved {len(saved)} evidence candidates for assessment {assessment_id}")
        return saved