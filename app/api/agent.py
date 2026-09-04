from fastapi import APIRouter, HTTPException

from app.schemas.agent import (
    AgentRequest,
    ApprovalRequest,
)
from app.services.agent_service import (
    agent_service,
)
from rq.job import Job

from app.schemas.agent import (
    AgentRequest,
    ApprovalRequest,
    AsyncAgentRequest,
)
from app.workers.queue import (
    agent_queue,
    redis_connection,
)
from app.workers.tasks import (
    execute_agent_task,
)

router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


@router.post("/run")
def run_agent(
    request: AgentRequest,
):

    try:

        result = (
            agent_service.run_agent(
                user_input=request.message,
                user_role=request.role,
                thread_id=request.thread_id,
            )
        )

        return {
            "success": True,
            "data": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post(
    "/{thread_id}/approval"
)
def approve_agent_action(
    thread_id: str,
    request: ApprovalRequest,
):

    try:

        result = (
            agent_service.resume_agent(
                thread_id=thread_id,
                approved=request.approved,
            )
        )

        return {
            "success": True,
            "data": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.post("/async")
def run_agent_async(
    request: AsyncAgentRequest,
):

    job = agent_queue.enqueue(
        execute_agent_task,
        request.message,
        request.role,
        job_timeout=300,
    )

    return {
        "success": True,
        "task_id": job.id,
        "status": job.get_status(),
    }

@router.get(
    "/tasks/{task_id}"
)
def get_task_status(
    task_id: str,
):

    try:

        job = Job.fetch(
            task_id,
            connection=redis_connection,
        )

    except Exception:

        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    response = {
        "task_id":
            job.id,

        "status":
            job.get_status(),

        "result":
            None,
    }

    if job.is_finished:

        response["result"] = (
            job.result
        )

    if job.is_failed:

        response["error"] = (
            job.exc_info
        )

    return response