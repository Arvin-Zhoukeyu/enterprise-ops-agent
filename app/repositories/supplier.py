from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Supplier


def list_suppliers(
    db: Session,
    limit: int = 20,
    offset: int = 0,
    risk_level: str | None = None,
) -> list[Supplier]:

    statement = select(
        Supplier
    )

    if risk_level is not None:

        statement = statement.where(
            Supplier.risk_level
            == risk_level
        )

    statement = (
        statement
        .order_by(
            Supplier.id
        )
        .offset(offset)
        .limit(limit)
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


def get_supplier_by_code(
    db: Session,
    supplier_code: str,
) -> Supplier | None:

    statement = (
        select(Supplier)
        .where(
            Supplier.supplier_code
            == supplier_code
        )
    )

    return (
        db.execute(statement)
        .scalar_one_or_none()
    )