from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import PurchaseOrder
from app.repositories.order import (
    find_high_risk_orders,
    get_order_by_number,
    list_orders,
)


def get_orders(
    db: Session,
    *,
    limit: int,
    offset: int,
    supplier_id: int | None,
) -> list[PurchaseOrder]:

    return list_orders(
        db=db,
        limit=limit,
        offset=offset,
        supplier_id=supplier_id,
    )


def get_order(
    db: Session,
    order_number: str,
) -> PurchaseOrder | None:

    return get_order_by_number(
        db,
        order_number,
    )


def get_high_risk_orders(
    db: Session,
    *,
    days: int,
    min_amount: Decimal,
    min_delay_days: int,
    min_historical_delays: int,
) -> list[dict]:

    return find_high_risk_orders(
        db=db,
        days=days,
        min_amount=min_amount,
        min_delay_days=min_delay_days,
        min_historical_delays=(
            min_historical_delays
        ),
    )