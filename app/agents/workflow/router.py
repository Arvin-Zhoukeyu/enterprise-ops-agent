from app.agents.workflow.state import AgentState


def route_after_intent(
    state: AgentState,
) -> str:
    """
    After the Router node:

    - Tool required -> Planner
    - General knowledge -> Direct Answer
    """

    if state["requires_tools"]:
        return "planner"

    return "direct_answer"


def route_after_execution(
    state: AgentState,
) -> str:
    """
    After Tool Executor:

    1. If a write operation is waiting for approval,
       go to the approval node.

    2. If there are more plan steps,
       continue executing tools.

    3. If all steps are finished,
       go to Verifier.
    """

    if state.get("pending_action") is not None:
        return "approval"

    if (
        state["current_step"]
        < len(state["plan"])
    ):
        return "tool_executor"

    return "verifier"


def route_after_verification(
    state: AgentState,
) -> str:
    """
    After Verifier:

    PASS
        -> generate final answer

    FAIL
        -> try replanning

    Too many replans
        -> stop retrying and generate a final answer
           based on currently available evidence.
    """

    if (
        state["verification_status"]
        == "PASS"
    ):
        return "final_answer"

    if (
        state["replan_count"]
        >= 2
    ):
        return "final_answer"

    return "replan"


def route_after_approval(
    state: AgentState,
) -> str:
    """
    After the human approval node,
    continue to the execution node.

    The execution node itself checks whether
    the operation was approved or rejected.
    """

    return "execute_approved_action"


def route_after_approved_execution(
    state: AgentState,
) -> str:
    """
    After an approved/rejected write action:

    - Continue if more plan steps exist.
    - Otherwise verify the overall task.
    """

    if (
        state["current_step"]
        < len(state["plan"])
    ):
        return "tool_executor"

    return "verifier"