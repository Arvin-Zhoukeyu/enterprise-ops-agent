from sqlalchemy import case, func, select

from app.db.session import SessionLocal
from app.models import (
    Delivery,
    Payment,
    PurchaseOrder,
    RiskEvent,
    Supplier,
)


def check_basic_counts(session):
    """
    Check whether core business tables contain data.
    """

    print("\n[1] Checking basic table counts...")

    supplier_count = session.scalar(
        select(func.count(Supplier.id))
    )

    order_count = session.scalar(
        select(func.count(PurchaseOrder.id))
    )

    delivery_count = session.scalar(
        select(func.count(Delivery.id))
    )

    payment_count = session.scalar(
        select(func.count(Payment.id))
    )

    risk_event_count = session.scalar(
        select(func.count(RiskEvent.id))
    )

    print(f"Suppliers:   {supplier_count}")
    print(f"Orders:      {order_count}")
    print(f"Deliveries:  {delivery_count}")
    print(f"Payments:    {payment_count}")
    print(f"Risk Events: {risk_event_count}")

    valid = (
        supplier_count > 0
        and order_count > 0
        and delivery_count > 0
        and payment_count > 0
    )

    return valid


def check_delivery_date_logic(session):
    """
    Validate delivery-related date rules.

    Rules:
    1. expected delivery date cannot be before order date
    2. actual delivery date cannot be before order date
    """

    print("\n[2] Checking delivery date logic...")

    statement = (
        select(
            PurchaseOrder.order_number,
            PurchaseOrder.order_date,
            PurchaseOrder.expected_delivery_date,
            Delivery.actual_date,
        )
        .join(
            Delivery,
            Delivery.purchase_order_id
            == PurchaseOrder.id,
        )
    )

    rows = session.execute(statement).all()

    invalid_orders = []

    for row in rows:

        if (
            row.expected_delivery_date
            < row.order_date
        ):
            invalid_orders.append(
                row.order_number
            )

        if (
            row.actual_date is not None
            and row.actual_date
            < row.order_date
        ):
            invalid_orders.append(
                row.order_number
            )

    print(
        f"Invalid delivery records: "
        f"{len(invalid_orders)}"
    )

    return invalid_orders


def check_large_orders_exist(session):
    """
    Make sure synthetic data contains large-value orders.

    These will later be used by the Agent for
    anomaly/risk analysis.
    """

    print("\n[3] Checking large purchase orders...")

    large_order_count = session.scalar(
        select(
            func.count(PurchaseOrder.id)
        )
        .where(
            PurchaseOrder.total_amount
            > 100000
        )
    )

    print(
        f"Orders above 100000 CNY: "
        f"{large_order_count}"
    )

    return large_order_count


def check_delayed_orders_exist(session):
    """
    Check whether meaningful delivery delays exist.
    """

    print("\n[4] Checking delayed deliveries...")

    statement = (
        select(
            Delivery.expected_date,
            Delivery.actual_date,
        )
        .where(
            Delivery.actual_date.is_not(None)
        )
    )

    rows = session.execute(statement).all()

    delayed_over_7_days = 0

    for row in rows:

        delay_days = (
            row.actual_date
            - row.expected_date
        ).days

        if delay_days >= 7:
            delayed_over_7_days += 1

    print(
        f"Deliveries delayed >= 7 days: "
        f"{delayed_over_7_days}"
    )

    return delayed_over_7_days


def check_payment_failures_exist(session):
    """
    Make sure payment failure cases exist.
    """

    print("\n[5] Checking payment failures...")

    failure_count = session.scalar(
        select(
            func.count(Payment.id)
        )
        .where(
            Payment.status == "failed"
        )
    )

    print(
        f"Failed payments: "
        f"{failure_count}"
    )

    return failure_count


