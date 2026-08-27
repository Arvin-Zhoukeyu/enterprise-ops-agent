from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Delivery,
    PurchaseOrder,
    Supplier,
)


def list_orders(
    db: Session,
    limit: int = 20,
    offset: int = 0,
    supplier_id: int | None = None,
) -> list[PurchaseOrder]:

    statement = select(
        PurchaseOrder
    )

    if supplier_id is not None:

        statement = statement.where(
            PurchaseOrder.supplier_id
            == supplier_id
        )

    statement = (
        statement
        .order_by(
            PurchaseOrder.order_date.desc()
        )
        .offset(offset)
        .limit(limit)
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


def get_order_by_number(
    db: Session,
    order_number: str,
) -> PurchaseOrder | None:

    statement = (
        select(PurchaseOrder)
        .where(
            PurchaseOrder.order_number
            == order_number
        )
    )

    return (
        db.execute(statement)
        .scalar_one_or_none()
    )


def find_high_risk_orders(
    db: Session,
    days: int = 90,
    min_amount: Decimal = Decimal("100000"),
    min_delay_days: int = 7,
    min_historical_delays: int = 2,
) -> list[dict]:

    cutoff_date = (
        date.today()
        - timedelta(days=days)
    )

    delay_history = (
        select(
            PurchaseOrder.supplier_id.label(
                "supplier_id"
            ),
            func.count(
                Delivery.id
            ).label(
                "delay_count"
            ),
        )
        .join(
            Delivery,
            Delivery.purchase_order_id
            == PurchaseOrder.id,
        )
        .where(
            Delivery.actual_date.is_not(None)
        )
        .where(
            (
                Delivery.actual_date
                - Delivery.expected_date
            ) >= min_delay_days
        )
        .group_by(
            PurchaseOrder.supplier_id
        )
        .subquery()
    )

    statement = (
        select(
            PurchaseOrder.order_number,
            PurchaseOrder.total_amount,
            PurchaseOrder.currency,
            PurchaseOrder.order_date,
            Supplier.supplier_code,
            Supplier.name.label(
                "supplier_name"
            ),
            Supplier.risk_level,
            (
                Delivery.actual_date
                - Delivery.expected_date
            ).label(
                "delay_days"
            ),
            delay_history.c.delay_count,
        )
        .join(
            Supplier,
            Supplier.id
            == PurchaseOrder.supplier_id,
        )
        .join(
            Delivery,
            Delivery.purchase_order_id
            == PurchaseOrder.id,
        )
        .join(
            delay_history,
            delay_history.c.supplier_id
            == Supplier.id,
        )
        .where(
            PurchaseOrder.order_date
            >= cutoff_date
        )
        .where(
            PurchaseOrder.total_amount
            >= min_amount
        )
        .where(
            Delivery.actual_date.is_not(None)
        )
        .where(
            (
                Delivery.actual_date
                - Delivery.expected_date
            ) >= min_delay_days
        )
        .where(
            delay_history.c.delay_count
            >= min_historical_delays
        )
        .order_by(
            PurchaseOrder.total_amount.desc()
        )
    )

    rows = db.execute(
        statement
    ).all()

    results = []

    for row in rows:

        results.append(
            {
                "order_number":
                    row.order_number,

                "supplier_code":
                    row.supplier_code,

                "supplier_name":
                    row.supplier_name,

                "total_amount":
                    row.total_amount,

                "currency":
                    row.currency,

                "order_date":
                    row.order_date,

                "delay_days":
                    row.delay_days,

                "historical_delay_count":
                    row.delay_count,

                "existing_risk_level":
                    row.risk_level,
            }
        )

    return results