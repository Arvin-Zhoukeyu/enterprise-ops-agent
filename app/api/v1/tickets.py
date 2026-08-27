from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
)
from app.services.ticket import (
    RiskEventClosedError,
    RiskEventNotFoundError,
    create_risk_ticket,
    get_ticket,
)

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_endpoint(
    payload: TicketCreate,
    db: Session = Depends(
        get_db
    ),
):

    try:

        return create_risk_ticket(
            db,
            payload,
        )

    except RiskEventNotFoundError:

        raise HTTPException(
            status_code=404,
            detail="Risk event not found",
        )

    except RiskEventClosedError:

        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot create ticket for "
                "closed risk event"
            ),
        )


@router.get(
    "/{ticket_number}",
    response_model=TicketResponse,
)
def get_ticket_endpoint(
    ticket_number: str,
    db: Session = Depends(
        get_db
    ),
):

    ticket = get_ticket(
        db,
        ticket_number,
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return ticket