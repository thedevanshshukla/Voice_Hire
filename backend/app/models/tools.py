from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

class ToolCall(BaseModel):
    tool_call_id: str = Field(default_factory=lambda: f"call-{uuid.uuid4().hex[:8]}")
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ToolResult(BaseModel):
    tool_call_id: str
    tool_name: str
    output: Any
    status: str = "success" # "success" or "error"
    execution_time_ms: float = 0.0

class DiagramNode(BaseModel):
    id: str
    label: str
    type: str = "service" # "client", "proxy", "service", "cache", "database", "queue"

class DiagramEdge(BaseModel):
    source: str
    target: str
    label: str = ""

class ArchitectureDiagramPayload(BaseModel):
    title: str = "Candidate Architecture Design"
    mermaid_syntax: str
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)

class CodeExecutionPayload(BaseModel):
    language: str = "python"
    code: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time_ms: float = 0.0

class DocumentationLookupPayload(BaseModel):
    topic: str
    engine: str
    summary: str
    official_source_url: str

class HumanFlagPayload(BaseModel):
    session_id: str
    category: str # "ACADEMIC_INTEGRITY", "FATAL_MISCONCEPTION", "RECRUITER_ATTENTION"
    reason: str
    candidate_claim: str
    flagged_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ExecuteToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    session_id: Optional[str] = None
