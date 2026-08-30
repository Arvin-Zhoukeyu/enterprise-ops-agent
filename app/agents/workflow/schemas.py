from typing import Any, Literal

from pydantic import BaseModel, Field


class RouteDecision(BaseModel):

    intent: str = Field(
        description=(
            "Short machine-readable intent."
        )
    )

    requires_tools: bool


class PlanStep(BaseModel):

    tool: str

    arguments: dict[str, Any]


class AgentPlan(BaseModel):

    steps: list[PlanStep]


class VerificationResult(BaseModel):

    status: Literal[
        "PASS",
        "FAIL",
    ]

    reason: str