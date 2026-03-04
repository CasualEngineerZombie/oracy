# AI/ML Pipeline V2 (Cost-Optimized)

## Overview

This document describes the cost-optimized AI/ML pipeline for Oracy AI, replacing paid cloud services (AWS Transcribe, OpenAI Whisper API) with open source self-hosted alternatives. This V2 design prioritizes cost efficiency while maintaining quality and accuracy.

### Cost Comparison

| Service | V1 (Cloud) | V2 (Self-Hosted) | Savings |
|---------|------------|------------------|---------|
| Speech-to-Text | OpenAI Whisper API ($0.006/min) + AWS Transcribe ($0.024/min) | Self-hosted Whisper (faster-whisper) | ~95% |
| GPU Infrastructure | N/A (pay-per-use) | RunPod/Vast.ai GPU instances | ~80% |
| Estimated Monthly Cost (1,000 assessments) | ~$1,500 | ~$300 | ~80% |

---

## Step 1: Speech-to-Text (STT) - Self-Hosted

### Recommended Approach: WhisperX with distil-large-v3

For the MVP, we will use **WhisperX** with the **distil-large-v3** model. WhisperX provides:
- **Word-level timestamps** with forced alignment (more accurate than Whisper alone)
- **Batch processing** for faster throughput
- **Speaker diarization** (future feature)
- **distil-large-v3**: 6x faster than large-v3 with <1% WER degradation
- Lower VRAM usage with `int8` quantization (~5.5GB vs ~10GB)

### Why WhisperX + distil-large-v3?

| Feature | Whisper (OpenAI) | faster-whisper | WhisperX |
|---------|------------------|----------------|----------|
| Word timestamps | Segment only | Word-level | **Character-level alignment** |
| Batch processing | No | Limited | **Yes (batch_size=4-16)** |
| Speaker diarization | No | No | **Yes (future)** |
| Speed (large model) | 1x | 4x | **6x (distil-large-v3)** |
| VRAM (large model) | ~10GB | ~6GB | **~5.5GB (int8)** |

### Implementation

#### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STT Service (Self-Hosted WhisperX)                                     │
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐    │
│  │  API Layer   │────▶│  Job Queue   │────▶│   GPU Worker Pool    │    │
│  │  (FastAPI)   │     │   (Redis)    │     │  (WhisperX +         │    │
│  └──────────────┘     └──────────────┘     │   distil-large-v3)   │    │
│         │                                  │   - int8 quantized   │    │
│         ▼                                  │   - batch_size=4     │    │
│  ┌──────────────┐                           └──────────────────────┘    │
│  │   Results    │◀──────────────────────────│   Transcript Store   │    │
│  │   Endpoint   │                           │    (PostgreSQL)      │    │
│  └──────────────┘                           └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Option A: RunPod Serverless GPU (Recommended for MVP)

Use RunPod's serverless GPU workers with WhisperX to transcribe audio without managing infrastructure:

