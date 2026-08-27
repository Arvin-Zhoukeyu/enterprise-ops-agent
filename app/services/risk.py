from sqlalchemy.orm import Session

from app.models import RiskEvent
from app.repositories.risk import (
    get_risk_event,
    list_risk_events,
)


def get_risk_events(
    db: Session,
    *,
    limit: int,
    offset: int,
    severity: str | None,
    event_type: str | None,
) -> list[RiskEvent]:

    return list_risk_events(
        db=db,
        limit=limit,
        offset=offset,
        severity=severity,
        event_type=event_type,
    )


def get_risk(
    db: Session,
    risk_event_id: int,
) -> RiskEvent | None:

    return get_risk_event(
        db,
        risk_event_id,
    )