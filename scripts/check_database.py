from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import (
    Delivery,
    Payment,
    PurchaseOrder,
    RiskEvent,
    Supplier,
)


def main():

    session = SessionLocal()

    try:

        print(
            "\n=== Database Overview ==="
        )

        supplier_count = session.scalar(
            select(
                func.count(
                    Supplier.id
                )
            )
        )

        order_count = session.scalar(
            select(
                func.count(
                    PurchaseOrder.id
                )
            )
        )

        print(
            f"Suppliers: {supplier_count}"
        )

        print(
            f"Orders: {order_count}"
        )

        print(
            "\n=== High Risk Suppliers ==="
        )

        high_risk_suppliers = (
            session.execute(
                select(Supplier)
                .where(
                    Supplier.risk_level
                    == "high"
                )
                .limit(10)
            )
            .scalars()
            .all()
        )

        for supplier in high_risk_suppliers:

            print(
                supplier.supplier_code,
                supplier.name,
                supplier.rating,
            )

        print(
            "\n=== Large Orders ==="
        )

        large_orders = (
            session.execute(
                select(PurchaseOrder)
                .where(
                    PurchaseOrder.total_amount
                    > 100000
                )
                .order_by(
                    PurchaseOrder.total_amount
                    .desc()
                )
                .limit(10)
            )
            .scalars()
            .all()
        )

        for order in large_orders:

            print(
                order.order_number,
                order.total_amount,
                order.order_date,
            )

        print(
            "\n=== Delayed Deliveries ==="
        )

        delayed_count = session.scalar(
            select(
                func.count(
                    Delivery.id
                )
            )
            .where(
                Delivery.status
                == "delayed"
            )
        )

        print(
            f"Delayed deliveries: "
            f"{delayed_count}"
        )

        print(
            "\n=== Payment Failures ==="
        )

        payment_failure_count = (
            session.scalar(
                select(
                    func.count(
                        Payment.id
                    )
                )
                .where(
                    Payment.status
                    == "failed"
                )
            )
        )

        print(
            f"Payment failures: "
            f"{payment_failure_count}"
        )

        print(
            "\n=== Risk Events ==="
        )

        risk_count = session.scalar(
            select(
                func.count(
                    RiskEvent.id
                )
            )
        )

        print(
            f"Risk events: "
            f"{risk_count}"
        )

    finally:

        session.close()


if __name__ == "__main__":
    main()