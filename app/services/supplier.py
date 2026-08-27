from sqlalchemy.orm import Session

from app.models import Supplier
from app.repositories.supplier import (
    get_supplier_by_code,
    list_suppliers,
)


def get_suppliers(
    db: Session,
    *,
    limit: int,
    offset: int,
    risk_level: str | None,
) -> list[Supplier]:

    return list_suppliers(
        db=db,
        limit=limit,
        offset=offset,
        risk_level=risk_level,
    )


def get_supplier(
    db: Session,
    supplier_code: str,
) -> Supplier | None:

    return get_supplier_by_code(
        db,
        supplier_code,
    )