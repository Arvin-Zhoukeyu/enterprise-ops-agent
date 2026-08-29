from decimal import Decimal

from pydantic import (
    BaseModel,
    Field,
)

from app.db.session import SessionLocal
from app.services.order import (
    get_high_risk_orders,
    get_order,
)
from app.tools.base import ToolDefinition
from app.tools.registry import (
    tool_registry,
)


class GetOrderInput(BaseModel):

    order_number: str = Field(
        description=(
            "Purchase order business number, "
            "for example PO-2026-000123."
        )
    )


class FindHighRiskOrdersInput(
    BaseModel
):

    days: int = Field(
        default=90,
        ge=1,
        le=3650,
        description=(
            "How many recent days of orders "
            "should be searched."
        ),
    )

    min_amount: Decimal = Field(
        default=Decimal("100000"),
        ge=0,
        description=(
            "Minimum purchase amount in CNY."
        ),
    )

    min_delay_days: int = Field(
        default=7,
        ge=0,
        description=(
            "Minimum current delivery delay "
            "in days."
        ),
    )

    min_historical_delays: int = Field(
        default=2,
        ge=0,
        description=(
            "Minimum number of historical "
            "serious delays for the supplier."
        ),
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description=(
            "Maximum number of results "
            "returned to the agent."
        ),
    )


def handle_get_order(
    order_number: str,
) -> dict:

    db = SessionLocal()

    try:

        order = get_order(
            db,
            order_number,
        )

        if order is None:

            return {
                "found": False,
                "order_number":
                    order_number,
            }

        return {
            "found": True,

            "order_number":
                order.order_number,

            "supplier_id":
                order.supplier_id,

            "total_amount":
                str(order.total_amount),

            "currency":
                order.currency,

            "order_date":
                order.order_date.isoformat(),

            "expected_delivery_date":
                order.expected_delivery_date
                .isoformat(),

            "status":
                order.status,
        }

    finally:

        db.close()


def handle_find_high_risk_orders(
    days: int = 90,
    min_amount: Decimal = (
        Decimal("100000")
    ),
    min_delay_days: int = 7,
    min_historical_delays: int = 2,
    limit: int = 20,
) -> list[dict]:

    db = SessionLocal()

    try:

        rows = get_high_risk_orders(
            db,
            days=days,
            min_amount=min_amount,
            min_delay_days=(
                min_delay_days
            ),
            min_historical_delays=(
                min_historical_delays
            ),
        )

        rows = rows[:limit]

        results = []

        for row in rows:

            results.append(
                {
                    "order_number":
                        row[
                            "order_number"
                        ],

                    "supplier_code":
                        row[
                            "supplier_code"
                        ],

                    "supplier_name":
                        row[
                            "supplier_name"
                        ],

                    "total_amount":
                        str(
                            row[
                                "total_amount"
                            ]
                        ),

                    "currency":
                        row["currency"],

                    "order_date":
                        row[
                            "order_date"
                        ].isoformat(),

                    "delay_days":
                        row[
                            "delay_days"
                        ],

                    "historical_delay_count":
                        row[
                            "historical_delay_count"
                        ],

                    "existing_risk_level":
                        row[
                            "existing_risk_level"
                        ],
                }
            )

        return results

    finally:

        db.close()


tool_registry.register(
    ToolDefinition(
        name="get_purchase_order",

        description=(
            "Get details for one purchase "
            "order by order number."
        ),

        input_model=GetOrderInput,

        handler=handle_get_order,

        permission="READ",

        side_effect=False,
    )
)


tool_registry.register(
    ToolDefinition(
        name="find_high_risk_orders",

        description=(
            "Find recent purchase orders "
            "matching risk conditions such as "
            "large amount, significant delivery "
            "delay, and repeated historical "
            "supplier delays."
        ),

        input_model=(
            FindHighRiskOrdersInput
        ),

        handler=(
            handle_find_high_risk_orders
        ),

        permission="READ",

        side_effect=False,
    )
)