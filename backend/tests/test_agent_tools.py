import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.agent.tools.executor import AgentToolExecutor

def test_python_sandbox_execution_success():
    res = AgentToolExecutor.execute_python_sandbox(
        code="res = sum([x**2 for x in range(1, 5)])\nprint(f'Sum of squares: {res}')"
    )
    assert res.exit_code == 0
    assert "Sum of squares: 30" in res.stdout
    assert res.execution_time_ms > 0

def test_python_sandbox_execution_error():
    res = AgentToolExecutor.execute_python_sandbox(
        code="print(undefined_variable + 10)"
    )
    assert res.exit_code != 0
    assert "NameError" in res.stderr

def test_python_sandbox_execution_timeout():
    res = AgentToolExecutor.execute_python_sandbox(
        code="import time; time.sleep(2)",
        timeout_seconds=0.3
    )
    assert res.exit_code == -1
    assert "timed out" in res.stderr

def test_architecture_diagram_generator():
    diag = AgentToolExecutor.generate_architecture_diagram(
        components=["Client Browser", "API Gateway", "Orders Service", "Redis Cache", "PostgreSQL DB"],
        title="E-Commerce Architecture"
    )
    assert diag.title == "E-Commerce Architecture"
    assert "flowchart TD" in diag.mermaid_syntax
    assert len(diag.nodes) == 5
    assert len(diag.edges) >= 4

def test_docs_lookup_and_human_flag():
    doc = AgentToolExecutor.lookup_documentation("postgres_mvcc")
    assert "PostgreSQL" in doc.engine
    assert "MVCC" in doc.summary

    flag = AgentToolExecutor.flag_for_human_review(
        session_id="sess-test-01",
        category="FATAL_MISCONCEPTION",
        reason="Claimed zero-latency 2PC across cross-cloud regions.",
        candidate_claim="Our 2PC transactions had 0ms latency across AWS and GCP."
    )
    assert flag.session_id == "sess-test-01"
    assert flag.category == "FATAL_MISCONCEPTION"

@pytest.mark.asyncio
async def test_api_agent_tools_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. List tools
        tools_resp = await ac.get("/api/agent/tools")
        assert tools_resp.status_code == 200
        tools = tools_resp.json()
        assert len(tools) == 4
        names = [t["name"] for t in tools]
        assert "execute_code_snippet" in names
        assert "generate_architecture_diagram" in names

        # 2. Execute Python code tool
        exec_resp = await ac.post("/api/agent/tools/execute", json={
            "tool_name": "execute_code_snippet",
            "arguments": {
                "code": "print('Tool API Execution OK')"
            }
        })
        assert exec_resp.status_code == 200
        exec_data = exec_resp.json()
        assert exec_data["status"] == "success"
        assert "Tool API Execution OK" in exec_data["output"]["stdout"]
