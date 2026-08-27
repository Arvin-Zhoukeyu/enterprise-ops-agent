from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import (
    Delivery,
    Payment,
    PurchaseOrder,
    Supplier,
)


def test_database_contains_suppliers():

    session = SessionLocal()

    try:

        count = session.scalar(
            select(
                func.count(Supplier.id)
            )
        )

        assert count > 0

    finally:

        session.close()


def test_database_contains_orders():

    session = SessionLocal()

    try:

        count = session.scalar(
            select(
                func.count(
                    PurchaseOrder.id
                )
            )
        )

        assert count > 0

    finally:

        session.close()


def test_every_order_has_supplier():

    session = SessionLocal()

    try:

        orders_without_supplier = (
            session.scalar(
                select(
                    func.count(
                        PurchaseOrder.id
                    )
                )
                .where(
                    PurchaseOrder.supplier_id
                    .is_(None)
                )
            )
        )

        assert (
            orders_without_supplier
            == 0
        )

    finally:

        session.close()


def test_delivery_dates_are_valid():

    session = SessionLocal()

    try:

        statement = (
            select(
                PurchaseOrder.order_date,
                PurchaseOrder
                .expected_delivery_date,
                Delivery.actual_date,
            )
            .join(
                Delivery,
                Delivery.purchase_order_id
                == PurchaseOrder.id,
            )
        )

        rows = session.execute(
            statement
        ).all()

        for row in rows:

            assert (
                row.expected_delivery_date
                >= row.order_date
            )

            if row.actual_date is not None:

                assert (
                    row.actual_date
                    >= row.order_date
                )

    finally:

        session.close()


def test_large_orders_exist():

    session = SessionLocal()

    try:

        count = session.scalar(
            select(
                func.count(
                    PurchaseOrder.id
                )
            )
            .where(
                PurchaseOrder.total_amount
                > 100000
            )
        )

        assert count > 0

    finally:

        session.close()


def test_delayed_deliveries_exist():

    session = SessionLocal()

    try:

        deliveries = (
            session.execute(
                select(Delivery)
                .where(
                    Delivery.actual_date
                    .is_not(None)
                )
            )
            .scalars()
            .all()
        )

        delayed_count = 0

        for delivery in deliveries:

            delay_days = (
                delivery.actual_date
                - delivery.expected_date
            ).days

            if delay_days >= 7:
                delayed_count += 1

        assert delayed_count > 0

    finally:

        session.close()


def test_payment_failures_exist():

    session = SessionLocal()

    try:

        failure_count = session.scalar(
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

        assert failure_count > 0

    finally:

        session.close()
def test_high_risk_suppliers_have_higher_delay_rate():

    session = SessionLocal()

    try:

        high_risk_deliveries = (
            session.execute(
                select(Delivery)
                .join(
                    PurchaseOrder,
                    PurchaseOrder.id
                    == Delivery.purchase_order_id,
                )
                .join(
                    Supplier,
                    Supplier.id
                    == PurchaseOrder.supplier_id,
                )
                .where(
                    Supplier.risk_level
                    == "high"
                )
            )
            .scalars()
            .all()
        )

        low_risk_deliveries = (
            session.execute(
                select(Delivery)
                .join(
                    PurchaseOrder,
                    PurchaseOrder.id
                    == Delivery.purchase_order_id,
                )
                .join(
                    Supplier,
                    Supplier.id
                    == PurchaseOrder.supplier_id,
                )
                .where(
                    Supplier.risk_level
                    == "low"
                )
            )
            .scalars()
            .all()
        )

        high_delay_count = sum(
            1
            for delivery
            in high_risk_deliveries
            if delivery.status
            == "delayed"
        )

        low_delay_count = sum(
            1
            for delivery
            in low_risk_deliveries
            if delivery.status
            == "delayed"
        )

        high_delay_rate = (
            high_delay_count
            / len(
                high_risk_deliveries
            )
        )

        low_delay_rate = (
            low_delay_count
            / len(
                low_risk_deliveries
            )
        )

        assert (
            high_delay_rate
            > low_delay_rate
        )

    finally:

        session.close()