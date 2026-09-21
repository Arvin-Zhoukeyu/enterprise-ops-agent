"""Product metrics with explicit denominators and missing-data semantics."""
import csv
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean

REVIEW_FIELDS = ["agent", "id", "reviewer", "task_achieved", "claims_checked",
                 "unsupported_claims", "citations_checked", "correct_citations",
                 "participant", "trial_type", "human_seconds", "assisted_seconds",
                 "human_success", "assisted_success", "satisfaction", "feedback"]


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def wilson(successes, total):
    if not total:
        return None
    p, z = successes / total, 1.96
    center = (p + z*z/(2*total)) / (1 + z*z/total)
    margin = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / (1 + z*z/total)
    return [round(center - margin, 4), round(center + margin, 4)]


def export_review_template(root, groups):
    path = root / "human_review.csv"
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for agent, rows in groups.items():
            for row in rows:
                writer.writerow({"agent": agent, "id": row["id"]})


def load_reviews(path, groups):
    if not path.exists():
        return {}
    known = {(agent, row["id"]) for agent, rows in groups.items() for row in rows}
    reviews = {}
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            key = row["agent"], row["id"]
            if key not in known or key in reviews:
                raise ValueError(f"Unknown or duplicate review: {key}")
            for field in ["task_achieved", "human_success", "assisted_success"]:
                value = row.get(field, "")
                if value not in {"", "0", "1"}:
                    raise ValueError(f"{key}: {field} must be blank, 0 or 1")
            if row.get("task_achieved") and not row.get("reviewer"):
                raise ValueError(f"{key}: reviewer required")
            for field in ["claims_checked", "unsupported_claims", "citations_checked", "correct_citations",
                          "human_seconds", "assisted_seconds", "satisfaction"]:
                value = row.get(field, "")
                if value and (not math.isfinite(float(value)) or float(value) < 0):
                    raise ValueError(f"{key}: invalid {field}")
            for numerator, denominator in [("unsupported_claims", "claims_checked"), ("correct_citations", "citations_checked")]:
                n, d = row.get(numerator, ""), row.get(denominator, "")
                if bool(n) != bool(d) or (n and (int(n) > int(d) or not row.get("reviewer"))):
                    raise ValueError(f"{key}: incomplete or invalid {numerator}/{denominator}")
            if row.get("satisfaction") and not 1 <= float(row["satisfaction"]) <= 5:
                raise ValueError(f"{key}: satisfaction must be 1-5")
            timed = row.get("human_seconds") or row.get("assisted_seconds")
            if timed and (not all(row.get(f) for f in ["human_seconds", "assisted_seconds", "participant", "trial_type", "human_success", "assisted_success"])
                          or float(row["human_seconds"]) <= 0 or float(row["assisted_seconds"]) <= 0
                          or row["trial_type"] not in {"simulation", "real_user"}):
                raise ValueError(f"{key}: paired timing needs participant, trial_type, positive times and success flags")
            reviews[key] = row
    return reviews


def failure_types(row):
    labels = []
    if row.get("error"):
        labels.append("execution_error")
    for fields, label in [(("routing_correct", "route_correct"), "routing"),
                          (("tool_correct", "tool_match"), "tool_selection"),
                          (("security_correct",), "security"),
                          (("verification_correct",), "insufficient_evidence")]:
        if any(row.get(f) is False for f in fields):
            labels.append(label)
    if row.get("argument_score", 1) < 1:
        labels.append("arguments")
    if not row.get("task_correct", False) and not labels:
        labels.append("execution_or_status")
    return labels


