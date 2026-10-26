# Vietnamese reranking (UIT-ViQuAD 2.0)

**Finding:** the English-only reranker this project originally shipped with
(`cross-encoder/ms-marco-MiniLM-L-6-v2`) ranks Vietnamese passages **worse
than plain BM25**. A small multilingual cross-encoder fixes that. It puts the
correct passage first 95.0% of the time, against 75.6% for the English model.

This confirms on 500 human-written questions what
[rag-evaluation.md](rag-evaluation.md) suggested from only 10 queries on the
project's own transcripts: the English reranker hurt ranking.

## Setup

- **Data.** 500 answerable questions sampled with seed 13 from the
  `validation` split of [`taidng/UIT-ViQuAD2.0`](https://huggingface.co/datasets/taidng/UIT-ViQuAD2.0).
  People wrote these questions about Vietnamese Wikipedia passages.
- **Task.** Each question is ranked against 10 candidate passages:
  - its own passage, which is the correct one;
  - other passages from the same article, which make hard negatives (same
    topic, wrong passage);
  - passages from other articles, used to fill the 10 slots only when the
    article has too few.

  Candidate order is shuffled. This isolates the reranking step of the RAG
  pipeline.
- **Metrics.** MRR, Recall@1 and nDCG@5. They come from the same
  implementation the rest of the evaluation framework uses
  (`ai/evaluation/metrics/retrieval.py`).
- **Hardware.** CPU only: Intel Core 12th gen (Family 6 Model 154), no GPU.
  Run on 2026-10-26.

Reproduce from `backend/`:

```bash
python scripts/benchmark_reranker_vi.py --tasks 500 --report ../docs/benchmarks/reranker-vi.md
```

## Results

| System | MRR | Recall@1 | nDCG@5 | Time for 500 questions |
|---|---|---|---|---|
| BM25 (lexical baseline) | 0.935 | 88.8% | 0.950 | 0.6 s |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` (previous default, English) | 0.848 | 75.6% | 0.876 | 271 s |
| `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (multilingual, ~118M params) | 0.972 | 95.0% | 0.979 | 494 s |
| `BAAI/bge-reranker-v2-m3` (multilingual, ~568M params) | **0.984** | **97.0%** | **0.987** | 5150 s* |

\* The bge run overlapped with a Whisper benchmark on the same CPU. Its time is
inflated, but it is still by far the slowest model.

## What it means

- **An English cross-encoder is a regression for Vietnamese.** It loses 13
  points of Recall@1 to BM25. Reranking is only worth its cost when the model
  understands the language.
- **`mmarco-mMiniLMv2-L12-H384-v1` is the practical choice on CPU.** It removes
  about 55% of BM25's first-place errors: 11.2% of questions misranked become
  5.0%. It takes roughly 1 s per query for 10 candidates.
- **`bge-reranker-v2-m3` is the most accurate model.** It gains another 2
  points of Recall@1, but it is about 10× slower and a 2.3 GB download. Use it
  when a GPU is available.

To switch models, change the existing `CROSS_ENCODER_MODEL` setting. No code
change is needed:

```env
CROSS_ENCODER_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
```

## Limits

- The passages are Wikipedia prose, not speech transcripts. Absolute scores on
  video content will be lower, because transcripts have recognition errors and
  no punctuation. Read the results as a comparison between models.
- The candidate sets are small (10 passages). The full pipeline reranks the
  hybrid retriever's top-k, so first-stage recall also matters. That is
  measured separately in [rag-evaluation.md](rag-evaluation.md), and
  `scripts/benchmark_rag_retrieval.py --reranker-models ...` runs the same
  comparison end to end on a project fixture.

## Decision

The default `CROSS_ENCODER_MODEL` is now
`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, set in
`app/config/settings.py`, `.env.example` and `.env.production`.
