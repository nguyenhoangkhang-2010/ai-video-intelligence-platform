"""
Compare rerankers on Vietnamese: does a multilingual cross-encoder
rank the right passage first more often than the English MS MARCO
model the RAG pipeline originally shipped with?

Motivation: docs/benchmarks/rag-evaluation.md found the English-tuned
reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) measurably hurt
ranking on this project's real Vietnamese transcripts - but on only 10
queries. This measures the same question on a large, human-labelled
Vietnamese dataset: UIT-ViQuAD 2.0 (questions written by people about
Vietnamese Wikipedia passages). See ai.evaluation.reranking_benchmark
for how each question becomes a ranking task.

Run from backend/ (PYTHONPATH covering `app` and `ai`). The first run
downloads the dataset and each model from the Hugging Face Hub:

    python scripts/benchmark_reranker_vi.py --tasks 500 \
        --report ../docs/benchmarks/reranker-vi.md

Pick models with --models (comma-separated sentence-transformers
CrossEncoder names). The winner can be switched on in the app with the
existing CROSS_ENCODER_MODEL setting - no code change needed.
"""
import argparse
import json
import platform
import time
from datetime import date
from pathlib import Path

from ai.evaluation.reranking_benchmark import (
    SystemScore,
    bm25_scorer,
    build_ranking_tasks,
    rank,
)


DATASET = "taidng/UIT-ViQuAD2.0"
DEFAULT_MODELS = ",".join(
    [
        "cross-encoder/ms-marco-MiniLM-L-6-v2",  # previous default (English)
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",  # current default (multilingual)
        "BAAI/bge-reranker-v2-m3",  # multilingual, larger
    ]
)


def load_records(split: str) -> list[dict]:
    from datasets import load_dataset

    return list(load_dataset(DATASET, split=split))


def cross_encoder_scorer(model_name: str, batch_size: int):
    from sentence_transformers import CrossEncoder

    model = CrossEncoder(model_name, max_length=512)

    def score(query, texts):
        return list(model.predict([(query, text) for text in texts], batch_size=batch_size))

    return score


def evaluate(name: str, scorer, tasks) -> SystemScore:
    result = SystemScore(name=name)
    started = time.perf_counter()
    for index, task in enumerate(tasks, start=1):
        result.add(rank(task, scorer), task.relevant_id)
        if index % 100 == 0:
            print(f"  {name}: {index}/{len(tasks)}")
    result.seconds = round(time.perf_counter() - started, 1)
    return result


def render_report(results: list[SystemScore], tasks: int, candidates: int, split: str) -> str:
    lines = [
        "# Vietnamese reranking (UIT-ViQuAD 2.0)",
        "",
        f"Measured {date.today().isoformat()} with `scripts/benchmark_reranker_vi.py` on {tasks} "
        f"answerable questions from the `{split}` split of `{DATASET}`, each ranked against "
        f"{candidates} candidate passages (its own passage plus others from the same article first). "
        f"CPU: {platform.processor() or platform.machine()}.",
        "",
        "MRR = mean reciprocal rank of the correct passage; Recall@1 = how often it is ranked first; "
        "nDCG@5 over the top five. Time is total ranking time for all questions.",
        "",
        "| System | MRR | Recall@1 | nDCG@5 | Time (s) |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        lines.append(
            f"| `{result.name}` | {result.mrr:.3f} | {result.recall_at_1:.1%} | "
            f"{result.ndcg_at_5:.3f} | {result.seconds} |"
        )
    lines += [
        "",
        "Passages are Wikipedia text, not speech transcripts, so absolute scores will differ on "
        "video content; the comparison between models is the point. Switch the app's reranker "
        "with `CROSS_ENCODER_MODEL=<model>`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--tasks", type=int, default=500, help="number of questions to evaluate")
    parser.add_argument("--candidates", type=int, default=10, help="passages ranked per question")
    parser.add_argument("--models", default=DEFAULT_MODELS)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    print(f"Loading {DATASET} ({args.split})...")
    tasks = build_ranking_tasks(
        load_records(args.split),
        candidates_per_task=args.candidates,
        max_tasks=args.tasks,
        seed=args.seed,
    )
    print(f"{len(tasks)} ranking tasks")

    results = [evaluate("BM25 (lexical baseline)", bm25_scorer, tasks)]
    for model_name in [name.strip() for name in args.models.split(",") if name.strip()]:
        print(f"Loading {model_name}...")
        results.append(evaluate(model_name, cross_encoder_scorer(model_name, args.batch_size), tasks))
        print(f"  MRR {results[-1].mrr:.3f}  R@1 {results[-1].recall_at_1:.1%}")

    report = render_report(results, len(tasks), args.candidates, args.split)
    print()
    print(report)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    if args.json:
        args.json.write_text(
            json.dumps(
                [
                    {"system": r.name, "mrr": r.mrr, "recall_at_1": r.recall_at_1,
                     "ndcg_at_5": r.ndcg_at_5, "seconds": r.seconds, "tasks": r.tasks}
                    for r in results
                ],
                indent=2,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
