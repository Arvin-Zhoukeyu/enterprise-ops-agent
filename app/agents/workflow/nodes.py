import json
from typing import Any

from openai import OpenAI

from app.agents.workflow.schemas import (
    AgentPlan,
    RouteDecision,
    VerificationResult,
)
from app.agents.workflow.state import (
    AgentState,
)
from app.core.config import settings
from app.tools import (
    load_tools,
    tool_registry,
)
from app.security.permissions import (
    has_permission,
)
from langgraph.types import (
    interrupt,
)


client = OpenAI(
    api_key=settings.openai_api_key
)

load_tools()

def router_node(
    state: AgentState,
) -> dict:

    prompt = f"""
Classify this enterprise operations request.

User request:
{state["user_input"]}

Determine:

1. A short intent name.
2. Whether enterprise tools are required.

Enterprise tools are required when the request
depends on private supplier, purchase order,
risk event, or ticket data.

General conceptual questions do not require tools.

Return JSON only:

{{
  "intent": "...",
  "requires_tools": true
}}
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    raw = response.output_text

    data = json.loads(raw)

    decision = (
        RouteDecision.model_validate(
            data
        )
    )

    print(
        "\n[Router]"
    )

    print(
        f"Intent: {decision.intent}"
    )

    print(
        "Requires tools: "
        f"{decision.requires_tools}"
    )

    return {
        "intent":
            decision.intent,

        "requires_tools":
            decision.requires_tools,
    }
def direct_answer_node(
    state: AgentState,
) -> dict:

    prompt = f"""
You are EnterpriseOps Agent.

Answer this general enterprise operations
question clearly and concisely.

Do not claim to have queried enterprise
systems.

Question:

{state["user_input"]}
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    print(
        "\n[Direct Answer]"
    )

    return {
        "final_answer":
            response.output_text
    }

def planner_node(
    state: AgentState,
) -> dict:

    available_tools = []

    for tool in (
        tool_registry.list_tools()
    ):

        available_tools.append(
            {
                "name":
                    tool.name,

                "description":
                    tool.description,

                "permission":
                    tool.permission,

                "side_effect":
                    tool.side_effect,

                "parameters":
                    tool.input_model
                    .model_json_schema(),
            }
        )

    prompt = f"""
You are the planning component of an enterprise
operations agent.

User request:

{state["user_input"]}

Intent:

{state["intent"]}

Available tools:

{json.dumps(
    available_tools,
    ensure_ascii=False,
    default=str
)}

Create the minimum tool execution plan required
to answer the request.

Rules:

- Use only tools from the available tool list.
- Never invent tool names.
- Prefer read-only tools.
- Do not add unnecessary steps.
- Extract arguments carefully from the user request.
- Do not execute tools.
- Only create a plan.

Return JSON:

{{
  "steps": [
    {{
      "tool": "...",
      "arguments": {{}}
    }}
  ]
}}
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    data = json.loads(
        response.output_text
    )

    plan = AgentPlan.model_validate(
        data
    )

    steps = [
        {
            "tool":
                step.tool,

            "arguments":
                step.arguments,
        }
        for step in plan.steps
    ]

    print(
        "\n[Planner]"
    )

    for index, step in enumerate(
        steps,
        start=1,
    ):

        print(
            f"Step {index}: "
            f"{step['tool']} "
            f"{step['arguments']}"
        )

    return {
        "plan": steps,
        "current_step": 0,
    }

def tool_executor_node(
    state: AgentState,
) -> dict:

    plan = state["plan"]

    current_step = (
        state["current_step"]
    )

    observations = list(
        state["observations"]
    )

    if current_step >= len(plan):

        return {
            "observations":
                observations
        }

    step = plan[
        current_step
    ]

    tool_name = (
        step["tool"]
    )

    arguments = (
        step["arguments"]
    )

    print(
        "\n[Executor]"
    )

    print(
        f"Tool: {tool_name}"
    )

    print(
        f"Arguments: {arguments}"
    )

    try:

        tool = tool_registry.get(
            tool_name
        )

    except Exception as exc:

        observations.append(
            {
                "step":
                    current_step,

                "tool":
                    tool_name,

                "status":
                    "FAILED",

                "result": {
                    "error":
                        str(exc)
                },
            }
        )

        return {
            "observations":
                observations,

            "current_step":
                current_step + 1,
        }

    #
    # RBAC
    #

    if not has_permission(
        state["user_role"],
        tool.permission,
    ):

        result = {
            "success": False,

            "error":
                "permission_denied",

            "required_permission":
                tool.permission,

            "user_role":
                state[
                    "user_role"
                ],
        }

        observations.append(
            {
                "step":
                    current_step,

                "tool":
                    tool_name,

                "arguments":
                    arguments,

                "status":
                    "PERMISSION_DENIED",

                "result":
                    result,
            }
        )

        return {
            "observations":
                observations,

            "current_step":
                current_step + 1,
        }

    #
    # Write Tool
    #

    if tool.side_effect:

        print(
            "[Executor] "
            "Human approval required."
        )

        return {
            "pending_action": {
                "tool":
                    tool_name,

                "arguments":
                    arguments,

                "step":
                    current_step,
            },

            "approval_status":
                "PENDING",
        }

    #
    # Read Tool
    #

    try:

        result = (
            tool_registry.execute(
                tool_name,
                arguments,
            )
        )

        status = "SUCCESS"

    except Exception as exc:

        result = {
            "success": False,
            "error": str(exc),
        }

        status = "FAILED"

    observations.append(
        {
            "step":
                current_step,

            "tool":
                tool_name,

            "arguments":
                arguments,

            "status":
                status,

            "result":
                result,
        }
    )

    return {
        "observations":
            observations,

        "current_step":
            current_step + 1,
    }

def verifier_node(
    state: AgentState,
) -> dict:

    prompt = f"""
