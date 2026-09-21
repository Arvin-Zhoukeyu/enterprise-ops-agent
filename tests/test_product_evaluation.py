import csv
import json
from datetime import date
from types import SimpleNamespace

import pytest

from app.observability.usage import capture_usage, record_usage
from app.services.risk_rules import six_months_before
from evaluation.business_evaluator import evaluate_risk, evaluate_security
from evaluation.product_cases import risk_cases, security_cases
from evaluation.product_report import build_product_report, compare_runs, REVIEW_FIELDS


@pytest.mark.parametrize("case", risk_cases(), ids=lambda c: c["id"] + "_" + c["category"])
def test_database_risk_boundaries(case):
    assert evaluate_risk(case)["passed"]


@pytest.mark.parametrize("case", security_cases(), ids=lambda c: c["id"])
def test_approval_graph_and_database_writes(case):
    assert evaluate_security(case)["passed"]


def test_calendar_month_boundary():
    assert six_months_before(date(2024, 8, 31)) == date(2024, 2, 29)
    assert six_months_before(date(2026, 8, 31)) == date(2026, 2, 28)


def test_usage_isolation_and_embeddings():
    with capture_usage() as outer:
        record_usage(SimpleNamespace(prompt_tokens=10, completion_tokens=4))
        with capture_usage() as inner:
            record_usage(None)
        record_usage(SimpleNamespace(total_tokens=9), embedding=True)
    assert outer["input_tokens"] == 10
    assert outer["embedding_tokens"] == 9
    assert outer["missing_usage"] == 0
    assert inner["missing_usage"] == 1


def prepare_run(root):
    folder = root / "baseline_common"
    folder.mkdir(parents=True)
    rows = [{"id": "C1", "task_correct": True, "latency_ms": 100,
             "usage": {"input_tokens": 100, "output_tokens": 20, "embedding_tokens": 10, "missing_usage": 0}},
            {"id": "C2", "task_correct": False, "latency_ms": 200, "argument_score": 0,
             "usage": {"input_tokens": 100, "output_tokens": 20, "embedding_tokens": 10, "missing_usage": 0}}]
    (folder / "results.json").write_text(json.dumps(rows), encoding="utf-8")


def write_reviews(root, rows):
    with (root / "human_review.csv").open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_unmeasured_metrics_are_not_perfect_scores(tmp_path):
    prepare_run(tmp_path)
    result = build_product_report(tmp_path)["agents"]["baseline_common"]
    assert result["reviewed_end_to_end_success_rate"] is None
    assert result["unsupported_claim_rate"] is None
    assert result["mean_cost_cny"] is None
    assert result["paired_time_reduction"] is None
    assert result["review_coverage"] == 0
    assert result["p95_latency_ms"] == 200


def test_reviewed_results_cost_denominators_and_time(tmp_path):
    prepare_run(tmp_path)
    write_reviews(tmp_path, [dict(agent="baseline_common", id="C1", reviewer="reviewer",
        task_achieved="1", claims_checked="5", unsupported_claims="1",
        citations_checked="2", correct_citations="1", participant="p1", trial_type="simulation",
        human_seconds="100", assisted_seconds="40", human_success="1", assisted_success="1",
        satisfaction="4"), dict(agent="baseline_common", id="C2", reviewer="reviewer", task_achieved="0")])
    result = build_product_report(tmp_path, prices={"input_tokens": 2, "output_tokens": 4, "embedding_tokens": 1})["agents"]["baseline_common"]
    assert result["reviewed_end_to_end_success_rate"] == 0.5
    assert result["unsupported_claim_rate"] == 0.2
    assert result["citation_correctness"] == 0.5
    assert result["mean_cost_cny"] == pytest.approx(0.00029)
    assert result["cost_per_reviewed_success_cny"] == pytest.approx(0.00058)
    assert result["paired_time_reduction"] == pytest.approx(0.6)
    assert result["time_reduction_by_trial_type"]["real_user"] is None


def test_review_validation_rejects_invalid_counts(tmp_path):
    prepare_run(tmp_path)
    write_reviews(tmp_path, [dict(agent="baseline_common", id="C1", reviewer="r", claims_checked="1", unsupported_claims="2")])
    with pytest.raises(ValueError):
        build_product_report(tmp_path)


def test_comparison_requires_same_dataset(tmp_path):
    before, after = tmp_path / "before", tmp_path / "after"
    for folder, sha in [(before, "a"), (after, "b")]:
        folder.mkdir()
        (folder / "summary.json").write_text(json.dumps({"dataset": {"sha256": sha}}))
    with pytest.raises(ValueError):
        compare_runs(after, before)


def test_workflow_errors_cannot_score_perfect_routing(tmp_path, monkeypatch):
    from evaluation.workflow_evaluator import WorkflowEvaluator
    evaluator = WorkflowEvaluator(output_dir=str(tmp_path))
    monkeypatch.setattr(evaluator, "load_dataset", lambda: [{"id": "X", "query": "question",
        "expected_route": "DIRECT_RESPONSE", "expected_tools": []}])
    def fail(**kwargs):
        raise RuntimeError("fixture failure")
    monkeypatch.setattr(evaluator.agent, "run", fail)
    rows, summary = evaluator.run()
    assert not rows[0]["task_correct"]
    assert summary["routing_accuracy"] == 0
    assert summary["tool_f1"] == 0


def test_workflow_checks_arguments_and_captures_usage(tmp_path, monkeypatch):
    from evaluation.workflow_evaluator import WorkflowEvaluator
    evaluator = WorkflowEvaluator(output_dir=str(tmp_path))
    monkeypatch.setattr(evaluator, "load_dataset", lambda: [{"id": "X", "query": "supplier 1",
        "expected_route": "TOOL_CALL", "expected_tools": ["get_supplier"],
        "expected_tool": "get_supplier", "expected_arguments": {"supplier_code": "S1"}}])
    def answer(**kwargs):
        record_usage(SimpleNamespace(prompt_tokens=15, completion_tokens=5))
        return {"result": {"requires_tools": True, "verification_status": "PASS",
            "observations": [{"tool": "get_supplier", "arguments": {"supplier_code": "S2"}, "status": "SUCCESS"}]}}
    monkeypatch.setattr(evaluator.agent, "run", answer)
    rows, summary = evaluator.run()
    assert rows[0]["argument_score"] == 0
    assert not rows[0]["task_correct"]
    assert rows[0]["usage"]["input_tokens"] == 15


def test_embedding_batches_keep_provider_usage(monkeypatch):
    from unittest.mock import MagicMock
    from app.rag import embeddings
    fake = MagicMock()
    client = fake.__enter__.return_value
    client.embeddings.create.side_effect = [
        SimpleNamespace(data=[SimpleNamespace(index=i, embedding=[float(i)]) for i in reversed(range(10))], usage=SimpleNamespace(total_tokens=100)),
        SimpleNamespace(data=[SimpleNamespace(index=0, embedding=[10.0])], usage=SimpleNamespace(total_tokens=10)),
    ]
    monkeypatch.setattr(embeddings, "create_bailian_client", lambda: fake)
    with capture_usage() as usage:
        result = embeddings.BailianEmbeddings().embed_documents(["text"]*11)
    assert result == [[float(i)] for i in range(11)]
    assert usage["embedding_tokens"] == 110
    assert usage["embedding_calls"] == 2
    assert len(client.embeddings.create.call_args_list[0].kwargs["input"]) == 10
