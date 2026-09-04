from evaluation.workflow_evaluator import (
    WorkflowEvaluator,
)


def main():

    evaluator = (
        WorkflowEvaluator()
    )

    evaluator.run()


if __name__ == "__main__":
    main()