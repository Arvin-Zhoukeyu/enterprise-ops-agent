import argparse
import json
import hashlib
import subprocess
import shutil
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path

from evaluation.product_report import build_product_report, compare_runs


DATASET_PATH = "evaluation/dataset.json"
OUTPUT_ROOT = Path("outputs/evaluation")


def print_summary(title: str, summary: dict) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")
    for key, value in summary.items():
        if not isinstance(value, dict):
            print(f"{key}: {value}")


def run_common() -> tuple[dict, dict]:
    from evaluation.evaluator import BaselineEvaluator
    from evaluation.workflow_evaluator import WorkflowEvaluator
    baseline = BaselineEvaluator(
        dataset_path=DATASET_PATH,
        dataset_section="common_agent_cases",
        output_dir=str(OUTPUT_ROOT / "baseline_common"),
    )
    baseline_results = []
    for case in baseline.load_dataset():
        baseline_results.append(baseline.evaluate_case(case))
    baseline.save_results(baseline_results)
    baseline_summary = baseline.calculate_summary(baseline_results)

    workflow = WorkflowEvaluator(
        dataset_path=DATASET_PATH,
        dataset_section="common_agent_cases",
        output_dir=str(OUTPUT_ROOT / "workflow_common"),
    )
    _, workflow_summary = workflow.run()

    print_summary("BASELINE - COMMON CASES", baseline_summary)
    print_summary("WORKFLOW - SAME COMMON CASES", workflow_summary)
    return baseline_summary, workflow_summary


def run_workflow_extension() -> dict:
    from evaluation.workflow_evaluator import WorkflowEvaluator
    evaluator = WorkflowEvaluator(
        dataset_path=DATASET_PATH,
        dataset_section="workflow_extension_cases",
        output_dir=str(OUTPUT_ROOT / "workflow_extension"),
    )
    _, summary = evaluator.run()
    print_summary("WORKFLOW EXTENSION - 30 CASES", summary)
    return summary


def run_rag(top_k: int) -> dict:
    from evaluation.rag_evaluator import RagEvaluator
    evaluator = RagEvaluator(
        dataset_path=DATASET_PATH,
        dataset_section="rag_cases",
        output_dir=str(OUTPUT_ROOT / "rag"),
        top_k=top_k,
    )
    _, summary = evaluator.run()
    print_summary("RAG RETRIEVAL - 20 CASES", summary)
    return summary


