from pydantic import (
    BaseModel,
    Field,
)

from app.db.session import SessionLocal
from app.services.risk import (
    get_risk_events,
)
from app.tools.base import ToolDefinition
from app.tools.registry import (
    tool_registry,
)


class ListRiskEventsInput(BaseModel):

    severity: str | None = Field(
        default=None,
        description=(
            "Optional severity filter: "
            "low, medium, high, or critical."
        ),
    )

    event_type: str | None = Field(
        default=None,
        description=(
            "Optional risk event type, "
            "such as delivery_delay or "
            "payment_failure."
        ),
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )


def handle_list_risk_events(
    severity: str | None = None,
    event_type: str | None = None,
    limit: int = 20,
) -> list[dict]:

    db = SessionLocal()

    try:

        events = get_risk_events(
            db,
            limit=limit,
            offset=0,
            severity=severity,
            event_type=event_type,
        )

        return [
            {
                "id":
                    event.id,

                "supplier_id":
                    event.supplier_id,

                "purchase_order_id":
                    event.purchase_order_id,

                "event_type":
                    event.event_type,

                "severity":
                    event.severity,

                "risk_score":
                    event.risk_score,

                "description":
                    event.description,

                "status":
                    event.status,

                "detected_at":
                    event.detected_at
                    .isoformat(),
            }
            for event in events
        ]

    finally:

        db.close()


tool_registry.register(
    ToolDefinition(
        name="list_risk_events",

        description=(
            "Retrieve historical enterprise "
            "risk events, optionally filtered "
            "by severity or event type."
        ),

        input_model=(
            ListRiskEventsInput
        ),

        handler=(
            handle_list_risk_events
        ),

        permission="READ",

        side_effect=False,
    )
)