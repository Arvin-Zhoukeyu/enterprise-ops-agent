import json
import time
from pathlib import Path
from statistics import mean, median

import pandas as pd

from app.agents.workflow.agent import WorkflowAgent


def unique_in_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


class WorkflowEvaluator:
    def __init__(
        self,
        dataset_path: str = "evaluation/dataset.json",
        dataset_section: str = "common_agent_cases",
        output_dir: str = "outputs/evaluation/workflow",
    ):
        self.dataset_path = Path(dataset_path)
        self.dataset_section = dataset_section
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.agent = WorkflowAgent()

    def load_dataset(self) -> list[dict]:
        with self.dataset_path.open("r", encoding="utf-8") as file:
            dataset = json.load(file)
        if isinstance(dataset, list):
            return dataset
        return dataset[self.dataset_section]

    def run(self):
        results = []

        for case in self.load_dataset():
            user_input = case.get("input") or case["query"]
            print(f"\n================================\nCase: {case['id']}\n{user_input}")
            start = time.perf_counter()
            execution_success = True
            error = None

            try:
                response = self.agent.run(
                    user_input=user_input,
                    user_role=case.get("role", "employee"),
                )
                state = response["result"]
            except Exception as exc:
                execution_success = False
                error = str(exc)
                state = {}

            latency_ms = (time.perf_counter() - start) * 1000
            observations = state.get("observations", [])
            actual_tools = [
                observation.get("tool")
                for observation in observations
                if observation.get("tool")
            ]

            pending_action = state.get("pending_action")
            if pending_action and pending_action.get("tool"):
                actual_tools.append(pending_action["tool"])

            actual_tools = unique_in_order(actual_tools)
            expected_tools = case.get("expected_tools", [])
            expected_set = set(expected_tools)
            actual_set = set(actual_tools)

            if expected_set:
                tool_recall = len(expected_set & actual_set) / len(expected_set)
            else:
                tool_recall = 1.0 if not actual_set else 0.0

            if actual_set:
                tool_precision = len(expected_set & actual_set) / len(actual_set)
            else:
                tool_precision = 1.0 if not expected_set else 0.0

            tool_f1 = (
                2 * tool_precision * tool_recall / (tool_precision + tool_recall)
                if tool_precision + tool_recall
                else 0.0
            )
            tool_match = actual_tools == expected_tools

            actual_route = (
                "TOOL_CALL"
                if state.get("requires_tools")
                else "DIRECT_RESPONSE"
            )
            expected_route = case.get("expected_route")
            route_correct = expected_route is None or actual_route == expected_route

            observation_statuses = {
                observation.get("status")
                for observation in observations
            }
            if "PERMISSION_DENIED" in observation_statuses:
                actual_security_status = "PERMISSION_DENIED"
            elif (
                pending_action is not None
                or state.get("approval_status") == "PENDING"
                or state.get("__interrupt__")
            ):
                actual_security_status = "APPROVAL_REQUIRED"
            else:
                actual_security_status = None

            expected_security_status = case.get("expected_security_status")
            security_correct = (
                expected_security_status is None
                or actual_security_status == expected_security_status
            )

            verification_status = state.get("verification_status", "")
            verification_required = (
                expected_route == "TOOL_CALL"
                and expected_security_status is None
            )
            verification_correct = (
                not verification_required
                or verification_status == "PASS"
            )

            task_correct = (
                execution_success
                and route_correct
                and tool_match
                and security_correct
                and verification_correct
            )

            results.append(
                {
                    "id": case["id"],
                    "category": case.get("category", "unspecified"),
                    "execution_success": execution_success,
                    "task_correct": task_correct,
                    "latency_ms": latency_ms,
                    "expected_route": expected_route,
                    "actual_route": actual_route,
                    "route_correct": route_correct,
                    "expected_tools": expected_tools,
                    "actual_tools": actual_tools,
                    "tool_match": tool_match,
                    "tool_precision": tool_precision,
                    "tool_recall": tool_recall,
                    "tool_f1": tool_f1,
                    "expected_security_status": expected_security_status,
                    "actual_security_status": actual_security_status,
                    "security_correct": security_correct,
                    "verification_status": verification_status,
                    "verification_correct": verification_correct,
                    "replan_count": state.get("replan_count", 0),
                    "error": error,
                }
            )

        self.save_results(results)
        summary = self.build_summary(results)
        self.save_summary(summary)
        print("\nFinal workflow summary:")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return results, summary

    def build_summary(self, results: list[dict]) -> dict:
        if not results:
            return {}

        total = len(results)
        latencies = sorted(result["latency_ms"] for result in results)
        security_results = [
            result
            for result in results
            if result["expected_security_status"] is not None
        ]
        categories = sorted({result["category"] for result in results})
        category_accuracy = {
            category: round(
                mean(
                    result["task_correct"]
                    for result in results
                    if result["category"] == category
                ),
                4,
            )
            for category in categories
        }
        p95_index = max(0, int(len(latencies) * 0.95) - 1)

        return {
            "total_cases": total,
            "execution_success_rate": round(
                mean(result["execution_success"] for result in results), 4
            ),
            "agent_success_rate": round(
                mean(result["execution_success"] for result in results), 4
            ),
            "task_completion_accuracy": round(
                mean(result["task_correct"] for result in results), 4
            ),
            "routing_accuracy": round(
                mean(result["route_correct"] for result in results), 4
            ),
            "exact_tool_sequence_accuracy": round(
                mean(result["tool_match"] for result in results), 4
            ),
            "tool_precision": round(
                mean(result["tool_precision"] for result in results), 4
            ),
            "tool_recall": round(
                mean(result["tool_recall"] for result in results), 4
            ),
            "tool_f1": round(
                mean(result["tool_f1"] for result in results), 4
            ),
            "security_control_accuracy": (
                round(mean(result["security_correct"] for result in security_results), 4)
                if security_results
                else None
            ),
            "average_latency_ms": round(mean(latencies), 2),
            "p50_latency_ms": round(median(latencies), 2),
            "p95_latency_ms": round(latencies[p95_index], 2),
            "average_replans": round(
                mean(result["replan_count"] for result in results), 4
            ),
            "category_task_accuracy": category_accuracy,
        }

    def save_results(self, results: list[dict]):
        with (self.output_dir / "results.json").open("w", encoding="utf-8") as file:
            json.dump(results, file, ensure_ascii=False, indent=2, default=str)
        pd.DataFrame(results).to_csv(
            self.output_dir / "results.csv",
            index=False,
            encoding="utf-8-sig",
        )

    def save_summary(self, summary: dict):
        with (self.output_dir / "summary.json").open("w", encoding="utf-8") as file:
            json.dump(summary, file, ensure_ascii=False, indent=2)
