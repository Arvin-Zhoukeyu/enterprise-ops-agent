from app.services.agent_service import (
    agent_service,
)


def execute_agent_task(
    message: str,
    role: str,
):

    return agent_service.run_agent(
        user_input=message,
        user_role=role,
    )