from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RiskEventResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    supplier_id: int | None

    purchase_order_id: int | None

    event_type: str

    severity: str

    risk_score: float

    description: str

    status: str

    detected_at: datetime