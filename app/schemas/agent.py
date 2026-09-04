from pydantic import BaseModel, Field


class AgentRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=5000,
    )

    role: str = "employee"

    thread_id: str | None = None


class ApprovalRequest(BaseModel):

    approved: bool


class AsyncAgentRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=5000,
    )

    role: str = "employee"