# ADR-016: Voice AI A/B Experimentation & Multi-Variant Evaluation

## Status
Accepted (v0.16.0)

## Context
Optimizing Voice AI pipelines requires comparing different cloud LLMs (e.g. Gemini 1.5 Flash vs OpenAI GPT-4o-mini), TTS engines (Deepgram Aura vs ElevenLabs Multilingual), and streaming chunking algorithms on live turn latency and evaluation quality. Without automated variant allocation and metric aggregation, engineering teams cannot make data-backed decisions.

## Decision
1. **Experiment Models & Configuration**:
   - `ExperimentConfig`: Defines active experiments with weighted `ExperimentVariant` splits.
   - Pre-seeded experiments:
     - `exp_llm_model`: Gemini 1.5 Flash vs OpenAI GPT-4o-mini
     - `exp_tts_engine`: Deepgram Aura vs ElevenLabs
2. **Deterministic Hash Allocation**:
   - `ABExperimentManager` uses deterministic MD5 hashing (`session_id:exp_id`) to ensure consistent variant assignment throughout an interview session.
3. **Metrics Tracking & APIs**:
   - Tracks sample count, average turn latency, average TTFT, and average scorecard score per variant.
   - `GET /api/experiments/active`, `POST /api/experiments/configure`, `GET /api/experiments/{exp_id}/results`.

## Consequences
### Positive
- Enables scientific evaluation of Voice AI provider trade-offs.
- Allows seamless online experimentation without code redeployments.

### Tradeoffs
- A/B experiments must be monitored to ensure treatment variants do not degrade live interview quality.
