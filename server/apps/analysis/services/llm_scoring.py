"""
LLM Scoring Service for the Oracy AI platform.

Per MVP Section 2.5: Step 5 – Rubric-Constrained LLM Scoring

Uses LLM to:
- Map signals + transcript to band per strand
- Select valid evidence clips (from candidates only)
- Generate justification text
- Produce strengths / next steps / goals

Strict requirements:
- Use structured JSON schema for output
- Output must include strand score, evidence clip IDs, justification
- Must state if insufficient evidence
- Must output strand-level confidence score
- Must NOT invent timestamps
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class StrandScore:
    """Score for a single strand."""
    band: str  # emerging, expected, exceeding
    confidence: float
    evidence_clips: List[str]
    justification: str
    subskills: Optional[Dict] = None


@dataclass
class Feedback:
    """Feedback structure."""
    strengths: List[Dict]  # [{"text": "...", "strand": "...", "evidence": "..."}]
    next_steps: List[Dict]  # [{"text": "...", "strand": "...", "specific": true}]
    goals: List[str]  # Student-friendly practice goals


@dataclass
class ScoringResult:
    """Complete scoring result."""
    physical: StrandScore
    linguistic: StrandScore
    cognitive: StrandScore
    social_emotional: StrandScore
    feedback: Feedback
    overall_confidence: float
    warnings: List[str]
    eal_scaffolds: Optional[Dict] = None


class LLMScoringService:
    """
    Service for rubric-constrained LLM scoring.
    
    Uses LiteLLM for provider abstraction, supporting OpenAI, Anthropic, etc.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize scoring service.
        
        Args:
            model: LiteLLM model string (e.g., 'openai/gpt-4o', 'anthropic/claude-3-sonnet')
        """
        self.model = model or getattr(settings, 'LITELLM_MODEL', 'gpt-4o-mini')
        self.fallback_models = getattr(settings, 'LITELLM_FALLBACK_MODELS', [])
    
    async def score_assessment(
        self,
        assessment_id: str,
        transcript_segments: List[Dict],
        feature_signals: Dict,
        evidence_candidates: List,
        benchmark_definition: Dict,
        prompt: str,
        is_eal: bool = False
    ) -> ScoringResult:
        """
        Score an assessment using LLM with rubric constraints.
        
        Args:
            assessment_id: UUID of assessment
            transcript_segments: Full transcript with timings
            feature_signals: Extracted feature signals
            evidence_candidates: Pre-generated evidence candidates
            benchmark_definition: Benchmark rubric definition
            prompt: Original assessment prompt
            is_eal: Whether student has EAL status
            
        Returns:
            ScoringResult with all strand scores and feedback
        """
        # Build the structured prompt
        system_prompt = self._build_system_prompt(benchmark_definition)
        user_prompt = self._build_user_prompt(
            transcript_segments,
            feature_signals,
            evidence_candidates,
            prompt,
            benchmark_definition,
            is_eal
        )
        
        # Call LLM with structured output
        try:
            result = await self._call_llm_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=self._get_response_schema()
            )
            
            # Parse and validate result
            scoring_result = self._parse_result(
                result,
                evidence_candidates,
                benchmark_definition
            )
            
            logger.info(f"Scoring complete for assessment {assessment_id}")
            return scoring_result
            
        except Exception as e:
            logger.error(f"LLM scoring failed: {e}")
            raise ScoringError(f"Failed to score assessment: {e}")
    
    def _build_system_prompt(self, benchmark: Dict) -> str:
        """Build the system prompt with rubric constraints."""
        strands = benchmark.get("strands", {})
        
        prompt = """You are an expert oracy assessment evaluator. Your task is to evaluate a student's spoken performance against a detailed rubric.

## CRITICAL RULES:
1. You MUST ONLY use evidence clips from the provided candidate list - DO NOT invent timestamps
2. You MUST reference specific rubric descriptors in your justifications
3. You MUST provide confidence scores (0.0-1.0) for each strand
4. If evidence is insufficient, state this clearly and reduce confidence
5. Feedback MUST be mode-specific (presenting/explaining/persuading) and NOT generic speaking tips
6. All scores must map to: emerging, expected, or exceeding

## STRAND DEFINITIONS:
"""
        
        for strand_name, strand_def in strands.items():
            prompt += f"\n### {strand_name.upper()}:\n"
            prompt += f"{strand_def.get('description', '')}\n"
            
            for band in ["emerging", "expected", "exceeding"]:
                band_desc = strand_def.get("bands", {}).get(band, {}).get("descriptor", "")
                prompt += f"\n{band.upper()}: {band_desc}\n"
        
        prompt += """
