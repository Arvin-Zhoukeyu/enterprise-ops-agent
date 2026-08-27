import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from faker import Faker
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models import (
    Delivery,
    OrderItem,
    Payment,
    Product,
    PurchaseOrder,
    RiskEvent,
    Supplier,
    Ticket,
)

fake = Faker("en_US")

random.seed(42)
Faker.seed(42)


SUPPLIER_COUNT = 100
PRODUCT_COUNT = 200
ORDER_COUNT = 3000


def clear_database(session):
    """
    Delete existing seeded data.

    Delete child tables before parent tables to avoid
    foreign-key constraint errors.
    """

    session.execute(delete(Ticket))
    session.execute(delete(RiskEvent))
    session.execute(delete(Payment))
    session.execute(delete(Delivery))
    session.execute(delete(OrderItem))
    session.execute(delete(PurchaseOrder))
    session.execute(delete(Product))
    session.execute(delete(Supplier))

    session.commit()


def create_suppliers(session):
    suppliers = []

    categories = [
        "electronics",
        "raw_material",
        "packaging",
        "office_supply",
        "logistics",
        "manufacturing",
    ]

    countries = [
        "China",
        "New Zealand",
        "Australia",
        "Singapore",
        "Malaysia",
        "Vietnam",
    ]

    for i in range(1, SUPPLIER_COUNT + 1):

        # 前 10 个供应商故意设计成高风险供应商
        if i <= 10:
            risk_level = "high"
            rating = round(random.uniform(2.0, 3.2), 2)

        # 11~30 为中风险供应商
        elif i <= 30:
            risk_level = "medium"
            rating = round(random.uniform(3.0, 4.0), 2)

        else:
            risk_level = "low"
            rating = round(random.uniform(4.0, 5.0), 2)

        supplier = Supplier(
            supplier_code=f"SUP-2026-{i:04d}",
            name=fake.company(),
            country=random.choice(countries),
            category=random.choice(categories),
            rating=rating,
            risk_level=risk_level,
            cooperation_years=random.randint(1, 15),
            status="active",
            created_at=datetime.now(timezone.utc),
        )

        session.add(supplier)
        suppliers.append(supplier)

    session.commit()

    return suppliers


def create_products(session):
    products = []

    categories = [
        "electronics",
        "components",
        "packaging",
        "equipment",
        "office_supply",
    ]

    for i in range(1, PRODUCT_COUNT + 1):

        product = Product(
            sku=f"SKU-{i:05d}",
            name=f"Product {i}",
            category=random.choice(categories),
            unit=random.choice(
                ["piece", "box", "kg", "set"]
            ),
            created_at=datetime.now(timezone.utc),
        )

        session.add(product)
        products.append(product)

    session.commit()

    return products


def generate_order_amount():
    """
    Most orders are normal-sized.

    A small percentage are intentionally generated as
    unusually large purchase orders.
    """

    probability = random.random()

    if probability < 0.05:
        # 5% high-value abnormal orders
        return Decimal(
            str(
                round(
                    random.uniform(
                        150000,
                        800000,
                    ),
                    2,
                )
            )
        )

    return Decimal(
        str(
            round(
                random.uniform(
                    5000,
                    90000,
                ),
                2,
            )
        )
    )


def generate_delay_days(supplier):
    """
    Generate delivery delays based on supplier risk.

    High-risk suppliers have much higher probability
    of repeated delays.
    """

    probability = random.random()

    if supplier.risk_level == "high":

        if probability < 0.65:
            return random.randint(8, 30)

        return random.randint(0, 5)

    if supplier.risk_level == "medium":

        if probability < 0.30:
            return random.randint(3, 15)

        return random.randint(0, 3)

    # low-risk supplier
    if probability < 0.08:
        return random.randint(1, 7)

    return 0


def create_orders(
    session,
    suppliers,
    products,
):
    orders = []

    today = date.today()

    for i in range(1, ORDER_COUNT + 1):

        supplier = random.choice(suppliers)

        order_date = today - timedelta(
            days=random.randint(1, 365)
        )

        expected_delivery = (
            order_date
            + timedelta(
                days=random.randint(7, 30)
            )
        )

        amount = generate_order_amount()

        purchase_order = PurchaseOrder(
            order_number=f"PO-2026-{i:06d}",
            supplier_id=supplier.id,
            total_amount=amount,
            currency="CNY",
            order_date=order_date,
            expected_delivery_date=expected_delivery,
            status="completed",
            created_at=datetime.now(timezone.utc),
        )

        session.add(purchase_order)
        session.flush()

        create_order_items(
            session,
            purchase_order,
            products,
        )

        create_delivery(
            session,
            purchase_order,
            supplier,
        )

        create_payment(
            session,
            purchase_order,
            supplier,
        )

        orders.append(purchase_order)

    session.commit()

    return orders


