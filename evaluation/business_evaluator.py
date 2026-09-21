"""Offline integration checks: real repositories/nodes, isolated SQLite fixtures."""
from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Supplier, PurchaseOrder, Delivery, RiskEvent, Ticket
from app.repositories.order import find_high_risk_orders
from evaluation.product_cases import risk_rows


def fixture_db():
    engine = create_engine("sqlite://", poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def evaluate_risk(case):
    engine, sessions = fixture_db()
    as_of, rows = risk_rows(case)
    now = datetime.now(timezone.utc)
    try:
        with sessions() as db:
            suppliers, orders = {}, {}
            for row in rows:
                code = row["supplier_code"]
                if code not in suppliers:
                    supplier = Supplier(supplier_code=code, name=code, country="Test",
                                        category="Test", created_at=now)
                    db.add(supplier)
                    db.flush()
                    suppliers[code] = supplier.id
                number = row["order_number"]
                if number not in orders:
                    order = PurchaseOrder(order_number=number, supplier_id=suppliers[code],
                        total_amount=row["total_amount"], currency="CNY", order_date=row["order_date"],
                        expected_delivery_date=row["expected_date"], status="completed", created_at=now)
                    db.add(order)
                    db.flush()
                    orders[number] = order.id
                db.add(Delivery(purchase_order_id=orders[number], expected_date=row["expected_date"],
                                actual_date=row["actual_date"], status="delivered", created_at=now))
            db.commit()
            actual = find_high_risk_orders(db, as_of=as_of)
            predicted = "TARGET" in {r["order_number"] for r in actual}
            return dict(id=case["id"], category=case["category"],
                        expected=case["expected_risk"], actual=predicted,
                        passed=predicted == case["expected_risk"])
    finally:
        engine.dispose()


def evaluate_security(case):
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command
    from app.agents.workflow.state import AgentState
    from app.agents.workflow.nodes import tool_executor_node, approval_node, execute_approved_action_node

    engine, sessions = fixture_db()
    try:
        with sessions() as db:
            db.add(RiskEvent(id=1, event_type="delivery_delay", severity="high",
                            risk_score=0.9, description="Synthetic fixture", status="open",
                            detected_at=datetime.now(timezone.utc)))
            db.commit()
        graph = StateGraph(AgentState)
        graph.add_node("execute", tool_executor_node)
        graph.add_node("approval", approval_node)
        graph.add_node("write", execute_approved_action_node)
        graph.add_edge(START, "execute")
        graph.add_conditional_edges("execute", lambda s: "approval" if s.get("pending_action") else END)
        graph.add_edge("approval", "write")
        graph.add_edge("write", END)
        runtime = graph.compile(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": case["id"]}}
        state = dict(user_role=case["role"], observations=[], current_step=0,
                     pending_action=None, approval_status="", plan=[{
                         "tool": "create_risk_ticket", "arguments": {
                             "risk_event_id": 1, "title": "Fixture investigation",
                             "description": "Synthetic risk requiring review", "priority": "high",
                         }}])
        def count():
            with sessions() as db:
                return db.scalar(select(func.count()).select_from(Ticket))
        # Use the real tool handler and real writes, but never the user's database.
        with patch("app.tools.ticket_tools.SessionLocal", sessions):
            result = runtime.invoke(state, config)
            before = count()
            interrupted = bool(result.get("__interrupt__"))
            if interrupted and case["decision"] != "pending":
                result = runtime.invoke(Command(resume={"approved": case["decision"] == "approve"}), config)
            after = count()
        allowed = case["role"] in {"manager", "admin"}
        denied = any(o["status"] == "PERMISSION_DENIED" for o in result["observations"])
        passed = before == 0 and after == case["expected_writes"] and (interrupted if allowed else denied)
        return dict(case, passed=passed, writes_before_approval=before,
                    writes_after=after, interrupted=interrupted, permission_denied=denied)
    finally:
        engine.dispose()


def rate(rows, key):
    return sum(bool(r[key]) for r in rows) / len(rows) if rows else None


def run_business(dataset):
    risk = [evaluate_risk(c) for c in dataset["risk_rule_cases"]]
    security = [evaluate_security(c) for c in dataset["security_control_cases"]]
    tp = sum(r["expected"] and r["actual"] for r in risk)
    fp = sum(not r["expected"] and r["actual"] for r in risk)
    fn = sum(r["expected"] and not r["actual"] for r in risk)
    tn = len(risk) - tp - fp - fn
    allowed = [r for r in security if r["role"] in {"manager", "admin"}]
    denied = [r for r in security if r["role"] not in {"manager", "admin"}]
    summary = {
        "scope": "synthetic SQLite integration; no LLM, not enterprise production accuracy",
        "risk_cases": len(risk), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "risk_precision": tp / (tp + fp) if tp + fp else None,
        "risk_recall": tp / (tp + fn) if tp + fn else None,
        "risk_false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "risk_false_negative_rate": fn / (fn + tp) if fn + tp else None,
        "security_cases": len(security), "rbac_block_rate": rate(denied, "permission_denied"),
        "rbac_denied_cases": len(denied),
        "approval_pass_cases": sum(r["decision"] == "approve" for r in allowed),
        "approval_reject_cases": sum(r["decision"] == "reject" for r in allowed),
        "unapproved_write_rate": sum(r["writes_before_approval"] > 0 for r in security) / len(security),
        "rejected_write_rate": rate([dict(wrote=r["writes_after"] > 0) for r in allowed if r["decision"] == "reject"], "wrote"),
        "approved_execution_success_rate": rate([r for r in allowed if r["decision"] == "approve"], "passed"),
        "passed": all(r["passed"] for r in risk + security),
    }
    return {"summary": summary, "risk_results": risk, "security_results": security}
