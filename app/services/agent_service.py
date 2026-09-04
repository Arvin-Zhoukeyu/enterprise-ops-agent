import time

from app.agents.workflow.agent import (
    WorkflowAgent,
)
from app.observability.metrics import (
    AGENT_APPROVALS,
    AGENT_LATENCY,
    AGENT_REQUESTS,
)


class AgentService:

    def __init__(self):

        self.agent = WorkflowAgent()

    def run_agent(
        self,
        user_input: str,
        user_role: str = "employee",
        thread_id: str | None = None,
    ) -> dict:

        start = time.perf_counter()

        try:

            response = self.agent.run(
                user_input=user_input,
                user_role=user_role,
                thread_id=thread_id,
            )

            AGENT_REQUESTS.labels(
                status="success"
            ).inc()

            return response

        except Exception:

            AGENT_REQUESTS.labels(
                status="failed"
            ).inc()

            raise

        finally:

            duration = (
                time.perf_counter()
                - start
            )

            AGENT_LATENCY.observe(
                duration
            )

    def resume_agent(
        self,
        thread_id: str,
        approved: bool,
    ) -> dict:

        decision = (
            "approved"
            if approved
            else "rejected"
        )

        AGENT_APPROVALS.labels(
            decision=decision
        ).inc()

        return self.agent.resume(
            thread_id=thread_id,
            approved=approved,
        )


agent_service = AgentService()