## OUTPUT FORMAT:
You must output valid JSON matching the provided schema exactly.
"""
        
        return prompt
    
    def _build_user_prompt(
        self,
        transcript_segments: List[Dict],
        feature_signals: Dict,
        evidence_candidates: List,
        prompt: str,
        benchmark: Dict,
        is_eal: bool
    ) -> str:
        """Build the user prompt with assessment data."""
        # Build transcript text
        full_transcript = " ".join(
            seg.get("text", "") for seg in transcript_segments
        )
        
        user_prompt = f"""## ASSESSMENT CONTEXT:
Mode: {benchmark.get('mode', 'presenting')}
Prompt: {prompt}
Age Band: {benchmark.get('age_band', 'unknown')}
EAL Student: {"Yes" if is_eal else "No"}

## EXTRACTED FEATURES:
"""
        
        # Add relevant features
        physical_features = {
            k: v for k, v in feature_signals.items()
            if k in ['wpm', 'pause_ratio', 'filler_frequency', 'volume_variance', 'rhythm_stability']
            and v is not None
        }
        linguistic_features = {
            k: v for k, v in feature_signals.items()
            if k in ['sentence_length_mean', 'vocabulary_diversity', 'clarity_score']
            and v is not None
        }
        cognitive_features = {
            k: v for k, v in feature_signals.items()
            if k in ['reason_density', 'structure_completeness', 'coherence_score']
            and v is not None
        }
        social_features = {
            k: v for k, v in feature_signals.items()
            if k in ['audience_reference_frequency', 'confidence_score']
            and v is not None
        }
        
        user_prompt += f"""
Physical: {json.dumps(physical_features, indent=2)}
Linguistic: {json.dumps(linguistic_features, indent=2)}
Cognitive: {json.dumps(cognitive_features, indent=2)}
Social-Emotional: {json.dumps(social_features, indent=2)}
Quality Flag: {feature_signals.get('quality_flag', 'unknown')}

## AVAILABLE EVIDENCE CLIPS (SELECT ONLY FROM THESE):
"""
        
        # Add evidence candidates
        for i, candidate in enumerate(evidence_candidates):
            user_prompt += f"""
clip_{i}:
  Time: {candidate.start_time:.1f}s - {candidate.end_time:.1f}s
  Type: {candidate.type}
  Text: "{candidate.transcript_text[:200]}..."
  Relevant Strands: {', '.join(candidate.relevant_strands)}
"""
        
        user_prompt += f"""
## FULL TRANSCRIPT:
{full_transcript}

## TASK:
1. Evaluate each of the 4 strands (physical, linguistic, cognitive, social_emotional)
2. Assign a band (emerging/expected/exceeding) with confidence score
3. Select 3-8 evidence clips from the list above that justify each score
4. Write justifications referencing rubric descriptors
5. Provide 3 specific strengths tied to the mode
6. Provide 3 specific next steps for improvement
7. Suggest 1-2 student-friendly practice goals
{"8. For EAL student: separate reasoning from language surface scores" if is_eal else ""}

