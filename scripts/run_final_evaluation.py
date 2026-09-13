import argparse

from evaluation.workflow_evaluator import (
    WorkflowEvaluator,
)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default="evaluation/dataset.json",
    )
    parser.add_argument(
        "--section",
        default="common_agent_cases",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/evaluation/workflow",
    )
    args = parser.parse_args()

    evaluator = (
        WorkflowEvaluator(
            dataset_path=args.dataset,
            dataset_section=args.section,
            output_dir=args.output_dir,
        )
    )

    evaluator.run()


if __name__ == "__main__":
    main()
