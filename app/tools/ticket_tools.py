from pydantic import (
    BaseModel,
    Field,
)

from app.db.session import SessionLocal
from app.schemas.ticket import (
    TicketCreate,
)
from app.services.ticket import (
    RiskEventClosedError,
    RiskEventNotFoundError,
    create_risk_ticket,
)
from app.tools.base import ToolDefinition
from app.tools.registry import (
    tool_registry,
)


class CreateTicketInput(BaseModel):

    risk_event_id: int = Field(
        ge=1
    )

    title: str = Field(
        min_length=3,
        max_length=255,
    )

    description: str = Field(
        min_length=5,
    )

    priority: str = Field(
        pattern=(
            "^(low|medium|high|critical)$"
        )
    )

    assigned_to: str | None = None


def handle_create_ticket(
    risk_event_id: int,
    title: str,
    description: str,
    priority: str,
    assigned_to: str | None = None,
) -> dict:

    db = SessionLocal()

    try:

        payload = TicketCreate(
            risk_event_id=risk_event_id,
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
        )

        ticket = create_risk_ticket(
            db,
            payload,
        )

        return {
            "success": True,

            "ticket_number":
                ticket.ticket_number,

            "status":
                ticket.status,

            "priority":
                ticket.priority,
        }

    except RiskEventNotFoundError:

        return {
            "success": False,
            "error":
                "risk_event_not_found",
        }

    except RiskEventClosedError:

        return {
            "success": False,
            "error":
                "risk_event_closed",
        }

    finally:

        db.close()


tool_registry.register(
    ToolDefinition(
        name="create_risk_ticket",

        description=(
            "Create an operational investigation "
            "ticket for an existing risk event. "
            "This changes business system state."
        ),

        input_model=CreateTicketInput,

        handler=handle_create_ticket,

        permission="WRITE",

        side_effect=True,
    )
)