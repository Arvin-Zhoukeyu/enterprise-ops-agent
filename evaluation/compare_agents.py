import json
from pathlib import Path

import pandas as pd


BASELINE_PATH = Path(
    "outputs/evaluation/"
    "baseline/summary.json"
)

WORKFLOW_PATH = Path(
    "outputs/evaluation/"
    "workflow/summary.json"
)

OUTPUT_DIR = Path(
    "outputs/evaluation/"
    "comparison"
)


def load_json(
    path: Path,
):

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    baseline = load_json(
        BASELINE_PATH
    )

    workflow = load_json(
        WORKFLOW_PATH
    )

    comparison = {

        "metric": [
            "Agent Success Rate",
            "Tool Selection Accuracy",
            "Average Latency (ms)",
        ],

        "Baseline": [
            baseline.get(
                "agent_success_rate"
            ),

            baseline.get(
                "tool_selection_accuracy"
            ),

            baseline.get(
                "average_latency_ms"
            ),
        ],

        "Workflow": [
            workflow.get(
                "agent_success_rate"
            ),

            workflow.get(
                "tool_selection_accuracy"
            ),

            workflow.get(
                "average_latency_ms"
            ),
        ],
    }

    dataframe = (
        pd.DataFrame(
            comparison
        )
    )

    path = (
        OUTPUT_DIR
        / "comparison.csv"
    )

    dataframe.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        dataframe
    )


if __name__ == "__main__":
    main()