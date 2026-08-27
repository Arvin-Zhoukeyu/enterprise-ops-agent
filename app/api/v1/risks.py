from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.risk import (
    RiskEventResponse,
)
from app.services.risk import (
    get_risk_events,
)

router = APIRouter(
    prefix="/risk-events",
    tags=["Risk Events"],
)


@router.get(
    "",
    response_model=list[
        RiskEventResponse
    ],
)
def list_risk_events_endpoint(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    severity: str | None = None,
    event_type: str | None = None,
    db: Session = Depends(
        get_db
    ),
):

    return get_risk_events(
        db,
        limit=limit,
        offset=offset,
        severity=severity,
        event_type=event_type,
    )