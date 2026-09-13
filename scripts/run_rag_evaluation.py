import argparse

from evaluation.rag_evaluator import RagEvaluator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="evaluation/dataset.json")
    parser.add_argument("--section", default="rag_cases")
    parser.add_argument("--output-dir", default="outputs/evaluation/rag")
    parser.add_argument("--top-k", type=int, default=2)
    args = parser.parse_args()

    evaluator = RagEvaluator(
        dataset_path=args.dataset,
        dataset_section=args.section,
        output_dir=args.output_dir,
        top_k=args.top_k,
    )
    evaluator.run()


if __name__ == "__main__":
    main()
