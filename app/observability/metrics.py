from prometheus_client import (
    Counter,
    Histogram,
)


AGENT_REQUESTS = Counter(
    "agent_requests_total",
    "Total number of agent requests",
    [
        "status",
    ],
)


AGENT_LATENCY = Histogram(
    "agent_latency_seconds",
    "Agent execution latency",
)


AGENT_TOOL_CALLS = Counter(
    "agent_tool_calls_total",
    "Total agent tool calls",
    [
        "tool",
        "status",
    ],
)


AGENT_REPLANS = Counter(
    "agent_replans_total",
    "Total agent replanning events",
)


AGENT_APPROVALS = Counter(
    "agent_approvals_total",
    "Human approval decisions",
    [
        "decision",
    ],
)