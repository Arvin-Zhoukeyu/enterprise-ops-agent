from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SupplierResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    supplier_code: str

    name: str

    country: str

    category: str

    rating: float

    risk_level: str

    cooperation_years: int

    status: str

    created_at: datetime