def main() -> None:
    global OUTPUT_ROOT, DATASET_PATH
    parser = argparse.ArgumentParser(
        description="Run the unified EnterpriseOps Agent benchmark."
    )
    parser.add_argument(
        "--suite",
        choices=["all", "common", "workflow", "rag", "business"],
        default="all",
    )
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--limit", type=int, help="Smoke test: first N cases per online section")
    parser.add_argument("--report-only", type=Path, help="Refresh a run after filling human_review.csv")
    parser.add_argument("--compare-to", type=Path, help="Previous run directory with the same dataset")
    parser.add_argument("--prices", type=Path, help="JSON: input_tokens/output_tokens/embedding_tokens CNY per million")
    args = parser.parse_args()

    prices = json.loads(args.prices.read_text(encoding="utf-8")) if args.prices else None
    if prices is not None:
        import math
        for key in ["input_tokens", "output_tokens", "embedding_tokens"]:
            if key not in prices or not isinstance(prices[key], (int, float)) or not math.isfinite(prices[key]) or prices[key] < 0:
                parser.error(f"prices needs a finite nonnegative number for {key}")
        if "hourly_labor_cny" in prices and (not isinstance(prices["hourly_labor_cny"], (int, float)) or not math.isfinite(prices["hourly_labor_cny"]) or prices["hourly_labor_cny"] < 0):
            parser.error("hourly_labor_cny must be a finite nonnegative number")
    if args.report_only:
        summary_file = args.report_only / "summary.json"
        saved = json.loads(summary_file.read_text(encoding="utf-8"))
        if prices is None:
            prices = saved.get("prices")
        saved["prices"] = prices
        saved["product"] = build_product_report(args.report_only, prices=prices)
        summary_file.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(saved["product"], ensure_ascii=False, indent=2))
        if args.compare_to:
            print(json.dumps(compare_runs(args.report_only, args.compare_to), indent=2))
        return
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    OUTPUT_ROOT = OUTPUT_ROOT / "runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:6])
    OUTPUT_ROOT.mkdir(parents=True)
    dataset = json.loads(Path(DATASET_PATH).read_text(encoding="utf-8"))
    if args.limit:
        for section in ["common_agent_cases", "workflow_extension_cases", "rag_cases"]:
            dataset[section] = dataset[section][:args.limit]
    DATASET_PATH = str(OUTPUT_ROOT / "dataset.json")
    Path(DATASET_PATH).write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    from app.core.config import settings
    from app.services.risk_rules import RULE_VERSION
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() if shutil.which("git") else "unavailable"
    source_hash = hashlib.sha256()
    for folder in [Path("app"), Path("evaluation")]:
        for file in sorted(folder.rglob("*.py")):
            source_hash.update(file.as_posix().encode())
            source_hash.update(file.read_bytes())

    combined = {
        "dataset": {
            "path": DATASET_PATH,
            "unique_cases": sum(len(v) for k, v in dataset.items() if k.endswith("_cases")),
            "sha256": hashlib.sha256(Path(DATASET_PATH).read_bytes()).hexdigest(),
            "counts": {k: len(v) for k, v in dataset.items() if k.endswith("_cases")},
            "source": "synthetic",
        },
        "prices": prices,
        "run": {"directory": str(OUTPUT_ROOT), "git_revision": revision,
                "source_sha256": source_hash.hexdigest(),
                "chat_model": settings.dashscope_chat_model,
                "embedding_model": settings.dashscope_embedding_model,
                "rule_version": RULE_VERSION, "suite": args.suite, "limit": args.limit},
    }

    if args.suite in {"all", "common"}:
        baseline_summary, workflow_common_summary = run_common()
        combined["baseline_common"] = baseline_summary
        combined["workflow_common"] = workflow_common_summary
        combined["common_comparison"] = {
            "task_completion_delta": round(
                workflow_common_summary["task_completion_accuracy"]
                - baseline_summary["task_completion_accuracy"],
                4,
            ),
            "routing_accuracy_delta": round(
                workflow_common_summary["routing_accuracy"]
                - baseline_summary["routing_accuracy"],
                4,
            ),
            "average_latency_delta_ms": round(
                workflow_common_summary["average_latency_ms"]
                - baseline_summary["average_latency_ms"],
                2,
            ),
        }

    if args.suite in {"all", "workflow"}:
        combined["workflow_extension"] = run_workflow_extension()

    if args.suite in {"all", "rag"}:
        combined["rag"] = run_rag(args.top_k)

    if args.suite in {"all", "business"}:
        from evaluation.business_evaluator import run_business
        business = run_business(dataset)
        combined["business_controls"] = business["summary"]
        (OUTPUT_ROOT / "business_results.json").write_text(json.dumps(business, indent=2), encoding="utf-8")
    combined["product"] = build_product_report(OUTPUT_ROOT, prices=prices)
    combined["executed_case_counts"] = {
        key: value["total_cases"] for key, value in combined.items()
        if isinstance(value, dict) and "total_cases" in value
    }
    if "business_controls" in combined:
        combined["executed_case_counts"].update(
            risk_rules=len(dataset["risk_rule_cases"]), security_controls=len(dataset["security_control_cases"]))

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary_path = OUTPUT_ROOT / "summary.json"
    summary_path.write_text(
        json.dumps(combined, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n{'#' * 64}\nUNIFIED EVALUATION SUMMARY\n{'#' * 64}")
    print(json.dumps(combined, ensure_ascii=False, indent=2))
    print(f"\nSaved to: {summary_path}")
    Path("outputs/evaluation/latest_run.txt").write_text(str(OUTPUT_ROOT), encoding="utf-8")
    if combined.get("business_controls", {}).get("passed") is False:
        raise SystemExit("Business control regression failed; inspect business_results.json")
    if args.compare_to:
        print(json.dumps(compare_runs(OUTPUT_ROOT, args.compare_to), indent=2))


if __name__ == "__main__":
    main()
