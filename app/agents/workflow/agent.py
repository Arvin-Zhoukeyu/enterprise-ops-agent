import uuid

from langgraph.types import (
    Command,
)

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
        user_role: str = "employee",
        thread_id: str | None = None,
    ):

        if thread_id is None:

            thread_id = str(
                uuid.uuid4()
            )

        initial_state = {

            "user_input":
                user_input,

            "user_role":
                user_role,

            "thread_id":
                thread_id,

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

            "pending_action":
                None,

            "approval_status":
                "",

            "final_answer":
                "",

            "error":
                None,
        }

        config = {
            "configurable": {
                "thread_id":
                    thread_id
            }
        }

        result = self.graph.invoke(
            initial_state,
            config=config,
        )

        self.last_state = result

        return {
            "thread_id":
                thread_id,

            "result":
                result,
        }

    def resume(
        self,
        thread_id: str,
        approved: bool,
    ):

        config = {
            "configurable": {
                "thread_id":
                    thread_id
            }
        }

        result = self.graph.invoke(
            Command(
                resume={
                    "approved":
                        approved
                }
            ),
            config=config,
        )

        self.last_state = result

        return result