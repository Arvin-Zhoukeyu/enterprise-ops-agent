import argparse
import json
from pathlib import Path

from evaluation.evaluator import BaselineEvaluator
from evaluation.rag_evaluator import RagEvaluator
from evaluation.workflow_evaluator import WorkflowEvaluator


DATASET_PATH = "evaluation/dataset.json"
OUTPUT_ROOT = Path("outputs/evaluation")


def print_summary(title: str, summary: dict) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")
    for key, value in summary.items():
        if not isinstance(value, dict):
            print(f"{key}: {value}")


def run_common() -> tuple[dict, dict]:
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

    print_summary("BASELINE - COMMON 60 CASES", baseline_summary)
    print_summary("WORKFLOW - SAME COMMON 60 CASES", workflow_summary)
    return baseline_summary, workflow_summary


def run_workflow_extension() -> dict:
    evaluator = WorkflowEvaluator(
        dataset_path=DATASET_PATH,
        dataset_section="workflow_extension_cases",
        output_dir=str(OUTPUT_ROOT / "workflow_extension"),
    )
    _, summary = evaluator.run()
    print_summary("WORKFLOW EXTENSION - 30 CASES", summary)
    return summary


def run_rag(top_k: int) -> dict:
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
    parser = argparse.ArgumentParser(
        description="Run the unified EnterpriseOps Agent benchmark."
    )
    parser.add_argument(
        "--suite",
        choices=["all", "common", "workflow", "rag"],
        default="all",
    )
    parser.add_argument("--top-k", type=int, default=2)
    args = parser.parse_args()

    combined = {
        "dataset": {
            "path": DATASET_PATH,
            "unique_cases": 110,
            "common_cases": 60,
            "workflow_extension_cases": 30,
            "rag_cases": 20,
            "source": "synthetic",
        }
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

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary_path = OUTPUT_ROOT / "summary.json"
    summary_path.write_text(
        json.dumps(combined, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n{'#' * 64}\nUNIFIED EVALUATION SUMMARY\n{'#' * 64}")
    print(json.dumps(combined, ensure_ascii=False, indent=2))
    print(f"\nSaved to: {summary_path}")


if __name__ == "__main__":
    main()
