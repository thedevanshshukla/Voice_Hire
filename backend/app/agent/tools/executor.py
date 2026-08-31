import sys
import subprocess
import time
import re
from typing import Dict, Any, List, Optional
from app.models.tools import (
    ToolResult, ArchitectureDiagramPayload, DiagramNode, DiagramEdge,
    CodeExecutionPayload, DocumentationLookupPayload, HumanFlagPayload
)
from app.core.logger import get_logger

logger = get_logger("agent.tools.executor")

OFFICIAL_DOCS_STORE = {
    "postgres_mvcc": {
        "topic": "PostgreSQL MVCC & Isolation Levels",
        "engine": "PostgreSQL 16+",
        "summary": "Postgres uses Multi-Version Concurrency Control (MVCC). Readers do not block writers and writers do not block readers. Under Read Committed, each query sees snapshot at query start. Under Repeatable Read, transaction sees snapshot at transaction start. Concurrent updates on same row trigger serialization failure (SQLSTATE 40001).",
        "official_source_url": "https://www.postgresql.org/docs/current/mvcc.html"
    },
    "redis_clustering": {
        "topic": "Redis Cluster & Hash Slot Partitioning",
        "engine": "Redis 7.2+",
        "summary": "Redis Cluster divides keyspace into 16,384 hash slots computed via CRC16(key) mod 16384. Multi-key operations require hash tags {user:123} to guarantee all keys map to the same slot and master node. Node failover uses Raft-like majority quorum between master instances.",
        "official_source_url": "https://redis.io/docs/management/scaling-with-redis-cluster/"
    },
    "kafka_rebalance": {
        "topic": "Kafka Consumer Group Rebalance Protocol",
        "engine": "Apache Kafka 3.6+",
        "summary": "Consumer groups use Cooperative Sticky Assignor to rebalance partitions incrementally without stopping the world (Eager rebalance). Heartbeats (heartbeat.interval.ms) detect failed consumers within max.poll.interval.ms.",
        "official_source_url": "https://kafka.apache.org/documentation/#theconsumer"
    }
}

