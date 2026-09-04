# EnterpriseOps Agent

A production-oriented AI Agent for enterprise procurement and supply-chain risk operations.

The project demonstrates how a simple LLM function-calling agent can evolve into a stateful, controllable and observable enterprise agent system using LangGraph, RAG, RBAC, Human-in-the-loop, asynchronous execution and containerized deployment.

---

## Overview

EnterpriseOps Agent is designed for procurement and supply-chain risk scenarios.

The agent can:

- Query supplier information
- Search purchase orders
- Identify high-risk orders
- Retrieve operational risk events
- Search enterprise procurement and supplier policies
- Combine structured business data with unstructured policy knowledge
- Generate multi-step execution plans
- Verify tool execution results
- Replan when evidence is insufficient
- Enforce role-based tool permissions
- Pause write operations for human approval
- Resume interrupted workflows
- Run synchronous or asynchronous agent tasks
- Record execution traces and metrics

The project uses synthetic enterprise data and policies for demonstration purposes.

---

## Motivation

A basic LLM agent can call tools, but complex enterprise tasks require more than function calling.

Several engineering problems appear quickly:

1. Complex tasks may require multiple dependent tool calls.
2. LLM decisions need to be observable and controllable.
3. Enterprise policies are private and cannot be assumed by the model.
4. Write operations require permission and human approval.
5. Agent workflows need failure recovery.
6. Production systems require logging, metrics, evaluation and deployment support.

This project addresses these problems incrementally.

---

## Architecture Evolution

### V1 — Function Calling Baseline

User
→ LLM
→ Function Calling
→ Business Tool
→ Answer

The baseline agent validates whether direct tool calling is sufficient for enterprise queries.

### V2 — LangGraph Workflow Agent

User
→ Router
→ Planner
→ Tool Executor
→ Verifier
→ Replanner
→ Final Answer

The workflow explicitly models agent execution using State, Nodes and Conditional Edges.

### V3 — Enterprise Knowledge

Structured Business Data
+
Enterprise Policy RAG
→ Risk Analysis

Enterprise policies are retrieved from a vector knowledge base instead of relying on model memory.

### V4 — Security and Human Approval

Tool Call
→ RBAC
→ Human Approval
→ Execute

State-changing actions cannot be performed automatically.

### V5 — Production Runtime

FastAPI
→ Agent Service
→ LangGraph
→ PostgreSQL / Chroma
→ Redis Worker
→ Metrics / Logging
→ Docker

---

## System Architecture

```mermaid
flowchart TD

    U[Client] --> API[FastAPI]

    API --> S[Agent Service]

    S --> G[LangGraph Agent]

    G --> R[Router]
    R --> P[Planner]

    P --> E[Tool Executor]

    E --> ST[Supplier Tools]
    E --> OT[Order Tools]
    E --> RT[Risk Tools]
    E --> KT[Policy RAG Tool]

    ST --> DB[(PostgreSQL)]
    OT --> DB
    RT --> DB

    KT --> VS[(Chroma Vector Store)]

    E --> V[Verifier]

    V -->|PASS| F[Final Answer]
    V -->|FAIL| RP[Replanner]

    RP --> E

    E -->|Write Tool| RBAC[RBAC]

    RBAC --> HITL[Human Approval]

    HITL -->|Approved| W[Execute Write Action]
    HITL -->|Rejected| F

    W --> V

    API --> Q[Redis Queue]
    Q --> WK[Worker]
    WK --> S

    G --> OBS[Observability]

    OBS --> LOG[Structured Logs]
    OBS --> MET[Prometheus Metrics]
    OBS --> TRACE[Agent Traces]