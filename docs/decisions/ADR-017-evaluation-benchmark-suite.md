# ADR-017: Golden Standard Evaluation Benchmark Suite & Scoring Calibration

## Status
Accepted (v0.17.0)

## Context
AI-powered interview evaluation models require continuous calibration against human hiring rubrics to avoid score drift, hallucinations, and false-positive red flags. VoiceHire requires a self-contained Evaluation Suite and automated benchmark runner to evaluate scoring consistency (Mean Absolute Error) and red flag precision/recall on standardized golden interview datasets.

## Decision
1. **Golden Dataset Architecture**:
   - `GoldenInterviewSample`: Standardized interview answers across seniority levels (SDE-1, SDE-2, Senior, Staff) with ground-truth expected scores and known red flag labels.
2. **Benchmark Runner & Metrics**:
   - `BenchmarkRunner.run_evaluation_suite()` executes automated grading on all golden transcripts.
   - Computes:
     - **Mean Absolute Error (MAE)**: Average point deviation between predicted score and human baseline.
     - **Calibration Accuracy**: Percentage of samples scored within ±0.8 of the golden standard.
     - **Red Flag Precision & Recall**: Accuracy of critical misconception detection.
3. **REST APIs & UI Suite**:
   - `POST /api/evaluation/run-benchmark`
   - `GET /api/evaluation/benchmark-results`
   - Benchmark evaluation modal tab in frontend.

## Consequences
### Positive
- Prevents regression in evaluation quality as underlying LLMs and prompts evolve.
- Provides quantitative confidence to hiring teams on evaluation reliability.

### Tradeoffs
- Golden dataset must be curated and expanded continuously as new domains are added.