def build_product_report(root: Path, *, prices=None):
    groups = {}
    for name in ["baseline_common", "workflow_common", "workflow_extension"]:
        path = root / name / "results.json"
        if path.exists():
            groups[name] = json.loads(path.read_text(encoding="utf-8"))
    export_review_template(root, groups)
    reviews = load_reviews(root / "human_review.csv", groups)
    report = {"scope": "synthetic offline benchmark; reviewed metrics apply only to reviewed samples",
              "prices_cny_per_million_tokens": prices,
              "cost_scope": "estimate from observed API usage, excludes hosting, KB ingestion and unreported retry usage",
              "agents": {}}
    bad = []
    for agent, rows in groups.items():
        reviewed = [(r, reviews.get((agent, r["id"]), {})) for r in rows]
        judged = [(r, v) for r, v in reviewed if v.get("task_achieved") in {"0", "1"}]
        success = sum(r["task_correct"] and v["task_achieved"] == "1" for r, v in judged)
        counts = Counter()
        costs = []
        total_usage = Counter()
        for row, review in reviewed:
            labels = failure_types(row)
            if review.get("task_achieved") == "0":
                labels.append("answer_or_business_outcome")
            counts.update(labels)
            if labels:
                bad.append(dict(agent=agent, id=row["id"], query=row.get("query"),
                                failures=labels, error=row.get("error"), feedback=review.get("feedback")))
            usage = row.get("usage", {})
            total_usage.update(usage)
            cost = None
            if prices is not None and usage and not usage.get("missing_usage") and not row.get("error"):
                cost = sum(usage.get(k, 0) * prices[k] for k in ["input_tokens", "output_tokens", "embedding_tokens"]) / 1_000_000
            costs.append(cost)
        def count_field(field):
            return sum(int(v[field]) for _, v in reviewed if v.get(field) != "" and v.get(field) is not None)
        latency = sorted(r["latency_ms"] for r in rows)
        measured_costs = [c for c in costs if c is not None]
        paired = [(r, v) for r, v in reviewed if v.get("human_seconds") and v.get("assisted_seconds")]
        comparable = [(r, v) for r, v in paired if v["human_success"] == v["assisted_success"] == "1"]
        human = sum(float(v["human_seconds"]) for _, v in comparable)
        assisted = sum(float(v["assisted_seconds"]) for _, v in comparable)
        ratings = [float(v["satisfaction"]) for _, v in reviewed if v.get("satisfaction") and v.get("participant")]
        labor_rate = prices.get("hourly_labor_cny") if prices else None
        saved_value = ((human-assisted) / 3600 * labor_rate) if comparable and labor_rate is not None else None
        report["agents"][agent] = {
            "cases": len(rows), "process_contract_success_rate": ratio(sum(r["task_correct"] for r in rows), len(rows)),
            "reviewed_cases": len(judged), "review_coverage": ratio(len(judged), len(rows)),
            "reviewed_end_to_end_success_rate": ratio(success, len(judged)),
            "reviewed_end_to_end_wilson95": wilson(success, len(judged)),
            "claims_checked": count_field("claims_checked"),
            "unsupported_claim_rate": ratio(count_field("unsupported_claims"), count_field("claims_checked")),
            "citations_checked": count_field("citations_checked"),
            "citation_correctness": ratio(count_field("correct_citations"), count_field("citations_checked")),
            "average_latency_ms": mean(latency) if latency else None,
            "p95_latency_ms": latency[math.ceil(len(latency)*0.95)-1] if latency else None,
            "usage": dict(total_usage), "cost_coverage": ratio(len(measured_costs), len(rows)),
            "mean_cost_cny": mean(measured_costs) if measured_costs else None,
            "cost_per_reviewed_success_cny": (sum(measured_costs)/success if success and len(judged)==len(rows) and len(measured_costs)==len(rows) else None),
            "timed_pairs": len(paired), "both_successful_pairs": len(comparable),
            "paired_time_reduction": (1-assisted/human) if human else None,
            "time_reduction_by_trial_type": {
                kind: (1-sum(float(v["assisted_seconds"]) for _, v in comparable if v["trial_type"] == kind)
                       /sum(float(v["human_seconds"]) for _, v in comparable if v["trial_type"] == kind))
                if any(v["trial_type"] == kind for _, v in comparable) else None
                for kind in ["simulation", "real_user"]},
            "participants": len({v["participant"] for _, v in paired}),
            "paired_labor_value_saved_cny": saved_value,
            "labor_value_scope": "scenario estimate on both-successful timed pairs; not realized headcount savings or total ROI",
            "assisted_trial_success_rate": ratio(sum(v["assisted_success"] == "1" for _, v in paired), len(paired)),
            "satisfaction_responses": len(ratings), "mean_satisfaction_1_to_5": mean(ratings) if ratings else None,
            "bad_case_counts": dict(counts),
        }
    (root / "product_metrics.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (root / "bad_cases.json").write_text(json.dumps(bad, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# AI PM Product Evaluation", "", report["scope"], "",
             "Blank metrics mean not measured, never zero or 100%.", "",
             "Review evidence in each agent's results.json and complete human_review.csv.", ""]
    business_path = root / "business_results.json"
    if business_path.exists():
        business = json.loads(business_path.read_text(encoding="utf-8"))["summary"]
        report["business_controls"] = business
        lines.extend(["## Business controls (no LLM)", "", "| Metric | Result |", "| --- | --- |"])
        lines.extend(f"| {key} | {value} |" for key, value in business.items())
        lines.append("")
    for agent, metrics in report["agents"].items():
        lines.extend([f"## {agent}", "", "| Metric | Result |", "| --- | --- |"])
        for key, value in metrics.items():
            if isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False)
            lines.append(f"| {key} | {'NOT MEASURED' if value is None else value} |")
        lines.append("")
    (root / "product_report.md").write_text("\n".join(lines), encoding="utf-8")
    (root / "product_metrics.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def compare_runs(current: Path, previous: Path):
    now = json.loads((current / "summary.json").read_text(encoding="utf-8"))
    old = json.loads((previous / "summary.json").read_text(encoding="utf-8"))
    if now["dataset"]["sha256"] != old["dataset"]["sha256"]:
        raise ValueError("Cannot compare runs with different datasets")
    comparison = {}
    for name in ["baseline_common", "workflow_common", "workflow_extension"]:
        a, b = current / name / "results.json", previous / name / "results.json"
        if not a.exists() or not b.exists():
            continue
        new = {r["id"]: r for r in json.loads(a.read_text(encoding="utf-8"))}
        prior = {r["id"]: r for r in json.loads(b.read_text(encoding="utf-8"))}
        if new.keys() != prior.keys():
            raise ValueError("Compared case IDs must match")
        comparison[name] = {
            "fixed": [i for i in new if new[i]["task_correct"] and not prior[i]["task_correct"]],
            "regressed": [i for i in new if not new[i]["task_correct"] and prior[i]["task_correct"]],
            "scope": "process contract only; inspect model/config changes before attributing causality",
        }
    (current / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    return comparison
