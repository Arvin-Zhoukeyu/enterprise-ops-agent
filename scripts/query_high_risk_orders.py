from datetime import date, timedelta

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import (
    Delivery,
    PurchaseOrder,
    Supplier,
)


def main():

    session = SessionLocal()

    try:

        cutoff_date = (
            date.today()
            - timedelta(days=90)
        )

        # ----------------------------------
        # Step 1:
        # Calculate historical delayed order
        # count for each supplier.
        # ----------------------------------

        delay_history = (
            select(
                PurchaseOrder.supplier_id.label(
                    "supplier_id"
                ),
                func.count(
                    Delivery.id
                ).label(
                    "delay_count"
                ),
            )
            .join(
                Delivery,
                Delivery.purchase_order_id
                == PurchaseOrder.id,
            )
            .where(
                Delivery.actual_date.is_not(None)
            )
            .where(
                (
                    Delivery.actual_date
                    - Delivery.expected_date
                ) >= 7
            )
            .group_by(
                PurchaseOrder.supplier_id
            )
            .subquery()
        )

        # ----------------------------------
        # Step 2:
        # Query high-risk candidate orders.
        # ----------------------------------

        statement = (
            select(
                PurchaseOrder.order_number,

                PurchaseOrder.total_amount,

                PurchaseOrder.order_date,

                Supplier.supplier_code,

                Supplier.name.label(
                    "supplier_name"
                ),

                Supplier.risk_level,

                (
                    Delivery.actual_date
                    - Delivery.expected_date
                ).label(
                    "delay_days"
                ),

                delay_history.c.delay_count,
            )
            .join(
                Supplier,
                Supplier.id
                == PurchaseOrder.supplier_id,
            )
            .join(
                Delivery,
                Delivery.purchase_order_id
                == PurchaseOrder.id,
            )
            .join(
                delay_history,
                delay_history.c.supplier_id
                == Supplier.id,
            )
            .where(
                PurchaseOrder.order_date
                >= cutoff_date
            )
            .where(
                PurchaseOrder.total_amount
                > 100000
            )
            .where(
                Delivery.actual_date.is_not(None)
            )
            .where(
                (
                    Delivery.actual_date
                    - Delivery.expected_date
                ) >= 7
            )
            .where(
                delay_history.c.delay_count
                >= 2
            )
            .order_by(
                PurchaseOrder.total_amount.desc()
            )
        )

        rows = session.execute(
            statement
        ).all()

        print(
            "\n=== High Risk Purchase Orders ==="
        )

        print(
            f"Candidates found: {len(rows)}\n"
        )

        for row in rows[:20]:

            print(
                f"Order: "
                f"{row.order_number}"
            )

            print(
                f"Supplier: "
                f"{row.supplier_code} - "
                f"{row.supplier_name}"
            )

            print(
                f"Existing Risk Level: "
                f"{row.risk_level}"
            )

            print(
                f"Amount: "
                f"{row.total_amount} CNY"
            )

            print(
                f"Order Date: "
                f"{row.order_date}"
            )

            print(
                f"Current Delay: "
                f"{row.delay_days} days"
            )

            print(
                f"Supplier Historical "
                f"Delays: {row.delay_count}"
            )

            print(
                "-" * 60
            )

    finally:

        session.close()


if __name__ == "__main__":
    main()