def create_order_items(
    session,
    order,
    products,
):
    item_count = random.randint(1, 5)

    selected_products = random.sample(
        products,
        item_count,
    )

    for product in selected_products:

        quantity = random.randint(1, 100)

        unit_price = Decimal(
            str(
                round(
                    random.uniform(
                        20,
                        5000,
                    ),
                    2,
                )
            )
        )

        item = OrderItem(
            purchase_order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=unit_price,
        )

        session.add(item)


def create_delivery(
    session,
    order,
    supplier,
):
    delay_days = generate_delay_days(
        supplier
    )

    actual_date = (
        order.expected_delivery_date
        + timedelta(
            days=delay_days
        )
    )

    status = (
        "delayed"
        if delay_days > 0
        else "delivered"
    )

    delivery = Delivery(
        purchase_order_id=order.id,
        expected_date=order.expected_delivery_date,
        actual_date=actual_date,
        status=status,
        carrier=random.choice(
            [
                "DHL",
                "FedEx",
                "UPS",
                "SF Express",
            ]
        ),
        tracking_number=fake.uuid4(),
        created_at=datetime.now(timezone.utc),
    )

    session.add(delivery)

    if delay_days >= 7:

        create_delay_risk_event(
            session,
            supplier,
            order,
            delay_days,
        )


def create_payment(
    session,
    order,
    supplier,
):
    probability = random.random()

    # High-risk suppliers have more payment issues
    if supplier.risk_level == "high":
        failure_probability = 0.15

    elif supplier.risk_level == "medium":
        failure_probability = 0.07

    else:
        failure_probability = 0.02

    if probability < failure_probability:
        status = "failed"
        payment_date = None

    else:
        status = "paid"

        payment_date = (
            order.order_date
            + timedelta(
                days=random.randint(
                    1,
                    30,
                )
            )
        )

    payment = Payment(
        purchase_order_id=order.id,
        payment_reference=f"PAY-{order.id:08d}",
        amount=order.total_amount,
        payment_date=payment_date,
        status=status,
        method=random.choice(
            [
                "bank_transfer",
                "credit",
                "corporate_account",
            ]
        ),
        created_at=datetime.now(timezone.utc),
    )

    session.add(payment)

    if status == "failed":

        risk_event = RiskEvent(
            supplier_id=supplier.id,
            purchase_order_id=order.id,
            event_type="payment_failure",
            severity="medium",
            risk_score=0.6,
            description=(
                f"Payment failed for order "
                f"{order.order_number}."
            ),
            status="open",
            detected_at=datetime.now(
                timezone.utc
            ),
        )

        session.add(risk_event)


def create_delay_risk_event(
    session,
    supplier,
    order,
    delay_days,
):
    if delay_days >= 15:
        severity = "high"
        risk_score = 0.9

    else:
        severity = "medium"
        risk_score = 0.7

    event = RiskEvent(
        supplier_id=supplier.id,
        purchase_order_id=order.id,
        event_type="delivery_delay",
        severity=severity,
        risk_score=risk_score,
        description=(
            f"Order {order.order_number} "
            f"was delayed by "
            f"{delay_days} days."
        ),
        status="open",
        detected_at=datetime.now(
            timezone.utc
        ),
    )

    session.add(event)


def print_summary(session):

    supplier_count = session.query(
        Supplier
    ).count()

    product_count = session.query(
        Product
    ).count()

    order_count = session.query(
        PurchaseOrder
    ).count()

    delivery_count = session.query(
        Delivery
    ).count()

    payment_count = session.query(
        Payment
    ).count()

    risk_count = session.query(
        RiskEvent
    ).count()

    print("\nDatabase seed completed.")
    print("-------------------------")
    print(
        f"Suppliers:     "
        f"{supplier_count}"
    )
    print(
        f"Products:      "
        f"{product_count}"
    )
    print(
        f"Orders:        "
        f"{order_count}"
    )
    print(
        f"Deliveries:    "
        f"{delivery_count}"
    )
    print(
        f"Payments:      "
        f"{payment_count}"
    )
    print(
        f"Risk Events:   "
        f"{risk_count}"
    )


def main():

    session = SessionLocal()

    try:

        print(
            "Cleaning existing data..."
        )

        clear_database(session)

        print(
            "Creating suppliers..."
        )

        suppliers = create_suppliers(
            session
        )

        print(
            "Creating products..."
        )

        products = create_products(
            session
        )

        print(
            "Creating purchase orders..."
        )

        create_orders(
            session,
            suppliers,
            products,
        )

        print_summary(session)

    except Exception:

        session.rollback()
        raise

    finally:

        session.close()


if __name__ == "__main__":
    main()