```python
# stt/runpod_service.py
import runpod
import aiohttp
from typing import Optional
import json

class RunPodWhisperXService:
    """
    Self-hosted WhisperX using RunPod serverless GPU.
    Uses distil-large-v3 model with int8 quantization for optimal speed/accuracy.
    Pay only for compute time used during transcription.
    """
    
    def __init__(self, api_key: str, endpoint_id: str):
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.base_url = f"https://api.runpod.ai/v2/{endpoint_id}"
    
    async def transcribe(
        self, 
        audio_url: str,
        model: str = "distil-large-v3",
        language: Optional[str] = "en",
        batch_size: int = 4
    ) -> dict:
        """
        Submit transcription job to RunPod serverless endpoint.
        
        Uses WhisperX with:
        - distil-large-v3 model (6x faster than large-v3, <1% WER loss)
        - int8 quantization (40% VRAM reduction)
        - batch processing (4-16 files simultaneously)
        - forced alignment for precise word timestamps
        
        Cost: ~$0.0003-0.0005 per minute
        vs OpenAI API: $0.006 per minute = ~95% savings
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "audio": audio_url,
                "model": model,  # distil-large-v3 (recommended), large-v2, large-v3
                "language": language,
                "batch_size": batch_size,  # 4 for 8GB VRAM, 16 for 16GB+
                "compute_type": "int8",  # Reduces VRAM by 40%
                "align_words": True  # WhisperX forced alignment for precise timestamps
            }
        }
        
        async with aiohttp.ClientSession() as session:
            # Submit job
            async with session.post(
                f"{self.base_url}/run",
                headers=headers,
                json=payload
            ) as resp:
                result = await resp.json()
                job_id = result["id"]
            
            # Poll for completion
            while True:
                async with session.get(
                    f"{self.base_url}/status/{job_id}",
                    headers=headers
                ) as resp:
                    status = await resp.json()
                    
                    if status["status"] == "COMPLETED":
                        return self._parse_result(status["output"])
                    elif status["status"] == "FAILED":
                        raise TranscriptionError(status.get("error", "Unknown error"))
                    
                    await asyncio.sleep(1)
    
    def _parse_result(self, output: dict) -> Transcript:
        """Convert WhisperX output to internal Transcript format."""
        segments = []
        for seg in output["segments"]:
            words = []
            for word in seg.get("words", []):
                words.append(Word(
                    word=word["word"],
                    start=word["start"],
                    end=word["end"],
                    confidence=word.get("score", 0.95)  # WhisperX uses 'score'
                ))
            
            segments.append(Segment(
                id=seg.get("id", 0),
                start=seg["start"],
                end=seg["end"],
                text=seg["text"],
                words=words
            ))
        
        return Transcript(
            segments=segments,
            language=output.get("language", "en"),
            duration_seconds=output["segments"][-1]["end"] if segments else 0,
            confidence_overall=output.get("avg_logprob", 0.0)
        )

# Pydantic models
from pydantic import BaseModel
from typing import List, Optional

class Word(BaseModel):
    word: str
    start: float
    end: float
    confidence: float

class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: List[Word]

class Transcript(BaseModel):
    segments: List[Segment]
    language: str
    duration_seconds: float
    confidence_overall: float
    
    def all_words(self) -> List[Word]:
        return [w for seg in self.segments for w in seg.words]
```

**RunPod Worker Handler** (Docker image deployed to RunPod):

```python
# stt/runpod_worker.py
import runpod
import whisperx
import tempfile
import requests
import os
import torch

# Load model once at startup (kept in memory)
model = None
device = "cuda" if torch.cuda.is_available() else "cpu"

def load_model(model_name: str = "distil-large-v3", compute_type: str = "int8"):
    """Load WhisperX model with specified compute type."""
    global model
    if model is None:
        model = whisperx.load_model(
            model_name,
            device=device,
            compute_type=compute_type,  # int8 for 40% VRAM reduction
            language="en"  # Skip language detection for faster loading
        )
    return model

def handler(event):
    """RunPod serverless handler for WhisperX."""
    job_input = event["input"]
    
    audio_url = job_input["audio"]
    model_name = job_input.get("model", "distil-large-v3")
    language = job_input.get("language", "en")
    batch_size = job_input.get("batch_size", 4)
    compute_type = job_input.get("compute_type", "int8")
    align_words = job_input.get("align_words", True)
    
    # Download audio file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        response = requests.get(audio_url)
        tmp.write(response.content)
        audio_path = tmp.name
    
    try:
        # Load audio
        audio = whisperx.load_audio(audio_path)
        
        # Load model (uses cached if already loaded)
        whisper_model = load_model(model_name, compute_type)
        
        # 1. Transcribe with Whisper
        result = whisper_model.transcribe(audio, batch_size=batch_size)
        
        # 2. Align words for precise timestamps (WhisperX feature)
        if align_words:
            model_a, metadata = whisperx.load_align_model(
                language_code=language, 
                device=device
            )
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                device,
                return_char_alignments=False
            )
        
        # Format output
        result_segments = []
        for i, segment in enumerate(result["segments"]):
            words = []
            if "words" in segment:
                for word in segment["words"]:
                    words.append({
                        "word": word["word"],
                        "start": word["start"],
                        "end": word["end"],
                        "score": word.get("score", 0.95)  # WhisperX alignment score
                    })
            
            result_segments.append({
                "id": i,
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"],
                "words": words
            })
        
        return {
            "segments": result_segments,
            "language": language,
            "model": model_name,
            "compute_type": compute_type
        }
    
    finally:
        os.unlink(audio_path)
        # Clean up GPU memory
        torch.cuda.empty_cache()

# Start serverless handler
runpod.serverless.start({"handler": handler})
```

**Key WhisperX Features Used:**
- **distil-large-v3**: 6x faster than large-v3, <1% accuracy loss
- **int8 quantization**: Reduces VRAM from ~10GB to ~5.5GB
- **Batch processing**: Process 4-16 audio files simultaneously
- **Forced alignment**: Character-level accurate word timestamps
- **Language-specific alignment models**: Better accuracy per language

