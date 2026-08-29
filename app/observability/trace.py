from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCallTrace:
    """
    Trace information for one tool execution.
    """

    tool_name: str

    arguments: dict[str, Any]

    permission: str

    side_effect: bool

    status: str

    latency_ms: float

    result: Any = None

    error: str | None = None


@dataclass
class AgentRunTrace:
    """
    Complete trace for one user request.
    """

    trace_id: str

    user_input: str

    routing: str | None = None

    tool_calls: list[ToolCallTrace] = field(
        default_factory=list
    )

    input_tokens: int = 0

    output_tokens: int = 0

    total_tokens: int = 0

    llm_calls: int = 0

    latency_ms: float = 0.0

    final_answer: str = ""

    success: bool = True

    error: str | None = None