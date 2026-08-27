from sqlalchemy.orm import Session

from app.models import Ticket
from app.repositories.risk import (
    get_risk_event,
)
from app.repositories.ticket import (
    create_ticket,
    get_ticket_by_number,
)
from app.schemas.ticket import TicketCreate


class RiskEventNotFoundError(Exception):
    pass


class RiskEventClosedError(Exception):
    pass


def create_risk_ticket(
    db: Session,
    data: TicketCreate,
) -> Ticket:

    risk_event = get_risk_event(
        db,
        data.risk_event_id,
    )

    if risk_event is None:
        raise RiskEventNotFoundError

    if risk_event.status == "closed":
        raise RiskEventClosedError

    return create_ticket(
        db=db,
        risk_event_id=data.risk_event_id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        assigned_to=data.assigned_to,
    )


def get_ticket(
    db: Session,
    ticket_number: str,
) -> Ticket | None:

    return get_ticket_by_number(
        db,
        ticket_number,
    )