**Pros:**
- 4-5x cheaper than OpenAI Whisper API
- No infrastructure to manage (serverless)
- GPU available on-demand
- Same accuracy as OpenAI API
- Word-level timestamps included

**Cons:**
- Cold start latency (~2-5 seconds for first request)
- External dependency (RunPod)
- Requires Docker deployment

#### Option B: Local GPU with Vast.ai (Scale Option)

For higher volumes, rent GPU instances from Vast.ai (cheaper than AWS):

```python
# stt/vast_ai_service.py
import requests
from typing import Optional

class VastAIWhisperService:
    """
    Self-hosted Whisper on Vast.ai GPU instances.
    Best for high-volume processing with predictable costs.
    """
    
    def __init__(self, api_key: str, instance_id: str):
        self.api_key = api_key
        self.instance_id = instance_id
        self.base_url = f"https://{instance_id}.cloud.vast.ai"
    
    async def transcribe(
        self,
        audio_path: str,
        model_size: str = "base"
    ) -> Transcript:
        """
        Transcribe using dedicated Vast.ai instance.
        
        Cost: ~$0.20-0.50/hour for RTX 3090/4090
        Can process ~100-200 assessments per hour
        = ~$0.001-0.005 per assessment
        """
        with open(audio_path, 'rb') as f:
            files = {'audio': f}
            data = {'model': model_size}
            
            response = requests.post(
                f"{self.base_url}/transcribe",
                files=files,
                data=data
            )
            response.raise_for_status()
            
            return self._parse_result(response.json())
```

**Vast.ai Instance Setup** (Docker Compose):

```yaml
# docker-compose.whisper-gpu.yml
version: '3.8'

services:
  whisper-api:
    image: oracy/whisper-gpu:latest
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - MODEL_SIZE=base  # tiny, base, small, medium, large-v3
      - WORKERS=2
    ports:
      - "8000:8000"
    volumes:
      - model-cache:/root/.cache/whisper
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  model-cache:
```

**Cost Estimate:**
- RTX 3090 on Vast.ai: ~$0.30/hour
- Can process ~150 assessments/hour (avg 2 min each)
- Cost per assessment: ~$0.002
- vs OpenAI API: $0.012 per 2-minute assessment
- **Savings: ~83%**

#### Option C: CPU-Only Fallback (Lowest Cost)

For development or low-volume periods, use WhisperX on CPU:

```python
# stt/cpu_whisperx_service.py
import whisperx
import torch

class CPUWhisperXService:
    """
    CPU-only WhisperX for development/testing.
    Slower but zero additional cost.
    """
    
    def __init__(self, model_name: str = "base"):
        # tiny or base model recommended for CPU
        self.device = "cpu"
        self.model = whisperx.load_model(
            model_name,
            device=self.device,
            compute_type="int8",  # Required for CPU
            language="en"
        )
    
    def transcribe(self, audio_path: str) -> Transcript:
        """
        CPU transcription - slower but free.
        
        base model: ~5-10x realtime (1 min audio takes 30-60s)
        tiny model: ~2-3x realtime (1 min audio takes 20-30s)
        
        Note: Word alignment is slower on CPU, may be skipped for speed.
        """
        # Load audio
        audio = whisperx.load_audio(audio_path)
        
        # Transcribe (no batch processing on CPU)
        result = self.model.transcribe(audio, batch_size=1)
        
        # Optional: Skip alignment on CPU for speed
        # On GPU we do alignment, on CPU we use Whisper timestamps
        
        # ... parse results
```

**When to use:**
- Development environment
- Testing/CI pipelines
- Backup when GPU unavailable
- Low-volume periods

**Note:** CPU mode is significantly slower. For a 2-minute assessment:
- GPU (distil-large-v3): ~20 seconds
- CPU (base model): ~2-3 minutes

### WhisperX Model Selection Guide

| Model | Size | VRAM (fp16) | VRAM (int8) | Speed | WER | Best For |
|-------|------|-------------|-------------|-------|-----|----------|
| tiny | 39 MB | ~1 GB | ~0.5 GB | ~32x RT | 60.5 | Testing only |
| base | 74 MB | ~1 GB | ~0.5 GB | ~16x RT | 47.6 | Development |
| small | 244 MB | ~2 GB | ~1 GB | ~6x RT | 33.4 | Low-resource |
| medium | 769 MB | ~5 GB | ~2.5 GB | ~2x RT | 21.9 | Balanced |
| large-v2 | 1550 MB | ~10 GB | ~5.5 GB | ~1x RT | 16.7 | High accuracy |
| **distil-large-v3** | **756 MB** | **~5 GB** | **~2.8 GB** | **~6x RT** | **17.2** | **MVP Recommended** |

