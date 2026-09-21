import json
import time
from pathlib import Path
from statistics import mean, median

import pandas as pd

from app.rag.retriever import search_policy
from math import ceil


class RagEvaluator:
    def __init__(
        self,
        dataset_path: str = "evaluation/dataset.json",
        dataset_section: str = "rag_cases",
        output_dir: str = "outputs/evaluation/rag",
        top_k: int = 2,
    ):
        self.dataset_path = Path(dataset_path)
        self.dataset_section = dataset_section
        self.output_dir = Path(output_dir)
        self.top_k = top_k
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_dataset(self) -> list[dict]:
        with self.dataset_path.open("r", encoding="utf-8") as file:
            dataset = json.load(file)
        if isinstance(dataset, list):
            return dataset
        return dataset[self.dataset_section]

    def run(self) -> tuple[list[dict], dict]:
        results = []

        for case in self.load_dataset():
            start = time.perf_counter()
            error = None
            try:
                documents = search_policy(case["query"], top_k=self.top_k)
            except Exception as exc:
                documents = []
                error = str(exc)
            latency_ms = (time.perf_counter() - start) * 1000

            actual_sources = [document.get("source") for document in documents]
            expected_sources = set(case["expected_sources"])
            hit_ranks = [
                rank
                for rank, source in enumerate(actual_sources, start=1)
                if source in expected_sources
            ]
            retrieved_relevant = len(expected_sources & set(actual_sources))

            results.append(
                {
                    "id": case["id"],
                    "query": case["query"],
                    "expected_sources": sorted(expected_sources),
                    "actual_sources": actual_sources,
                    "hit_at_1": bool(hit_ranks and hit_ranks[0] == 1),
                    f"hit_at_{self.top_k}": bool(hit_ranks),
                    f"recall_at_{self.top_k}": retrieved_relevant / len(expected_sources),
                    f"reciprocal_rank_at_{self.top_k}": 1 / hit_ranks[0] if hit_ranks else 0.0,
                    "latency_ms": latency_ms,
                    "error": error,
                }
            )

        latencies = sorted(result["latency_ms"] for result in results)
        p95_index = max(0, ceil(len(latencies) * 0.95) - 1)
        summary = {
            "total_cases": len(results),
            "top_k": self.top_k,
            "hit_at_1": round(mean(result["hit_at_1"] for result in results), 4),
            f"hit_at_{self.top_k}": round(
                mean(result[f"hit_at_{self.top_k}"] for result in results), 4
            ),
            f"recall_at_{self.top_k}": round(
                mean(result[f"recall_at_{self.top_k}"] for result in results), 4
            ),
            f"mrr_at_{self.top_k}": round(
                mean(result[f"reciprocal_rank_at_{self.top_k}"] for result in results),
                4,
            ),
            "average_latency_ms": round(mean(latencies), 2),
            "p50_latency_ms": round(median(latencies), 2),
            "p95_latency_ms": round(latencies[p95_index], 2),
            "error_rate": round(mean(result["error"] is not None for result in results), 4),
        }

        with (self.output_dir / "results.json").open("w", encoding="utf-8") as file:
            json.dump(results, file, ensure_ascii=False, indent=2)
        with (self.output_dir / "summary.json").open("w", encoding="utf-8") as file:
            json.dump(summary, file, ensure_ascii=False, indent=2)
        pd.DataFrame(results).to_csv(
            self.output_dir / "results.csv",
            index=False,
            encoding="utf-8-sig",
        )

        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return results, summary
