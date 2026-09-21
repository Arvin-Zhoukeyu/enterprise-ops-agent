"""Retrospective risk screening: inclusive thresholds, six calendar months."""
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict

RULE_VERSION = "2026.2"


def six_months_before(day: date) -> date:
    year, month = divmod(day.year * 12 + day.month - 1 - 6, 12)
    month += 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


def screen_orders(rows, *, as_of, days=90, min_amount=Decimal("100000"),
                  min_delay_days=7, min_historical_delays=2):
    """Rows are order-delivery records. Count distinct prior orders, not shipments."""
    result = []
    by_supplier = defaultdict(list)
    for row in rows:
        by_supplier[row["supplier_code"]].append(row)
    for row in rows:
        actual = row["actual_date"]
        if actual is None or actual > as_of:
            continue
        if not as_of - timedelta(days=days) <= row["order_date"] <= as_of:
            continue
        delay = (actual - row["expected_date"]).days
        if Decimal(str(row["total_amount"])) < min_amount or delay < min_delay_days:
            continue
        # A prior incident must have been observable before this delivery.
        prior = {
            other["order_number"] for other in by_supplier[row["supplier_code"]]
            if other["supplier_code"] == row["supplier_code"]
            and other["order_number"] != row["order_number"]
            and other["actual_date"] is not None
            and six_months_before(actual) <= other["actual_date"] < actual
            and (other["actual_date"] - other["expected_date"]).days >= min_delay_days
        }
        if len(prior) >= min_historical_delays:
            result.append({
                key: row[key] for key in (
                    "order_number", "supplier_code", "supplier_name", "total_amount",
                    "currency", "order_date", "existing_risk_level",
                )
            } | {"delay_days": delay, "historical_delay_count": len(prior)})
    # Multi-shipment orders must not be returned repeatedly.
    unique = {row["order_number"]: row for row in result}
    return sorted(unique.values(), key=lambda row: (-Decimal(str(row["total_amount"])), row["order_number"]))