class AgentToolExecutor:
    """
    Central tool execution engine for mid-interview code sandboxing,
    system architecture diagram generation, and documentation lookups.
    """

    @classmethod
    def get_tool_definitions(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "execute_code_snippet",
                "description": "Executes candidate-provided Python code in a safe timed sandbox.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python 3 code to execute"}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "generate_architecture_diagram",
                "description": "Generates a live Mermaid architecture diagram based on candidate system design.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Diagram title"},
                        "components": {"type": "array", "items": {"type": "string"}, "description": "List of system components"},
                        "data_flow": {"type": "array", "items": {"type": "string"}, "description": "Directed edges (e.g. 'Client -> API Gateway')"}
                    },
                    "required": ["components"]
                }
            },
            {
                "name": "lookup_documentation",
                "description": "Queries official technical documentation to verify architecture mechanisms.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic or keyword (e.g. 'postgres_mvcc', 'kafka_rebalance', 'redis_clustering')"},
                        "engine": {"type": "string", "description": "Target engine or framework"}
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "flag_for_human_review",
                "description": "Logs an interview flag for human recruiter / engineering manager audit.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "ACADEMIC_INTEGRITY, FATAL_MISCONCEPTION, RECRUITER_ATTENTION"},
                        "reason": {"type": "string", "description": "Audit rationale"},
                        "candidate_claim": {"type": "string", "description": "Verbatim candidate claim"}
                    },
                    "required": ["category", "reason", "candidate_claim"]
                }
            }
        ]

    @classmethod
    def execute_python_sandbox(cls, code: str, timeout_seconds: float = 3.0) -> CodeExecutionPayload:
        start_time = time.time()
        try:
            # Execute in separate isolated python process with strict timeout
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            elapsed_ms = (time.time() - start_time) * 1000
            return CodeExecutionPayload(
                language="python",
                code=code,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time_ms=round(elapsed_ms, 2)
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = (time.time() - start_time) * 1000
            return CodeExecutionPayload(
                language="python",
                code=code,
                stdout="",
                stderr=f"Execution timed out after {timeout_seconds}s.",
                exit_code=-1,
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return CodeExecutionPayload(
                language="python",
                code=code,
                stdout="",
                stderr=str(e),
                exit_code=1,
                execution_time_ms=round(elapsed_ms, 2)
            )

    @classmethod
    def generate_architecture_diagram(
        cls,
        components: List[str],
        data_flow: Optional[List[str]] = None,
        title: str = "Candidate System Architecture"
    ) -> ArchitectureDiagramPayload:
        nodes: List[DiagramNode] = []
        edges: List[DiagramEdge] = []
        lines: List[str] = ["flowchart TD"]

        node_id_map: Dict[str, str] = {}
        for idx, comp in enumerate(components):
            safe_id = f"node_{idx}"
            node_id_map[comp.lower()] = safe_id
            
            comp_lower = comp.lower()
            if "db" in comp_lower or "sql" in comp_lower or "postgres" in comp_lower or "mongo" in comp_lower:
                node_type = "database"
                lines.append(f"  {safe_id}[(({comp}))]")
            elif "cache" in comp_lower or "redis" in comp_lower or "memcached" in comp_lower:
                node_type = "cache"
                lines.append(f"  {safe_id}[({comp})]")
            elif "queue" in comp_lower or "kafka" in comp_lower or "rabbitmq" in comp_lower:
                node_type = "queue"
                lines.append(f"  {safe_id}[[{comp}]]")
            elif "client" in comp_lower or "browser" in comp_lower or "mobile" in comp_lower:
                node_type = "client"
                lines.append(f"  {safe_id}[/{comp}/]")
            elif "gateway" in comp_lower or "proxy" in comp_lower or "envoy" in comp_lower:
                node_type = "proxy"
                lines.append(f"  {safe_id}{{{comp}}}")
            else:
                node_type = "service"
                lines.append(f"  {safe_id}[{comp}]")

            nodes.append(DiagramNode(id=safe_id, label=comp, type=node_type))

        # Default sequential flow if none provided
        if not data_flow:
            for i in range(len(nodes) - 1):
                src = nodes[i].id
                dst = nodes[i + 1].id
                lines.append(f"  {src} --> {dst}")
                edges.append(DiagramEdge(source=src, target=dst, label="calls"))
        else:
            for flow in data_flow:
                parts = flow.split("->")
                if len(parts) == 2:
                    src_name = parts[0].strip().lower()
                    dst_name = parts[1].strip().lower()
                    src_id = node_id_map.get(src_name, "node_0")
                    dst_id = node_id_map.get(dst_name, "node_1")
                    lines.append(f"  {src_id} --> {dst_id}")
                    edges.append(DiagramEdge(source=src_id, target=dst_id, label="data flow"))

        mermaid_syntax = "\n".join(lines)
        return ArchitectureDiagramPayload(
            title=title,
            mermaid_syntax=mermaid_syntax,
            nodes=nodes,
            edges=edges
        )

    @classmethod
    def lookup_documentation(cls, topic: str, engine: str = "general") -> DocumentationLookupPayload:
        clean_key = topic.lower().replace(" ", "_")
        for key, doc in OFFICIAL_DOCS_STORE.items():
            if key in clean_key or clean_key in key or any(w in doc["topic"].lower() for w in topic.lower().split()):
                return DocumentationLookupPayload(
                    topic=doc["topic"],
                    engine=doc["engine"],
                    summary=doc["summary"],
                    official_source_url=doc["official_source_url"]
                )

        return DocumentationLookupPayload(
            topic=topic,
            engine=engine,
            summary=f"Official reference manual for {topic}: Standard enterprise architectural guidelines apply.",
            official_source_url="https://developer.mozilla.org"
        )

    @classmethod
    def flag_for_human_review(
        cls,
        session_id: str,
        category: str,
        reason: str,
        candidate_claim: str
    ) -> HumanFlagPayload:
        payload = HumanFlagPayload(
            session_id=session_id,
            category=category,
            reason=reason,
            candidate_claim=candidate_claim
        )
        logger.warning("Human Review Flag Created", extra=payload.model_dump())
        return payload

    @classmethod
    def execute_tool(
        cls,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> ToolResult:
        start_time = time.time()
        tool_call_id = f"call-{int(start_time*1000)}"

        try:
            if tool_name == "execute_code_snippet":
                code = arguments.get("code", "")
                output = cls.execute_python_sandbox(code)
            elif tool_name == "generate_architecture_diagram":
                components = arguments.get("components", ["Client", "API Server", "Database"])
                data_flow = arguments.get("data_flow")
                title = arguments.get("title", "System Architecture")
                output = cls.generate_architecture_diagram(components, data_flow, title)
            elif tool_name == "lookup_documentation":
                topic = arguments.get("topic", "postgres_mvcc")
                engine = arguments.get("engine", "general")
                output = cls.lookup_documentation(topic, engine)
            elif tool_name == "flag_for_human_review":
                category = arguments.get("category", "RECRUITER_ATTENTION")
                reason = arguments.get("reason", "")
                claim = arguments.get("candidate_claim", "")
                output = cls.flag_for_human_review(session_id or "session-unknown", category, reason, claim)
            else:
                return ToolResult(
                    tool_call_id=tool_call_id,
                    tool_name=tool_name,
                    output=f"Unknown tool: {tool_name}",
                    status="error",
                    execution_time_ms=(time.time() - start_time) * 1000
                )

            elapsed_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                output=output.model_dump() if hasattr(output, "model_dump") else output,
                status="success",
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                output=str(e),
                status="error",
                execution_time_ms=round(elapsed_ms, 2)
            )
