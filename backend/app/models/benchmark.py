from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

class GoldenInterviewSample(BaseModel):
    sample_id: str
    role: str
    level: str
    topic: str
    stage: str
    candidate_reply: str
    expected_overall_score: float
    expected_red_flag: Optional[str] = None

class SampleEvaluationResult(BaseModel):
    sample_id: str
    expected_score: float
    predicted_score: float
    absolute_error: float
    expected_red_flag: Optional[str] = None
    detected_red_flag: Optional[str] = None
    red_flag_matched: bool

class BenchmarkRunSummary(BaseModel):
    total_samples: int
    mean_absolute_error: float
    accuracy_within_half_point_pct: float
    red_flag_precision: float
    red_flag_recall: float
    sample_results: List[SampleEvaluationResult] = Field(default_factory=list)
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