**RT = Realtime** (e.g., 6x RT = 1 min audio processed in ~10 seconds)

**Why distil-large-v3?**
- Same speed as "small" model but accuracy close to "large-v2"
- Optimized for English (97% of our use case)
- Works with int8 quantization (only ~2.8GB VRAM)
- Can batch 4-8 files on a single 8GB GPU

**MVP Recommendation:** Use `distil-large-v3` with `int8` quantization on RunPod RTX 3090.

### Service Interface

```python
from abc import ABC, abstractmethod
from typing import Protocol, Optional

class STTService(Protocol):
    @abstractmethod
    async def transcribe(
        self, 
        audio_path: str,
        model: str = "distil-large-v3",
        language: Optional[str] = "en",
        batch_size: int = 4
    ) -> Transcript:
        """Generate timestamped transcript using WhisperX."""
        ...
    
    @abstractmethod
    def supports_batching(self) -> bool:
        """Whether batch processing is supported (WhisperX feature)."""
        ...

# Usage - easy to swap implementations
stt_service: STTService = RunPodWhisperXService(api_key, endpoint_id)
# or: stt_service = VastAIWhisperXService(api_key, instance_id)
# or: stt_service = CPUWhisperXService(model_name="base")

transcript = await stt_service.transcribe(
    audio_path,
    model="distil-large-v3",
    batch_size=4
)
```

---

## Step 2: Deterministic Feature Extraction

This step remains **unchanged** from V1. The feature extraction is already using open source libraries (librosa, spaCy, VADER) and does not require modifications.

### Key Libraries (All Open Source)

| Feature | Library | License |
|---------|---------|---------|
| Audio processing | librosa | ISC |
| Voice Activity Detection | webrtcvad | BSD-3 |
| NLP | spaCy | MIT |
| Sentiment Analysis | VADER | MIT |
| Text statistics | textstat | MIT |

**No changes required** - this is already cost-optimized.

---

## Step 3: Benchmarking Layer (Core IP)

No changes required - the BDL (Benchmark Definition Language) is internal IP and does not rely on external services.

---

## Step 4: Evidence Candidate Generation

No changes required - deterministic algorithm, no external dependencies.

---

## Step 5: LLM Scoring Service

### Cost-Optimized Approach: OpenRouter + Local Fallback

Instead of direct OpenAI API, use OpenRouter for competitive pricing with fallback to local models.

```python
# llm/openrouter_service.py
import os
from typing import Optional, Dict, Any
import aiohttp

class OpenRouterService:
    """
    LLM scoring via OpenRouter - aggregates multiple providers for best pricing.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
    
    async def score_assessment(
        self,
        transcript: str,
        features: Dict[str, float],
        rubric: Dict[str, Any],
        model: str = "anthropic/claude-3.5-haiku"  # Cheaper than GPT-4o
    ) -> Dict[str, Any]:
        """
        Score assessment using OpenRouter.
        
        Cost comparison (per 1K input tokens):
        - OpenAI GPT-4o: $0.005
        - Anthropic Claude 3.5 Haiku: $0.0008 (via OpenRouter)
        - Google Gemini Flash: $0.00035 (via OpenRouter)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://oracy.ai",
            "X-Title": "Oracy AI"
        }
        
        prompt = self._build_scoring_prompt(transcript, features, rubric)
        
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3
                }
            )
            result = await response.json()
            return self._parse_scoring_result(result)
```

**Cost-Effective Model Selection:**

| Model | Input Cost | Output Cost | Best For |
|-------|------------|-------------|----------|
| google/gemini-flash-1.5 | $0.00035/1K | $0.00105/1K | Initial scoring (cheapest) |
| anthropic/claude-3.5-haiku | $0.0008/1K | $0.004/1K | Balanced quality/cost |
| openai/gpt-4o-mini | $0.00015/1K | $0.0006/1K | Alternative cheap option |
| anthropic/claude-3.5-sonnet | $0.003/1K | $0.015/1K | Final review (if needed) |

### Optional: Local LLM Fallback (Ollama)

For zero API cost, run local models with Ollama:

