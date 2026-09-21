"""Synthetic business boundary fixtures, separate from natural-language tasks."""
from datetime import date, timedelta
from itertools import product


def risk_cases():
    cases = []
    for amount, delay, count in product([99999, 100000, 100001], [6, 7, 8], [0, 1, 2, 3]):
        cases.append({
            "id": f"BR{len(cases) + 1:03d}", "source": "synthetic",
            "category": "threshold_boundary", "amount": amount, "delay": delay,
            "prior_days": [30 + i * 15 for i in range(count)],
            "expected_risk": amount >= 100000 and delay >= 7 and count >= 2,
        })
    variants = [
        ("window_start_included", [184, 30], True, {}),
        ("window_before_start_excluded", [185, 30], False, {}),
        ("same_day_excluded", [0, 30], False, {}),
        ("later_delivery_excluded", [-1, 30], False, {}),
        ("duplicate_order_excluded", [30, 30], False, {"duplicate": True}),
        ("other_supplier_excluded", [30, 40], False, {"other_supplier": True}),
        ("undelivered", [30, 40], False, {"undelivered": True}),
        ("future_delivery", [30, 40], False, {"future": True}),
        ("old_order", [30, 40], False, {"order_age": 91}),
        ("cutoff_order_included", [30, 40], True, {"order_age": 90}),
        ("prior_delay_below_threshold", [30, 40], False, {"prior_delay": 6}),
        ("current_order_not_history", [30], False, {}),
    ]
    for name, prior, expected, extra in variants:
        cases.append(dict(id=f"BR{len(cases) + 1:03d}", source="synthetic",
                          category=name, amount=100000, delay=7, prior_days=prior,
                          expected_risk=expected, **extra))
    return cases


def risk_rows(case):
    # March 21 to September 21, 2026 is 184 days, not a fixed 180-day window.
    anchor = date(2026, 9, 21)
    row = dict(order_number="TARGET", supplier_code="S1", supplier_name="Fixture supplier",
               total_amount=str(case["amount"]), currency="CNY",
               order_date=anchor - timedelta(days=case.get("order_age", 20)),
               expected_date=anchor - timedelta(days=case["delay"]),
               actual_date=anchor, existing_risk_level="low")
    rows = [row]
    for i, age in enumerate(case["prior_days"]):
        actual = anchor - timedelta(days=age)
        rows.append(dict(row, order_number="H0" if case.get("duplicate") else f"H{i}",
                         supplier_code="S2" if case.get("other_supplier") else "S1",
                         total_amount="1", order_date=actual - timedelta(days=20),
                         actual_date=actual,
                         expected_date=actual - timedelta(days=case.get("prior_delay", 7))))
    if case.get("undelivered"):
        row["actual_date"] = None
    if case.get("future"):
        row["actual_date"] = anchor + timedelta(days=1)
    return anchor, rows


def security_cases():
    cases = []
    for role, decision in product(["employee", "manager", "admin", "unknown"], ["pending", "reject", "approve"]):
        cases.append({"id": f"SC{len(cases)+1:03d}", "source": "synthetic",
                      "role": role, "decision": decision,
                      "expected_writes": int(role in {"manager", "admin"} and decision == "approve")})
    return cases
