from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Delivery, PurchaseOrder, Supplier
from app.services.risk_rules import screen_orders, six_months_before


def list_orders(db: Session, limit=20, offset=0, supplier_id=None):
    statement = select(PurchaseOrder)
    if supplier_id is not None:
        statement = statement.where(PurchaseOrder.supplier_id == supplier_id)
    return db.execute(statement.order_by(PurchaseOrder.order_date.desc())
                      .offset(offset).limit(limit)).scalars().all()


def get_order_by_number(db: Session, order_number: str):
    return db.execute(select(PurchaseOrder).where(
        PurchaseOrder.order_number == order_number
    )).scalar_one_or_none()


def find_high_risk_orders(db: Session, days=90, min_amount=Decimal("100000"),
                         min_delay_days=7, min_historical_delays=2, *, as_of=None):
    as_of = as_of or date.today()
    # Load the candidate period plus the prior six months needed as evidence.
    statement = select(
        PurchaseOrder.order_number, PurchaseOrder.total_amount,
        PurchaseOrder.currency, PurchaseOrder.order_date,
        Supplier.supplier_code, Supplier.name.label("supplier_name"),
        Supplier.risk_level.label("existing_risk_level"),
        Delivery.expected_date, Delivery.actual_date,
    ).join(Supplier, Supplier.id == PurchaseOrder.supplier_id).join(
        Delivery, Delivery.purchase_order_id == PurchaseOrder.id
    ).where(
        Delivery.actual_date <= as_of,
        Delivery.actual_date >= six_months_before(as_of - timedelta(days=days)),
    )
    return screen_orders(db.execute(statement).mappings().all(), as_of=as_of,
                         days=days, min_amount=min_amount,
                         min_delay_days=min_delay_days,
                         min_historical_delays=min_historical_delays)
