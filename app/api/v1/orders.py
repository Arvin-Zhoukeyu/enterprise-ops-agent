from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.order import (
    HighRiskOrderResponse,
    OrderResponse,
)
from app.services.order import (
    get_high_risk_orders,
    get_order,
    get_orders,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.get(
    "",
    response_model=list[
        OrderResponse
    ],
)
def list_orders_endpoint(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    supplier_id: int | None = Query(
        default=None,
        ge=1,
    ),
    db: Session = Depends(
        get_db
    ),
):

    return get_orders(
        db,
        limit=limit,
        offset=offset,
        supplier_id=supplier_id,
    )


@router.get(
    "/high-risk",
    response_model=list[
        HighRiskOrderResponse
    ],
)
def high_risk_orders_endpoint(
    days: int = Query(
        default=90,
        ge=1,
        le=3650,
    ),
    min_amount: Decimal = Query(
        default=Decimal("100000"),
        ge=0,
    ),
    min_delay_days: int = Query(
        default=7,
        ge=0,
    ),
    min_historical_delays: int = Query(
        default=2,
        ge=0,
    ),
    db: Session = Depends(
        get_db
    ),
):

    return get_high_risk_orders(
        db,
        days=days,
        min_amount=min_amount,
        min_delay_days=min_delay_days,
        min_historical_delays=(
            min_historical_delays
        ),
    )


@router.get(
    "/{order_number}",
    response_model=OrderResponse,
)
def get_order_endpoint(
    order_number: str,
    db: Session = Depends(
        get_db
    ),
):

    order = get_order(
        db,
        order_number,
    )

    if order is None:

        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order