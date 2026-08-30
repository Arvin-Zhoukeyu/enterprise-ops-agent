from app.agents.workflow.state import (
    AgentState,
)


def route_after_intent(
    state: AgentState,
) -> str:

    if state["requires_tools"]:
        return "planner"

    return "direct_answer"

def route_after_execution(
    state: AgentState,
) -> str:

    if (
        state["current_step"]
        < len(state["plan"])
    ):

        return "tool_executor"

    return "verifier"

def route_after_verification(
    state: AgentState,
) -> str:

    if (
        state[
            "verification_status"
        ]
        == "PASS"
    ):
        return "final_answer"

    if (
        state["replan_count"]
        >= 2
    ):
        return "final_answer"

    return "replan"