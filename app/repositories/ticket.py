from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ticket


def create_ticket(
    db: Session,
    *,
    risk_event_id: int,
    title: str,
    description: str,
    priority: str,
    assigned_to: str | None,
) -> Ticket:

    ticket = Ticket(
        ticket_number="PENDING",
        risk_event_id=risk_event_id,
        title=title,
        description=description,
        priority=priority,
        status="open",
        assigned_to=assigned_to,
        created_at=datetime.now(
            timezone.utc
        ),
    )

    db.add(ticket)

    db.flush()

    ticket.ticket_number = (
        f"TKT-2026-{ticket.id:06d}"
    )

    db.commit()

    db.refresh(ticket)

    return ticket


def get_ticket_by_number(
    db: Session,
    ticket_number: str,
) -> Ticket | None:

    statement = (
        select(Ticket)
        .where(
            Ticket.ticket_number
            == ticket_number
        )
    )

    return (
        db.execute(statement)
        .scalar_one_or_none()
    )