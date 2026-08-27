from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RiskEvent


def list_risk_events(
    db: Session,
    limit: int = 20,
    offset: int = 0,
    severity: str | None = None,
    event_type: str | None = None,
) -> list[RiskEvent]:

    statement = select(
        RiskEvent
    )

    if severity is not None:

        statement = statement.where(
            RiskEvent.severity
            == severity
        )

    if event_type is not None:

        statement = statement.where(
            RiskEvent.event_type
            == event_type
        )

    statement = (
        statement
        .order_by(
            RiskEvent.detected_at.desc()
        )
        .offset(offset)
        .limit(limit)
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


def get_risk_event(
    db: Session,
    risk_event_id: int,
) -> RiskEvent | None:

    return db.get(
        RiskEvent,
        risk_event_id,
    )