Respond with valid JSON only.
"""
        
        return user_prompt
    
    def _get_response_schema(self) -> Dict:
        """Get the JSON schema for structured LLM output."""
        return {
            "type": "object",
            "properties": {
                "physical_score": {
                    "type": "object",
                    "properties": {
                        "band": {"type": "string", "enum": ["emerging", "expected", "exceeding"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "evidence_clips": {"type": "array", "items": {"type": "string"}},
                        "justification": {"type": "string"},
                        "subskills": {"type": "object"}
                    },
                    "required": ["band", "confidence", "evidence_clips", "justification"]
                },
                "linguistic_score": {
                    "type": "object",
                    "properties": {
                        "band": {"type": "string", "enum": ["emerging", "expected", "exceeding"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "evidence_clips": {"type": "array", "items": {"type": "string"}},
                        "justification": {"type": "string"},
                        "subskills": {"type": "object"}
                    },
                    "required": ["band", "confidence", "evidence_clips", "justification"]
                },
                "cognitive_score": {
                    "type": "object",
                    "properties": {
                        "band": {"type": "string", "enum": ["emerging", "expected", "exceeding"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "evidence_clips": {"type": "array", "items": {"type": "string"}},
                        "justification": {"type": "string"},
                        "subskills": {"type": "object"}
                    },
                    "required": ["band", "confidence", "evidence_clips", "justification"]
                },
                "social_emotional_score": {
                    "type": "object",
                    "properties": {
                        "band": {"type": "string", "enum": ["emerging", "expected", "exceeding"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "evidence_clips": {"type": "array", "items": {"type": "string"}},
                        "justification": {"type": "string"},
                        "subskills": {"type": "object"}
                    },
                    "required": ["band", "confidence", "evidence_clips", "justification"]
                },
                "feedback": {
                    "type": "object",
                    "properties": {
                        "strengths": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "strand": {"type": "string"},
                                    "evidence": {"type": "string"}
                                }
                            }
                        },
                        "next_steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "strand": {"type": "string"},
                                    "specific": {"type": "boolean"}
                                }
                            }
                        },
                        "goals": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["strengths", "next_steps", "goals"]
                },
                "overall_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "warnings": {"type": "array", "items": {"type": "string"}},
                "eal_scaffolds": {"type": "object"}
            },
            "required": [
                "physical_score", "linguistic_score", "cognitive_score",
                "social_emotional_score", "feedback", "overall_confidence", "warnings"
            ]
        }
    
    async def _call_llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Dict
    ) -> Dict:
        """Call LLM with structured output using LiteLLM."""
        try:
            from litellm import acompletion
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await acompletion(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            
            # Try fallback models
            for fallback_model in self.fallback_models:
                try:
                    logger.info(f"Trying fallback model: {fallback_model}")
                    response = await acompletion(
                        model=fallback_model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.3,
                        max_tokens=4000
                    )
                    content = response.choices[0].message.content
                    return json.loads(content)
                except Exception as fallback_error:
                    logger.error(f"Fallback model {fallback_model} failed: {fallback_error}")
                    continue
            
            raise ScoringError(f"All LLM models failed: {e}")
    
    def _parse_result(
        self,
        result: Dict,
        evidence_candidates: List,
        benchmark: Dict
    ) -> ScoringResult:
        """Parse and validate LLM result."""
        
        # Get valid clip IDs
        valid_clips = {f"clip_{i}" for i in range(len(evidence_candidates))}
        
        # Parse strand scores
        strands = {}
        warnings = result.get("warnings", [])
        
        for strand_name in ["physical", "linguistic", "cognitive", "social_emotional"]:
            score_data = result.get(f"{strand_name}_score", {})
            
            # Validate evidence clips
            clips = score_data.get("evidence_clips", [])
            invalid_clips = [c for c in clips if c not in valid_clips]
            
            if invalid_clips:
                warnings.append(f"Invalid evidence clips removed for {strand_name}: {invalid_clips}")
                clips = [c for c in clips if c in valid_clips]
            
            # Ensure at least 3 clips, max 8
            if len(clips) < 3:
                warnings.append(f"Insufficient evidence for {strand_name}: only {len(clips)} clips")
            if len(clips) > 8:
                clips = clips[:8]
                warnings.append(f"Too much evidence for {strand_name}: limited to 8 clips")
            
            strands[strand_name] = StrandScore(
                band=score_data.get("band", "emerging"),
                confidence=score_data.get("confidence", 0.5),
                evidence_clips=clips,
                justification=score_data.get("justification", ""),
                subskills=score_data.get("subskills")
            )
        
        # Parse feedback
        feedback_data = result.get("feedback", {})
        feedback = Feedback(
            strengths=feedback_data.get("strengths", [])[:3],  # Max 3
            next_steps=feedback_data.get("next_steps", [])[:3],  # Max 3
            goals=feedback_data.get("goals", [])[:2]  # Max 2
        )
        
        return ScoringResult(
            physical=strands["physical"],
            linguistic=strands["linguistic"],
            cognitive=strands["cognitive"],
            social_emotional=strands["social_emotional"],
            feedback=feedback,
            overall_confidence=result.get("overall_confidence", 0.5),
            warnings=warnings,
            eal_scaffolds=result.get("eal_scaffolds")
        )
    
    def save_report(
        self,
        assessment_id: str,
        result: ScoringResult,
        benchmark_version: str,
        ai_model: str
    ):
        """Save scoring result as a draft report."""
        from apps.reports.models import DraftReport
        from apps.assessments.models import Assessment
        
        assessment = Assessment.objects.get(id=assessment_id)
        
        def strand_to_dict(score: StrandScore) -> Dict:
            return {
                "band": score.band,
                "confidence": score.confidence,
                "evidence_clips": score.evidence_clips,
                "justification": score.justification,
                "subskills": score.subskills or {}
            }
        
        report = DraftReport.objects.create(
            assessment=assessment,
            physical_score=strand_to_dict(result.physical),
            linguistic_score=strand_to_dict(result.linguistic),
            cognitive_score=strand_to_dict(result.cognitive),
            social_emotional_score=strand_to_dict(result.social_emotional),
            feedback={
                "strengths": result.feedback.strengths,
                "next_steps": result.feedback.next_steps,
                "goals": result.feedback.goals
            },
            overall_confidence=result.overall_confidence,
            warnings=result.warnings,
            eal_scaffolds=result.eal_scaffolds or {},
            ai_model=ai_model,
            ai_provider=self.model.split("/")[0] if "/" in self.model else "unknown",
            ai_version="latest",
            benchmark_version=benchmark_version
        )
        
        logger.info(f"Draft report created for assessment {assessment_id}")
        return report


class ScoringError(Exception):
    """Exception for scoring errors."""
    pass