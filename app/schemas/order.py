from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrderResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    order_number: str

    supplier_id: int

    total_amount: Decimal

    currency: str

    order_date: date

    expected_delivery_date: date

    status: str


class HighRiskOrderResponse(BaseModel):

    order_number: str

    supplier_code: str

    supplier_name: str

    total_amount: Decimal

    currency: str

    order_date: date

    delay_days: int

    historical_delay_count: int

    existing_risk_level: str