from evaluation.evaluator import (
    BaselineEvaluator,
)


def main():

    evaluator = (
        BaselineEvaluator()
    )

    evaluator.run()


if __name__ == "__main__":
    main()