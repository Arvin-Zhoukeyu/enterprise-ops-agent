from app.agents.workflow.graph import (
    build_agent_graph,
)


class WorkflowAgent:

    def __init__(self):

        self.graph = (
            build_agent_graph()
        )

        self.last_state = None

    def run(
        self,
        user_input: str,
    ) -> str:

        initial_state = {
            "user_input":
                user_input,

            "intent":
                "",

            "requires_tools":
                False,

            "plan":
                [],

            "current_step":
                0,

            "observations":
                [],

            "verification_status":
                "",

            "verification_reason":
                "",

            "replan_count":
                0,

            "final_answer":
                "",

            "error":
                None,
        }

        result = self.graph.invoke(
            initial_state
        )

        self.last_state = result

        return result[
            "final_answer"
        ]