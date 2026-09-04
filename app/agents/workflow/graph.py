from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.workflow.nodes import (
    approval_node,
    direct_answer_node,
    execute_approved_action_node,
    final_answer_node,
    planner_node,
    replan_node,
    router_node,
    tool_executor_node,
    verifier_node,
)
from app.agents.workflow.router import (
    route_after_approved_execution,
    route_after_approval,
    route_after_execution,
    route_after_intent,
    route_after_verification,
)
from app.agents.workflow.state import AgentState


def build_agent_graph():
    """
    Build and compile the EnterpriseOps Agent workflow.

    Workflow:
          |
          v
        router
          |
          +----------------------+
          |                      |
          v                      v
       planner             direct_answer
          |                      |
          v                      v
    tool_executor                END
          |
          +-----------------------------+
          |                             |
          | read / next step            | write operation
          v                             v
    tool_executor                    approval
          |                             |
          |                             v
          |                  execute_approved_action
          |                             |
          +-------------+---------------+
                        |
                        v
                     verifier
                    /        \
                 PASS         FAIL
                  |             |
                  v             v
            final_answer      replan
                  |             |
                  v             |
                 END <----------+
                                |
                                v
                          tool_executor
    """

    # --------------------------------------------------
    # 1. Checkpointer
    # --------------------------------------------------
    #
    # Required for:
    # - thread state
    # - human-in-the-loop interrupt
    # - resume()
    #
    # Part 6 uses memory storage.
    # Part 7 can replace this with persistent storage.
    #

    checkpointer = InMemorySaver()

    # --------------------------------------------------
    # 2. Create graph
    # --------------------------------------------------

    graph = StateGraph(
        AgentState
    )

    # --------------------------------------------------
    # 3. Register nodes
    # --------------------------------------------------

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
        "approval",
        approval_node,
    )

    graph.add_node(
        "execute_approved_action",
        execute_approved_action_node,
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

    # --------------------------------------------------
    # 4. START -> Router
    # --------------------------------------------------

    graph.add_edge(
        START,
        "router",
    )

    # --------------------------------------------------
    # 5. Router decision
    # --------------------------------------------------
    #
    # General knowledge:
    #
    # router
    #   -> direct_answer
    #
    # Enterprise/private data:
    #
    # router
    #   -> planner
    #

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

    # --------------------------------------------------
    # 6. Planner -> Tool Executor
    # --------------------------------------------------

    graph.add_edge(
        "planner",
        "tool_executor",
    )

    # --------------------------------------------------
    # 7. Tool Executor routing
    # --------------------------------------------------
    #
    # Possible routes:
    #
    # More read steps:
    #   -> tool_executor
    #
    # Write operation:
    #   -> approval
    #
    # Plan finished:
    #   -> verifier
    #

    graph.add_conditional_edges(
        "tool_executor",
        route_after_execution,
        {
            "tool_executor":
                "tool_executor",

            "approval":
                "approval",

            "verifier":
                "verifier",
        },
    )

    # --------------------------------------------------
    # 8. Human approval
    # --------------------------------------------------
    #
    # approval_node uses LangGraph interrupt().
    #
    # Graph pauses here until resume() is called.
    #

    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "execute_approved_action":
                "execute_approved_action",
        },
    )

    # --------------------------------------------------
    # 9. Execute approved/rejected action
    # --------------------------------------------------
    #
    # After processing the write action:
    #
    # More plan steps:
    #   -> tool_executor
    #
    # All steps finished:
    #   -> verifier
    #

    graph.add_conditional_edges(
        "execute_approved_action",
        route_after_approved_execution,
        {
            "tool_executor":
                "tool_executor",

            "verifier":
                "verifier",
        },
    )

    # --------------------------------------------------
    # 10. Verifier routing
    # --------------------------------------------------
    #
    # PASS:
    #   -> final_answer
    #
    # FAIL:
    #   -> replan
    #
    # Too many replans:
    #   -> final_answer
    #

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

    # --------------------------------------------------
    # 11. Replan -> Executor
    # --------------------------------------------------

    graph.add_edge(
        "replan",
        "tool_executor",
    )

    # --------------------------------------------------
    # 12. End routes
    # --------------------------------------------------

    graph.add_edge(
        "direct_answer",
        END,
    )

    graph.add_edge(
        "final_answer",
        END,
    )

    # --------------------------------------------------
    # 13. Compile graph
    # --------------------------------------------------
    #
    # Checkpointer enables:
    #
    # graph.invoke(
    #     state,
    #     config={
    #         "configurable": {
    #             "thread_id": "..."
    #         }
    #     }
    # )
    #
    # and later:
    #
    # graph.invoke(
    #     Command(resume=...),
    #     same_config
    # )
    #

    compiled_graph = graph.compile(
        checkpointer=checkpointer
    )

    return compiled_graph