def check_payment_risk_events(session):
    """
    Compare failed payments with payment failure
    risk events.

    We do not require exact equality here because
    future business rules may create additional
    risk events.
    """

    print(
        "\n[6] Checking payment risk events..."
    )

    failed_payment_count = session.scalar(
        select(
            func.count(Payment.id)
        )
        .where(
            Payment.status == "failed"
        )
    )

    payment_risk_count = session.scalar(
        select(
            func.count(RiskEvent.id)
        )
        .where(
            RiskEvent.event_type
            == "payment_failure"
        )
    )

    print(
        f"Failed payments: "
        f"{failed_payment_count}"
    )

    print(
        f"Payment risk events: "
        f"{payment_risk_count}"
    )

    return (
        failed_payment_count,
        payment_risk_count,
    )


def compare_supplier_delay_rates(session):
    """
    Check whether high-risk suppliers actually
    show worse delivery performance.

    This validates that the synthetic dataset
    contains an observable business pattern.
    """

    print(
        "\n[7] Comparing supplier delay rates..."
    )

    statement = (
        select(
            Supplier.risk_level,
            func.count(
                Delivery.id
            ).label(
                "total_deliveries"
            ),
            func.sum(
                case(
                    (
                        Delivery.status
                        == "delayed",
                        1,
                    ),
                    else_=0,
                )
            ).label(
                "delayed_deliveries"
            ),
        )
        .join(
            PurchaseOrder,
            PurchaseOrder.supplier_id
            == Supplier.id,
        )
        .join(
            Delivery,
            Delivery.purchase_order_id
            == PurchaseOrder.id,
        )
        .group_by(
            Supplier.risk_level
        )
    )

    rows = session.execute(statement).all()

    delay_rates = {}

    for row in rows:

        total = row.total_deliveries

        delayed = (
            row.delayed_deliveries
            or 0
        )

        delay_rate = (
            delayed / total
            if total
            else 0
        )

        delay_rates[
            row.risk_level
        ] = delay_rate

        print(
            f"{row.risk_level:>6} | "
            f"deliveries={total:4} | "
            f"delayed={delayed:4} | "
            f"delay_rate={delay_rate:.2%}"
        )

    return delay_rates


def main():

    session = SessionLocal()

    try:

        basic_data_valid = (
            check_basic_counts(session)
        )

        delivery_errors = (
            check_delivery_date_logic(
                session
            )
        )

        large_orders = (
            check_large_orders_exist(
                session
            )
        )

        delayed_orders = (
            check_delayed_orders_exist(
                session
            )
        )

        payment_failures = (
            check_payment_failures_exist(
                session
            )
        )

        (
            failed_payment_count,
            payment_risk_count,
        ) = check_payment_risk_events(
            session
        )

        delay_rates = (
            compare_supplier_delay_rates(
                session
            )
        )

        print(
            "\n=============================="
        )

        print(
            "Business Validation Summary"
        )

        print(
            "=============================="
        )

        if basic_data_valid:
            print(
                "PASS: Core tables contain data."
            )
        else:
            print(
                "FAIL: Missing core business data."
            )

        if len(delivery_errors) == 0:
            print(
                "PASS: Delivery dates are valid."
            )
        else:
            print(
                "FAIL: Invalid delivery dates found."
            )

        if large_orders > 0:
            print(
                "PASS: Large-order scenarios exist."
            )
        else:
            print(
                "WARNING: No large orders found."
            )

        if delayed_orders > 0:
            print(
                "PASS: Delayed-order scenarios exist."
            )
        else:
            print(
                "WARNING: No delayed orders found."
            )

        if payment_failures > 0:
            print(
                "PASS: Payment-failure scenarios exist."
            )
        else:
            print(
                "WARNING: No payment failures found."
            )

        if (
            failed_payment_count
            == payment_risk_count
        ):
            print(
                "PASS: Payment failures have "
                "matching risk events."
            )
        else:
            print(
                "WARNING: Payment failure and "
                "risk-event counts differ."
            )

        high_rate = delay_rates.get(
            "high",
            0,
        )

        low_rate = delay_rates.get(
            "low",
            0,
        )

        if high_rate > low_rate:
            print(
                "PASS: High-risk suppliers show "
                "higher delay rates."
            )
        else:
            print(
                "WARNING: Risk pattern is weak."
            )

    finally:

        session.close()


if __name__ == "__main__":
    main()