from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class TicketCreate(BaseModel):

    risk_event_id: int

    title: str = Field(
        min_length=3,
        max_length=255,
    )

    description: str = Field(
        min_length=5
    )

    priority: str = Field(
        pattern="^(low|medium|high|critical)$"
    )

    assigned_to: str | None = None


class TicketResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    ticket_number: str

    risk_event_id: int

    title: str

    description: str

    priority: str

    status: str

    assigned_to: str | None

    created_at: datetime