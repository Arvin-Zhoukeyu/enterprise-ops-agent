from app.observability.trace import (
    AgentRunTrace,
    ToolCallTrace,
)


def test_agent_trace_creation():

    trace = AgentRunTrace(
        trace_id="test-001",
        user_input="test query",
    )

    assert (
        trace.trace_id
        == "test-001"
    )

    assert (
        trace.tool_calls
        == []
    )

    assert (
        trace.total_tokens
        == 0
    )


def test_tool_trace_creation():

    tool_trace = ToolCallTrace(
        tool_name="get_supplier",
        arguments={
            "supplier_code":
                "SUP-2026-0003"
        },
        permission="READ",
        side_effect=False,
        status="SUCCESS",
        latency_ms=10.5,
    )

    assert (
        tool_trace.tool_name
        == "get_supplier"
    )

    assert (
        tool_trace.permission
        == "READ"
    )

    assert (
        tool_trace.side_effect
        is False
    )