You are the verification component of an
enterprise operations agent.

Original user request:

{state["user_input"]}

Execution plan:

{json.dumps(
    state["plan"],
    ensure_ascii=False,
    default=str
)}

Tool observations:

{json.dumps(
    state["observations"],
    ensure_ascii=False,
    default=str
)}

Determine whether the collected evidence is
sufficient to answer the user's request.

PASS:
The observations contain enough reliable
information to answer.

FAIL:
Important information is missing, a tool failed,
or the plan was insufficient.

Return JSON:

{{
  "status": "PASS",
  "reason": "..."
}}
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    data = json.loads(
        response.output_text
    )

    verification = (
        VerificationResult
        .model_validate(data)
    )

    print(
        "\n[Verifier]"
    )

    print(
        f"Status: "
        f"{verification.status}"
    )

    print(
        f"Reason: "
        f"{verification.reason}"
    )

    return {
        "verification_status":
            verification.status,

        "verification_reason":
            verification.reason,
    }

def replan_node(
    state: AgentState,
) -> dict:

    if state["replan_count"] >= 2:

        return {
            "error":
                "maximum_replan_reached"
        }

    available_tools = [
        {
            "name": tool.name,
            "description":
                tool.description,
        }
        for tool in (
            tool_registry.list_tools()
        )
    ]

    prompt = f"""
The previous enterprise agent plan was
insufficient.

User request:

{state["user_input"]}

Previous plan:

{json.dumps(
    state["plan"],
    ensure_ascii=False,
    default=str
)}

Observations:

{json.dumps(
    state["observations"],
    ensure_ascii=False,
    default=str
)}

Verifier feedback:

{state["verification_reason"]}

Available tools:

{json.dumps(
    available_tools,
    ensure_ascii=False
)}

Create a corrected minimal plan.

Do not repeat failed steps unless changing their
arguments can reasonably fix the problem.

Return JSON:

{{
  "steps": [
    {{
      "tool": "...",
      "arguments": {{}}
    }}
  ]
}}
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    data = json.loads(
        response.output_text
    )

    plan = AgentPlan.model_validate(
        data
    )

    steps = [
        {
            "tool": step.tool,
            "arguments":
                step.arguments,
        }
        for step in plan.steps
    ]

    print(
        "\n[Replanner]"
    )

    print(
        f"Attempt: "
        f"{state['replan_count'] + 1}"
    )

    for step in steps:

        print(
            step
        )

    return {
        "plan": steps,

        "current_step": 0,

        "replan_count":
            state[
                "replan_count"
            ] + 1,
    }

def final_answer_node(
    state: AgentState,
) -> dict:

    prompt = f"""
You are EnterpriseOps Agent.

Answer the user's request using only the
enterprise evidence collected below.

User request:

{state["user_input"]}

Evidence:

{json.dumps(
    state["observations"],
    ensure_ascii=False,
    default=str
)}

Verification:

{state["verification_status"]}

Verifier reason:

{state["verification_reason"]}

Rules:

- Do not invent enterprise facts.
- Clearly state when information is unavailable.
- Keep the answer business-focused.
- Mention relevant supplier/order/risk identifiers.
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    return {
        "final_answer":
            response.output_text
    }

def approval_node(
    state: AgentState,
) -> dict:

    pending = (
        state["pending_action"]
    )

    if pending is None:

        return {
            "approval_status":
                "NOT_REQUIRED"
        }

    decision = interrupt(
        {
            "type":
                "approval_required",

            "message":
                "A write operation requires "
                "human approval.",

            "tool":
                pending["tool"],

            "arguments":
                pending[
                    "arguments"
                ],

            "user_role":
                state[
                    "user_role"
                ],
        }
    )

    approved = (
        decision.get(
            "approved",
            False,
        )
    )

    if not approved:

        return {
            "approval_status":
                "REJECTED"
        }

    return {
        "approval_status":
            "APPROVED"
    }

def execute_approved_action_node(
    state: AgentState,
) -> dict:

    pending = (
        state["pending_action"]
    )

    observations = list(
        state["observations"]
    )

    if pending is None:

        return {
            "observations":
                observations
        }

    if (
        state["approval_status"]
        != "APPROVED"
    ):

        observations.append(
            {
                "tool":
                    pending["tool"],

                "arguments":
                    pending[
                        "arguments"
                    ],

                "status":
                    "REJECTED",

                "result": {
                    "success":
                        False,

                    "error":
                        "human_rejected",
                },
            }
        )

        return {
            "observations":
                observations,

            "pending_action":
                None,

            "current_step":
                state[
                    "current_step"
                ] + 1,
        }

    try:

        result = (
            tool_registry.execute(
                pending["tool"],
                pending["arguments"],
            )
        )

        status = "SUCCESS"

    except Exception as exc:

        result = {
            "success": False,
            "error":
                str(exc),
        }

        status = "FAILED"

    observations.append(
        {
            "tool":
                pending["tool"],

            "arguments":
                pending[
                    "arguments"
                ],

            "status":
                status,

            "result":
                result,
        }
    )

    return {
        "observations":
            observations,

        "pending_action":
            None,

        "current_step":
            state[
                "current_step"
            ] + 1,
    }