import json
from dataclasses import asdict
from math import ceil
from pathlib import Path
from statistics import mean, median
from typing import Any

import pandas as pd

from app.agents.baseline_agent import (
    BaselineAgent,
)
from evaluation.metrics import (
    argument_match_score,
)
from app.observability.usage import capture_usage


class BaselineEvaluator:

    def __init__(
        self,
        dataset_path: str = (
            "evaluation/"
            "dataset.json"
        ),
        dataset_section: str = "common_agent_cases",
        output_dir: str = (
            "outputs/evaluation/baseline"
        ),
    ):

        self.dataset_path = Path(
            dataset_path
        )

        self.dataset_section = dataset_section

        self.output_dir = Path(
            output_dir
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.agent = BaselineAgent(
            save_traces=False
        )

    def load_dataset(
        self,
    ) -> list[dict[str, Any]]:

        with self.dataset_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            dataset = json.load(file)

        if isinstance(dataset, list):
            return dataset

        return dataset[self.dataset_section]

    def run(self):

        dataset = (
            self.load_dataset()
        )

        results = []

        print(
            f"\nRunning baseline evaluation "
            f"with {len(dataset)} cases...\n"
        )

        for index, case in enumerate(
            dataset,
            start=1,
        ):

            print(
                f"[{index}/{len(dataset)}] "
                f"{case['id']} "
                f"{case['query']}"
            )

            result = (
                self.evaluate_case(
                    case
                )
            )

            results.append(
                result
            )

            print(
                f"  Routing: "
                f"{result['actual_routing']}"
            )

            print(
                f"  Tool: "
                f"{result['actual_tool']}"
            )

            print(
                f"  Routing Correct: "
                f"{result['routing_correct']}"
            )

            print(
                f"  Tool Correct: "
                f"{result['tool_correct']}"
            )

            print()

        self.save_results(
            results
        )

        self.print_summary(
            results
        )

    def evaluate_case(
        self,
        case: dict[str, Any],
    ) -> dict[str, Any]:

        error = None

        try:

            with capture_usage() as usage:
                answer = self.agent.run(case["query"])

        except Exception as exc:

            answer = ""

            error = str(exc)

        trace = self.agent.last_trace

        if trace is None:

            raise RuntimeError(
                "Agent trace was not generated."
            )

        actual_tool = None

        actual_arguments = {}

        actual_tool_status = None

        if trace.tool_calls:

            first_tool = (
                trace.tool_calls[0]
            )

            actual_tool = (
                first_tool.tool_name
            )

            actual_arguments = (
                first_tool.arguments
            )

            actual_tool_status = (
                first_tool.status
            )

        expected_routing = (
            case[
                "expected_routing"
            ]
        )

        expected_tool = (
            case.get(
                "expected_tool"
            )
        )

        expected_arguments = (
            case.get(
                "expected_arguments",
                {},
            )
        )

        routing_correct = (
            trace.routing
            == expected_routing
        )

        if expected_tool is None:

            tool_correct = (
                actual_tool is None
            )

        else:

            tool_correct = (
                actual_tool
                == expected_tool
            )

        argument_score = (
            argument_match_score(
                expected_arguments,
                actual_arguments,
            )
            if expected_tool
            is not None
            else 1.0
        )

        actual_tools = list(dict.fromkeys(call.tool_name for call in trace.tool_calls))
        expected_tools = case.get("expected_tools", [expected_tool] if expected_tool else [])
        tool_correct = not error and trace.success and actual_tools == expected_tools

        expected_status = (
            case.get(
                "expected_status"
            )
        )

        if expected_status:

            status_correct = (
                actual_tool_status
                == expected_status
            )

        else:

            status_correct = True

        return {
            "usage": usage,
            "actual_tools": actual_tools,
            "expected_tools": expected_tools,
            "observations": [asdict(call) for call in trace.tool_calls],
            "id":
                case["id"],

            "category":
                case["category"],

            "query":
                case["query"],

            "expected_routing":
                expected_routing,

            "actual_routing":
                trace.routing,

            "routing_correct":
                routing_correct,

            "expected_tool":
                expected_tool,

            "actual_tool":
                actual_tool,

            "tool_correct":
                tool_correct,

            "expected_arguments":
                expected_arguments,

            "actual_arguments":
                actual_arguments,

            "argument_score":
                argument_score,

            "expected_status":
                expected_status,

            "actual_tool_status":
                actual_tool_status,

            "status_correct":
                status_correct,

            "task_correct": (
                trace.success
                and all(call.status in {"SUCCESS", "BLOCKED"} for call in trace.tool_calls)
                and all(not (call.status == "SUCCESS" and isinstance(call.result, dict)
                             and call.result.get("success") is False) for call in trace.tool_calls)
                and routing_correct
                and tool_correct
                and argument_score == 1.0
                and status_correct
            ),

            "llm_calls":
                trace.llm_calls,

            "tool_calls":
                len(
                    trace.tool_calls
                ),

            "input_tokens":
                trace.input_tokens,

            "output_tokens":
                trace.output_tokens,

            "total_tokens":
                trace.total_tokens,

            "latency_ms":
                trace.latency_ms,

            "agent_success":
                trace.success,

            "answer":
                answer,

            "error":
                error
                or trace.error,
        }

    def save_results(
        self,
        results: list[
            dict[str, Any]
        ],
    ):

        json_file = (
            self.output_dir
            / "results.json"
        )

        with json_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                results,
                file,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

        dataframe = pd.DataFrame(
            results
        )

        dataframe.to_csv(
            self.output_dir
            / "results.csv",
            index=False,
            encoding="utf-8-sig",
        )

        summary = (
            self.calculate_summary(
                results
            )
        )

        with (
            self.output_dir
            / "summary.json"
        ).open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                summary,
                file,
                ensure_ascii=False,
                indent=2,
            )

    def calculate_summary(
        self,
        results,
    ):

        total = len(results)

        routing_accuracy = (
            sum(
                result[
                    "routing_correct"
                ]
                for result in results
            )
            / total
        )

        tool_accuracy = (
            sum(
                result[
                    "tool_correct"
                ]
                for result in results
            )
            / total
        )

        argument_accuracy = mean(
            result[
                "argument_score"
            ]
            for result in results
        )

        success_rate = (
            sum(
                result[
                    "agent_success"
                ]
                for result in results
            )
            / total
        )

        task_accuracy = (
            sum(
                result["task_correct"]
                for result in results
            )
            / total
        )

        status_accuracy = (
            sum(
                result["status_correct"]
                for result in results
            )
            / total
        )

        average_latency = mean(
            result[
                "latency_ms"
            ]
            for result in results
        )

        average_tokens = mean(
            result[
                "total_tokens"
            ]
            for result in results
        )

        sorted_latencies = sorted(
            result[
                "latency_ms"
            ]
            for result in results
        )

        p95_index = max(
            0,
            ceil(
                len(sorted_latencies)
                * 0.95
            )
            - 1,
        )

        p95_latency = (
            sorted_latencies[
                p95_index
            ]
        )

        categories = sorted({
            result["category"]
            for result in results
        })

        category_accuracy = {}
        for category in categories:
            category_results = [
                result
                for result in results
                if result["category"] == category
            ]
            category_accuracy[category] = round(
                sum(
                    result["task_correct"]
                    for result in category_results
                )
                / len(category_results),
                4,
            )

        return {
            "total_cases":
                total,

            "routing_accuracy":
                round(
                    routing_accuracy,
                    4,
                ),

            "tool_selection_accuracy":
                round(
                    tool_accuracy,
                    4,
                ),

            "argument_accuracy":
                round(
                    argument_accuracy,
                    4,
                ),

            "agent_success_rate":
                round(
                    success_rate,
                    4,
                ),

            "task_completion_accuracy":
                round(task_accuracy, 4),

            "status_accuracy":
                round(status_accuracy, 4),

            "average_latency_ms":
                round(
                    average_latency,
                    2,
                ),

            "p50_latency_ms":
                round(median(sorted_latencies), 2),

            "p95_latency_ms":
                round(
                    p95_latency,
                    2,
                ),

            "average_tokens":
                round(
                    average_tokens,
                    2,
                ),

            "average_llm_calls":
                round(
                    mean(
                        result["llm_calls"]
                        for result in results
                    ),
                    2,
                ),

            "average_tool_calls":
                round(
                    mean(
                        result["tool_calls"]
                        for result in results
                    ),
                    2,
                ),

            "category_task_accuracy":
                category_accuracy,
        }

    def print_summary(
        self,
        results,
    ):

        summary = (
            self.calculate_summary(
                results
            )
        )

        print(
            "\n"
            "================================="
        )

        print(
            " Baseline Agent Evaluation"
        )

        print(
            "================================="
        )

        for key, value in (
            summary.items()
        ):

            print(
                f"{key}: {value}"
            )

        print(
            "================================="
        )
