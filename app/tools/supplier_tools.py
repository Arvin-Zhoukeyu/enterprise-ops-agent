from pydantic import (
    BaseModel,
    Field,
)

from app.db.session import SessionLocal
from app.services.supplier import (
    get_supplier,
    get_suppliers,
)
from app.tools.base import ToolDefinition
from app.tools.registry import (
    tool_registry,
)


class GetSupplierInput(BaseModel):

    supplier_code: str = Field(
        description=(
            "Business supplier code, "
            "for example SUP-2026-0003."
        )
    )


class ListSuppliersInput(BaseModel):

    risk_level: str | None = Field(
        default=None,
        description=(
            "Optional supplier risk level: "
            "low, medium, or high."
        ),
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )


def handle_get_supplier(
    supplier_code: str,
) -> dict:

    db = SessionLocal()

    try:

        supplier = get_supplier(
            db,
            supplier_code,
        )

        if supplier is None:

            return {
                "found": False,
                "supplier_code":
                    supplier_code,
            }

        return {
            "found": True,

            "supplier_code":
                supplier.supplier_code,

            "name":
                supplier.name,

            "country":
                supplier.country,

            "category":
                supplier.category,

            "rating":
                supplier.rating,

            "risk_level":
                supplier.risk_level,

            "cooperation_years":
                supplier.cooperation_years,

            "status":
                supplier.status,
        }

    finally:

        db.close()


def handle_list_suppliers(
    risk_level: str | None = None,
    limit: int = 20,
) -> list[dict]:

    db = SessionLocal()

    try:

        suppliers = get_suppliers(
            db,
            limit=limit,
            offset=0,
            risk_level=risk_level,
        )

        return [
            {
                "supplier_code":
                    supplier.supplier_code,

                "name":
                    supplier.name,

                "rating":
                    supplier.rating,

                "risk_level":
                    supplier.risk_level,

                "country":
                    supplier.country,
            }
            for supplier in suppliers
        ]

    finally:

        db.close()


tool_registry.register(
    ToolDefinition(
        name="get_supplier",

        description=(
            "Get detailed information for "
            "one supplier using its supplier "
            "business code."
        ),

        input_model=GetSupplierInput,

        handler=handle_get_supplier,

        permission="READ",

        side_effect=False,
    )
)


tool_registry.register(
    ToolDefinition(
        name="list_suppliers",

        description=(
            "List suppliers, optionally "
            "filtered by risk level."
        ),

        input_model=ListSuppliersInput,

        handler=handle_list_suppliers,

        permission="READ",

        side_effect=False,
    )
)