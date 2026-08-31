from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid

class ExperimentVariant(BaseModel):
    variant_id: str
    name: str
    description: str = ""
    config_overrides: Dict[str, Any] = Field(default_factory=dict)
    weight: float = 0.5

class ExperimentConfig(BaseModel):
    experiment_id: str
    title: str
    description: str = ""
    is_active: bool = True
    variants: List[ExperimentVariant] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class VariantPerformance(BaseModel):
    variant_id: str
    sample_count: int = 0
    avg_turn_latency_ms: float = 0.0
    avg_ttft_ms: float = 0.0
    avg_scorecard_score: float = 0.0

class ExperimentResult(BaseModel):
    experiment_id: str
    title: str
    is_active: bool
    total_sessions_allocated: int = 0
    variant_performances: List[VariantPerformance] = Field(default_factory=list)
