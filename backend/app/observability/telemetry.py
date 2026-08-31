from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import time
import uuid

class TurnSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: f"span-{uuid.uuid4().hex[:8]}")
    session_id: Optional[str] = None
    turn_index: int = 1
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Latencies in milliseconds
    audio_ingest_ms: float = 0.0
    vad_endpoint_ms: float = 0.0
    stt_latency_ms: float = 0.0
    llm_ttft_ms: float = 0.0
    llm_total_ms: float = 0.0
    tool_execution_ms: float = 0.0
    tts_ttfa_ms: float = 0.0
    tts_total_ms: float = 0.0
    barge_in_latency_ms: float = 0.0
    e2e_latency_ms: float = 0.0

    stt_provider: str = "mock"
    llm_provider: str = "mock"
    tts_provider: str = "mock"
    language: str = "en"
    was_interrupted: bool = False

    def finish(self):
        self.end_time = time.time()
        self.e2e_latency_ms = round((self.end_time - self.start_time) * 1000, 2)

class MetricsExporter:
    """
    In-memory metrics collector and Prometheus format exporter for Voice AI pipeline telemetry.
    """
    _spans: List[TurnSpan] = []
    _turn_counter: int = 0
    _interruption_counter: int = 0

    @classmethod
    def record_span(cls, span: TurnSpan):
        span.finish()
        cls._spans.append(span)
        cls._turn_counter += 1
        if span.was_interrupted:
            cls._interruption_counter += 1

    @classmethod
    def get_summary_stats(cls) -> Dict[str, Any]:
        if not cls._spans:
            return {
                "total_turns": 0,
                "total_interruptions": 0,
                "avg_e2e_latency_ms": 0.0,
                "avg_llm_ttft_ms": 0.0,
                "avg_tts_ttfa_ms": 0.0
            }

        n = len(cls._spans)
        avg_e2e = sum(s.e2e_latency_ms for s in cls._spans) / n
        avg_ttft = sum(s.llm_ttft_ms for s in cls._spans) / n
        avg_ttfa = sum(s.tts_ttfa_ms for s in cls._spans) / n

        return {
            "total_turns": cls._turn_counter,
            "total_interruptions": cls._interruption_counter,
            "avg_e2e_latency_ms": round(avg_e2e, 2),
            "avg_llm_ttft_ms": round(avg_ttft, 2),
            "avg_tts_ttfa_ms": round(avg_ttfa, 2)
        }

    @classmethod
    def generate_prometheus_metrics(cls) -> str:
        stats = cls.get_summary_stats()
        lines = [
            "# HELP voicehire_turns_total Total number of voice interview turns processed",
            "# TYPE voicehire_turns_total counter",
            f"voicehire_turns_total {stats['total_turns']}",
            "",
            "# HELP voicehire_interruptions_total Total number of candidate barge-in interruptions",
            "# TYPE voicehire_interruptions_total counter",
            f"voicehire_interruptions_total {stats['total_interruptions']}",
            "",
            "# HELP voicehire_turn_latency_ms_avg Average end-to-end turn latency in milliseconds",
            "# TYPE voicehire_turn_latency_ms_avg gauge",
            f"voicehire_turn_latency_ms_avg {stats['avg_e2e_latency_ms']}",
            "",
            "# HELP voicehire_llm_ttft_ms_avg Average LLM time-to-first-token in milliseconds",
            "# TYPE voicehire_llm_ttft_ms_avg gauge",
            f"voicehire_llm_ttft_ms_avg {stats['avg_llm_ttft_ms']}",
            "",
            "# HELP voicehire_tts_ttfa_ms_avg Average TTS time-to-first-audio in milliseconds",
            "# TYPE voicehire_tts_ttfa_ms_avg gauge",
            f"voicehire_tts_ttfa_ms_avg {stats['avg_tts_ttfa_ms']}",
            ""
        ]
        return "\n".join(lines)
