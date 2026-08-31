from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

class LoadTestConfig(BaseModel):
    concurrent_sessions: int = Field(default=10, ge=1, le=100)
    turns_per_session: int = Field(default=3, ge=1, le=20)
    simulated_delay_ms: float = Field(default=10.0, ge=0.0)

class LoadTestResult(BaseModel):
    total_turns_simulated: int
    successful_turns: int
    failed_turns: int
    throughput_tps: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
