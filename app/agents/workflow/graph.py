from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from app.agents.workflow.nodes import (
    direct_answer_node,
    final_answer_node,
    planner_node,
    replan_node,
    router_node,
    tool_executor_node,
    verifier_node,
)
from app.agents.workflow.router import (
    route_after_execution,
    route_after_intent,
    route_after_verification,
)
from app.agents.workflow.state import (
    AgentState,
)


def build_agent_graph():

    graph = StateGraph(
        AgentState
    )

    graph.add_node(
        "router",
        router_node,
    )

    graph.add_node(
        "planner",
        planner_node,
    )

    graph.add_node(
        "direct_answer",
        direct_answer_node,
    )

    graph.add_node(
        "tool_executor",
        tool_executor_node,
    )

    graph.add_node(
        "verifier",
        verifier_node,
    )

    graph.add_node(
        "replan",
        replan_node,
    )

    graph.add_node(
        "final_answer",
        final_answer_node,
    )

    graph.add_edge(
        START,
        "router",
    )

    graph.add_conditional_edges(
        "router",
        route_after_intent,
        {
            "planner":
                "planner",

            "direct_answer":
                "direct_answer",
        },
    )

    graph.add_edge(
        "planner",
        "tool_executor",
    )

    graph.add_conditional_edges(
        "tool_executor",
        route_after_execution,
        {
            "tool_executor":
                "tool_executor",

            "verifier":
                "verifier",
        },
    )

    graph.add_conditional_edges(
        "verifier",
        route_after_verification,
        {
            "final_answer":
                "final_answer",

            "replan":
                "replan",
        },
    )

    graph.add_edge(
        "replan",
        "tool_executor",
    )

    graph.add_edge(
        "direct_answer",
        END,
    )

    graph.add_edge(
        "final_answer",
        END,
    )

    return graph.compile()