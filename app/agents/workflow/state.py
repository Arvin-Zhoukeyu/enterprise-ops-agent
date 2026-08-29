from typing import Any, TypedDict


class AgentState(TypedDict):

    user_input: str

    intent: str

    requires_tools: bool

    plan: list[dict[str, Any]]

    current_step: int

    observations: list[dict[str, Any]]

    verification_status: str

    verification_reason: str

    replan_count: int

    final_answer: str

    error: str | None