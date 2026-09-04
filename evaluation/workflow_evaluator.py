import json
import time
from pathlib import Path
from statistics import mean

import pandas as pd

from app.agents.workflow.agent import (
    WorkflowAgent,
)


class WorkflowEvaluator:

    def __init__(
        self,
        dataset_path: str = (
            "evaluation/"
            "workflow_dataset.json"
        ),
        output_dir: str = (
            "outputs/"
            "evaluation/"
            "workflow"
        ),
    ):

        self.dataset_path = Path(
            dataset_path
        )

        self.output_dir = Path(
            output_dir
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.agent = (
            WorkflowAgent()
        )

    def load_dataset(
        self,
    ) -> list[dict]:

        with self.dataset_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(
                file
            )

    def run(self):

        dataset = (
            self.load_dataset()
        )

        results = []

        for case in dataset:

            print(
                "\n"
                "================================"
            )

            print(
                f"Case: {case['id']}"
            )

            print(
                case["input"]
            )

            start = (
                time.perf_counter()
            )

            success = True
            error = None

            try:

                response = (
                    self.agent.run(
                        user_input=(
                            case["input"]
                        ),
                        user_role=(
                            case.get(
                                "role",
                                "employee",
                            )
                        ),
                    )
                )

                state = (
                    response["result"]
                )

            except Exception as exc:

                success = False

                error = str(exc)

                state = {}

            latency_ms = (
                time.perf_counter()
                - start
            ) * 1000

            observations = (
                state.get(
                    "observations",
                    [],
                )
            )

            actual_tools = [
                observation.get(
                    "tool"
                )
                for observation
                in observations
                if observation.get(
                    "tool"
                )
            ]

            expected_tools = (
                case.get(
                    "expected_tools",
                    [],
                )
            )

            if expected_tools:

                tool_match = all(
                    tool in actual_tools
                    for tool
                    in expected_tools
                )

            else:

                tool_match = True

            verification_status = (
                state.get(
                    "verification_status",
                    "",
                )
            )

            replan_count = (
                state.get(
                    "replan_count",
                    0,
                )
            )

            results.append(
                {
                    "id":
                        case["id"],

                    "success":
                        success,

                    "latency_ms":
                        latency_ms,

                    "expected_tools":
                        expected_tools,

                    "actual_tools":
                        actual_tools,

                    "tool_match":
                        tool_match,

                    "verification_status":
                        verification_status,

                    "replan_count":
                        replan_count,

                    "error":
                        error,
                }
            )

        self.save_results(
            results
        )

        summary = (
            self.build_summary(
                results
            )
        )

        self.save_summary(
            summary
        )

        print(
            "\nFinal workflow summary:"
        )

        print(
            json.dumps(
                summary,
                indent=2,
                ensure_ascii=False,
            )
        )

        return results, summary

    def build_summary(
        self,
        results: list[dict],
    ) -> dict:

        if not results:

            return {}

        total = len(
            results
        )

        successful = sum(
            1
            for result
            in results
            if result["success"]
        )

        tool_correct = sum(
            1
            for result
            in results
            if result["tool_match"]
        )

        latencies = [
            result["latency_ms"]
            for result
            in results
        ]

        replans = [
            result["replan_count"]
            for result
            in results
        ]

        return {
            "total_cases":
                total,

            "agent_success_rate":
                successful / total,

            "tool_selection_accuracy":
                tool_correct / total,

            "average_latency_ms":
                mean(latencies),

            "average_replans":
                mean(replans),
        }

    def save_results(
        self,
        results: list[dict],
    ):

        json_path = (
            self.output_dir
            / "results.json"
        )

        csv_path = (
            self.output_dir
            / "results.csv"
        )

        with json_path.open(
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

        dataframe = (
            pd.DataFrame(
                results
            )
        )

        dataframe.to_csv(
            csv_path,
            index=False,
            encoding="utf-8-sig",
        )

    def save_summary(
        self,
        summary: dict,
    ):

        path = (
            self.output_dir
            / "summary.json"
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                summary,
                file,
                ensure_ascii=False,
                indent=2,
            )