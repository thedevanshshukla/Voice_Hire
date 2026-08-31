# ADR-013: Mid-Interview Agent Tools, Code Sandbox & Architecture Visualizer

## Status
Accepted (v0.13.0)

## Context
During software engineering interviews, candidates frequently provide code snippets (algorithms, concurrency primitives, queries) and propose distributed system topologies. A voice-only interviewer cannot verify if code compiles, execute algorithm edge cases, visualize multi-tier microservice data flows, or query official documentation to settle technical disputes. VoiceHire requires a modular Agent Tools & Actions framework to execute sandboxed code, generate interactive Mermaid architecture diagrams, and log audit flags for human reviewers.

## Decision
1. **Agent Tool Registry & Dispatch Architecture**:
   - `AgentToolExecutor`: Dispatches structured function calls with validation and execution telemetry (`execution_time_ms`).
   - Tools implemented:
     - `execute_code_snippet`: Safe Python 3 sandbox execution with strict timeout limits and stdout/stderr capture.
     - `generate_architecture_diagram`: Synthesizes Mermaid flowchart syntax and node-edge topologies from candidate component lists.
     - `lookup_documentation`: Authoritative technical engine documentation retrieval (Postgres MVCC, Kafka rebalances, Redis clustering).
     - `flag_for_human_review`: Dispatches audit flags for recruiter / EM review.

2. **REST APIs & WebSocket Broadcasts**:
   - `GET /api/agent/tools`: Returns OpenAI-compatible JSON Schema tool specifications.
   - `POST /api/agent/tools/execute`: Executes tools directly.
   - WebSocket emits `tool_executed` events when tools are triggered mid-interview.

3. **Frontend Architecture Visualizer & Python Console**:
   - "🛠️ Architecture & Tools" tab in the Scorecard modal.
   - Dynamic node badges (`database`, `cache`, `queue`, `proxy`, `client`, `service`) with syntax-highlighted Mermaid code.
   - Interactive Python Code Sandbox runner with stdout/stderr console.

## Consequences
### Positive
- Allows live interactive verification of candidate code algorithms and data structures.
- Provides immediate visual representation of complex system designs during the System Design stage.
- Gives recruiters authoritative documentation references to resolve technical debates.

### Tradeoffs
- Code execution requires strict timeout boundaries to avoid hanging during realtime voice interactions.
