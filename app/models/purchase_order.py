from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=False,
        index=True,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="CNY",
    )

    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    expected_delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    supplier = relationship(
        "Supplier",
        back_populates="purchase_orders",
    )

    items = relationship(
        "OrderItem",
        back_populates="purchase_order",
    )

    deliveries = relationship(
        "Delivery",
        back_populates="purchase_order",
    )

    payments = relationship(
        "Payment",
        back_populates="purchase_order",
    )

    risk_events = relationship(
        "RiskEvent",
        back_populates="purchase_order",
    )