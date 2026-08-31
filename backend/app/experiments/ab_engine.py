import hashlib
from typing import Dict, Any, List, Optional
from app.models.experiments import (
    ExperimentConfig, ExperimentVariant, ExperimentResult, VariantPerformance
)
from app.core.logger import get_logger

logger = get_logger("experiments.ab_engine")

PRESEEDED_EXPERIMENTS: List[ExperimentConfig] = [
    ExperimentConfig(
        experiment_id="exp_llm_model",
        title="LLM Speed vs Reasoning Benchmark",
        description="Compares Gemini 1.5 Flash against OpenAI GPT-4o-mini on TTFT and scoring depth.",
        is_active=True,
        variants=[
            ExperimentVariant(
                variant_id="control_gemini",
                name="Control (Gemini 1.5 Flash)",
                description="Ultra low-latency streaming inference",
                config_overrides={"llm_provider": "gemini"},
                weight=0.5
            ),
            ExperimentVariant(
                variant_id="treatment_openai",
                name="Treatment (OpenAI GPT-4o-mini)",
                description="Structured JSON reasoning accuracy",
                config_overrides={"llm_provider": "openai"},
                weight=0.5
            )
        ]
    ),
    ExperimentConfig(
        experiment_id="exp_tts_engine",
        title="TTS Voice Engine Comparison",
        description="Compares Deepgram Aura against ElevenLabs Multilingual on TTFA.",
        is_active=True,
        variants=[
            ExperimentVariant(
                variant_id="control_deepgram",
                name="Control (Deepgram Aura)",
                description="Sub-150ms TTFA voice stream",
                config_overrides={"tts_provider": "deepgram"},
                weight=0.5
            ),
            ExperimentVariant(
                variant_id="treatment_elevenlabs",
                name="Treatment (ElevenLabs)",
                description="High-fidelity conversational prosody",
                config_overrides={"tts_provider": "elevenlabs"},
                weight=0.5
            )
        ]
    )
]

class ABExperimentManager:
    """
    Manages active A/B experiments, deterministic variant allocations,
    and quality / latency metric aggregations per variant.
    """
    _experiments: Dict[str, ExperimentConfig] = {}
    _records: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def initialize_defaults(cls):
        for exp in PRESEEDED_EXPERIMENTS:
            cls._experiments[exp.experiment_id] = exp
            if exp.experiment_id not in cls._records:
                cls._records[exp.experiment_id] = []

    @classmethod
    def get_active_experiments(cls) -> List[ExperimentConfig]:
        if not cls._experiments:
            cls.initialize_defaults()
        return [exp for exp in cls._experiments.values() if exp.is_active]

    @classmethod
    def assign_variants(cls, session_id: str) -> Dict[str, str]:
        """
        Deterministically allocates an experiment variant for a given session ID.
        """
        if not cls._experiments:
            cls.initialize_defaults()

        assignments: Dict[str, str] = {}
        for exp_id, exp in cls._experiments.items():
            if not exp.is_active or not exp.variants:
                continue

            # Deterministic hash allocation
            hash_val = int(hashlib.md5(f"{session_id}:{exp_id}".encode()).hexdigest(), 16)
            bucket = (hash_val % 100) / 100.0

            cumulative = 0.0
            chosen = exp.variants[0].variant_id
            for variant in exp.variants:
                cumulative += variant.weight
                if bucket <= cumulative:
                    chosen = variant.variant_id
                    break

            assignments[exp_id] = chosen

        return assignments

    @classmethod
    def record_metric(
        cls,
        experiment_id: str,
        variant_id: str,
        turn_latency_ms: float,
        ttft_ms: float,
        scorecard_score: float
    ):
        if experiment_id not in cls._records:
            cls._records[experiment_id] = []

        cls._records[experiment_id].append({
            "variant_id": variant_id,
            "turn_latency_ms": turn_latency_ms,
            "ttft_ms": ttft_ms,
            "scorecard_score": scorecard_score
        })

    @classmethod
    def get_experiment_results(cls, experiment_id: str) -> Optional[ExperimentResult]:
        if not cls._experiments:
            cls.initialize_defaults()

        exp = cls._experiments.get(experiment_id)
        if not exp:
            return None

        records = cls._records.get(experiment_id, [])
        perf_map: Dict[str, List[Dict[str, Any]]] = {}
        for var in exp.variants:
            perf_map[var.variant_id] = []

        for rec in records:
            v_id = rec["variant_id"]
            if v_id in perf_map:
                perf_map[v_id].append(rec)

        variant_performances: List[VariantPerformance] = []
        for var in exp.variants:
            samples = perf_map[var.variant_id]
            if samples:
                avg_turn = sum(s["turn_latency_ms"] for s in samples) / len(samples)
                avg_ttft = sum(s["ttft_ms"] for s in samples) / len(samples)
                avg_score = sum(s["scorecard_score"] for s in samples) / len(samples)
                variant_performances.append(VariantPerformance(
                    variant_id=var.variant_id,
                    sample_count=len(samples),
                    avg_turn_latency_ms=round(avg_turn, 2),
                    avg_ttft_ms=round(avg_ttft, 2),
                    avg_scorecard_score=round(avg_score, 2)
                ))
            else:
                variant_performances.append(VariantPerformance(
                    variant_id=var.variant_id,
                    sample_count=0
                ))

        return ExperimentResult(
            experiment_id=exp.experiment_id,
            title=exp.title,
            is_active=exp.is_active,
            total_sessions_allocated=len(records),
            variant_performances=variant_performances
        )
