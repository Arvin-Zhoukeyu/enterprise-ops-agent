from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.supplier import (
    SupplierResponse,
)
from app.services.supplier import (
    get_supplier,
    get_suppliers,
)

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)


@router.get(
    "",
    response_model=list[
        SupplierResponse
    ],
)
def list_supplier_endpoint(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    risk_level: str | None = Query(
        default=None,
    ),
    db: Session = Depends(
        get_db
    ),
):

    return get_suppliers(
        db,
        limit=limit,
        offset=offset,
        risk_level=risk_level,
    )


@router.get(
    "/{supplier_code}",
    response_model=SupplierResponse,
)
def get_supplier_endpoint(
    supplier_code: str,
    db: Session = Depends(
        get_db
    ),
):

    supplier = get_supplier(
        db,
        supplier_code,
    )

    if supplier is None:

        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    return supplier