```python
# llm/ollama_service.py
import aiohttp

class OllamaService:
    """
    Local LLM scoring using Ollama - zero API costs.
    Suitable for development and low-volume production.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    async def score_assessment(
        self,
        transcript: str,
        features: Dict[str, float],
        rubric: Dict[str, Any],
        model: str = "llama3.2:3b"  # Small but capable
    ) -> Dict[str, Any]:
        """
        Score using local Ollama instance.
        
        Recommended models:
        - llama3.2:3b (3B params, fast, decent quality)
        - qwen2.5:7b (better quality, slightly slower)
        - phi4:14b (best quality, requires more VRAM)
        """
        prompt = self._build_scoring_prompt(transcript, features, rubric)
        
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "system": self.SYSTEM_PROMPT,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_ctx": 8192
                    }
                }
            )
            result = await response.json()
            return json.loads(result["response"])
```

**Ollama Setup:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull llama3.2:3b
ollama pull qwen2.5:7b

# Start server
ollama serve
```

**When to use local LLMs:**
- Development/testing
- Low-volume periods
- Privacy-sensitive deployments
- Cost-zero requirement

---

## Infrastructure Changes Summary

### Removed Services
- ~~AWS Transcribe~~ → Self-hosted Whisper (faster-whisper)
- ~~OpenAI Whisper API~~ → RunPod/Vast.ai self-hosted

### Added Services
- RunPod serverless GPU endpoints
- Vast.ai GPU instances (optional)
- Ollama local LLM server (optional)

### Cost Impact

| Component | V1 Monthly | V2 Monthly | Savings |
|-----------|------------|------------|---------|
| STT (1,000 assessments) | $600 | $50 | 92% |
| LLM Scoring | $400 | $100 | 75% |
| GPU Infrastructure | $0 | $150 | - |
| **Total** | **$1,000** | **$300** | **70%** |

---

## Migration Guide

### Phase 1: RunPod Setup (Week 1)

1. Create RunPod account
2. Build and deploy Whisper worker
3. Update environment variables
4. Test transcription pipeline

### Phase 2: OpenRouter Migration (Week 1-2)

1. Create OpenRouter account
2. Update LLM service to use OpenRouter
3. Test scoring pipeline
4. Compare quality with V1

### Phase 3: Optimization (Ongoing)

1. Monitor costs and accuracy
2. Adjust model sizes based on quality requirements
3. Consider Vast.ai for high-volume periods
4. Implement local LLM fallback

---

## Quality Assurance

### Accuracy Validation

Run parallel scoring to validate V2 against V1:

```python
async def validate_stt_accuracy(sample_audio_paths: List[str]):
    """
    Compare V1 (OpenAI) vs V2 (Self-hosted) transcription accuracy.
    """
    v1_service = WhisperAPIService()
    v2_service = RunPodWhisperService()
    
    results = []
    for path in sample_audio_paths:
        v1_transcript = await v1_service.transcribe(path)
        v2_transcript = await v2_service.transcribe(path)
        
        # Calculate WER (Word Error Rate)
        wer = calculate_wer(v1_transcript.full_text, v2_transcript.full_text)
        results.append(wer)
    
    avg_wer = sum(results) / len(results)
    assert avg_wer < 0.05, f"WER too high: {avg_wer}"
```

### Target Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| STT WER vs OpenAI | < 5% | Word Error Rate |
| LLM Score Correlation | > 0.95 | Pearson correlation |
| End-to-end Latency | < 3 min | 95th percentile |
| Cost per Assessment | < $0.50 | Full pipeline |

---

## Appendix: Docker Images

### WhisperX GPU Worker (RunPod)

```dockerfile
# Dockerfile.whisperx-gpu
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Pre-download models (optional, speeds up cold start)
RUN python3 -c "import whisperx; whisperx.load_model('distil-large-v3', device='cpu', compute_type='int8')"

COPY stt/runpod_worker.py .

# Use flashboot for faster cold starts
ENV RUNPOD_FLASHBOOT_ACTIVE="true"

CMD ["python3", "-m", "runpod.serverless.start", "--handler", "runpod_worker.handler"]
```

**requirements.txt:**
```
whisperx>=3.1.1
torch>=2.0.0
torchaudio>=2.0.0
runpod>=1.6.0
requests>=2.31.0
numpy>=1.24.0
```

**Key Optimizations:**
- Pre-download `distil-large-v3` model during build (faster cold start)
- Use `int8` quantization (40% VRAM reduction)
- Enable RunPod flashboot (reduces cold start from 10s to 2s)
- Cache alignment models for repeated use

### Ollama Server

```dockerfile
# Dockerfile.ollama
FROM ollama/ollama:latest

# Pre-download models
RUN ollama serve & \
    sleep 5 && \
    ollama pull llama3.2:3b && \
    ollama pull qwen2.5:7b && \
    pkill ollama

EXPOSE 11434

ENTRYPOINT ["ollama", "serve"]
```
