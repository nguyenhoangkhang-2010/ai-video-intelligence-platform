# Real RAG Retrieval Evaluation

Run on 2026-10-07, against the real dev database and the real,
unmodified retrieval stack. This is **not** the synthetic regression
fixture (`ai/evaluation/fixtures/golden_dataset.json`) that proves the
evaluation framework's own math is correct and runs in CI
(`tests/ai/evaluation/test_golden_dataset.py`) - this is a one-off,
manually-run measurement of this deployment's *actual* retrieval
quality, using real content.

## Dataset

- 6 real documents: the actual transcript text stored for 6 of this
  deployment's real processed videos (`backend/ai/evaluation/fixtures/real_ground_truth.json`),
  pulled directly from the dev database via `EmbeddingRepository` on
  the day this was run.
- 10 real queries, hand-authored after actually reading each
  transcript, including one deliberate negative control (a query with
  no relevant document in the pool, to check retrievers don't force a
  confident-looking wrong answer) and one genuine duplicate-content
  case (two videos share byte-identical transcript text).
- Content is short-form Vietnamese motivational/quote clips (9-76
  seconds each) - this project's real dev data has no long-form video
  that produces more than one embedding chunk per video, so there is
  no real multi-chunk, within-video ranking scenario to evaluate yet.

## Methodology

The product's real retrieval classes (`DenseRetriever`,
`SparseRetriever`, `HybridRetriever`, `RetrievalPipeline`,
`CrossEncoderReranker`) are used completely unmodified. Only the
data-access layer is substituted: a shim `EmbeddingRepository`
(`backend/scripts/benchmark_rag_retrieval.py::_PooledEmbeddingRepository`)
returns the same 6 real embedding rows for any `video_id`, so the
real, globally-shared FAISS index (confirmed in
[ADR 0008](../adr/0008-vector-retrieval-architecture.md) to already
hold every video's vectors together) is queried across all 6 real
documents at once instead of filtered down to one video - a genuine
cross-document retrieval test, standing in for the within-video
ranking this dataset can't exercise. No retrieval, ranking, or
reranking code was changed to produce these numbers.

**This is a small, exploratory measurement, not a statistically
significant one.** 10 queries over 6 documents is nowhere near enough
to draw confident conclusions - every number below should be read as
"this is what actually happened on this real, small sample," not "this
proves X is better than Y in general."

## Results (Precision@5 / Recall@5 / MRR / NDCG@5, top_k=5)

| Metric | Dense only | Sparse only (BM25) | Hybrid (RRF) | Hybrid + reranking |
|---|---:|---:|---:|---:|
| precision@5 | 0.200 | 0.250 | 0.200 | 0.200 |
| recall@5 | 0.900 | 0.900 | 0.900 | 0.900 |
| mrr | 0.900 | 0.900 | 0.900 | 0.850 |
| ndcg@5 | 0.900 | 0.900 | 0.900 | 0.863 |
| avg query latency (s) | 0.534 | 0.001 | 0.147 | 0.515 |

## Interpretation

- **Precision@5's ~0.2 ceiling is a dataset artifact, not a quality
  signal**: with only 6 total documents and `top_k=5`, almost every
  query (9 of 10 have exactly one truly relevant document) can score
  at best 1/5 = 0.200 on precision@5 by construction - there simply
  aren't enough irrelevant-but-plausible documents in the pool for
  precision to mean anything at this `top_k`. This would need a much
  larger document pool to be a meaningful number.
- **Recall@5 = 0.900 for dense/sparse/hybrid is actually a perfect
  score**: one of the 10 queries is the deliberate negative control
  (no relevant document exists), which contributes exactly 0.0 to
  recall for every retriever by definition (`recall_at_k` returns 0.0
  when `relevant_ids` is empty) - 9/10 = 0.900 is the maximum any
  retriever could score, and dense/sparse/hybrid all hit it.
- **BM25 (sparse-only) matched or slightly beat dense/hybrid on this
  sample.** Plausible real reason: these are short, keyword-dense
  Vietnamese quotes where exact lexical overlap between query and
  transcript is already a strong signal - not evidence that sparse
  retrieval is generally better, just what happened on these 10
  queries.
- **Reranking measurably hurt MRR and NDCG on this real sample**
  (0.900 → 0.850 / 0.863). The real, honest explanation: this
  deployment's configured reranker
  (`cross-encoder/ms-marco-MiniLM-L-6-v2`, `settings.retrieval.cross_encoder_model`)
  is an English-tuned model, and this content is Vietnamese. This is
  a genuine finding, not a benchmark artifact - it suggests the
  current reranker may not be the right choice for this deployment's
  actual (non-English) content, and is worth a real follow-up decision
  (a multilingual cross-encoder, or disabling reranking for non-English
  content) rather than something to quietly ignore.
- **Latency**: sparse (BM25, in-memory, no model) is ~500x faster per
  query than dense (which pays a BGE-M3 embedding inference cost) or
  reranking (a second model forward pass). Hybrid sits between them
  (still pays the dense cost, plus a cheap BM25 pass and RRF fusion -
  no extra model inference). These are single-process, single-request,
  unloaded-system numbers - see `docs/benchmarks/performance.md` for
  load-bearing, concurrent measurements.

## Limitations

- 10 queries, 6 documents - far too small to generalize from.
- All content is short-form (<80s) Vietnamese text; no long-form,
  multi-chunk, or English-language content was evaluated.
- The "cross-document" framing is a deliberate benchmark construction
  to get *some* real ranking signal out of this deployment's actual
  (very short) real videos - it does not reflect the product's real
  per-request behavior, which is always scoped to one video.
- This was run once, on one machine, with the models already warm in
  the container's page cache - no variance/repeat-run statistics were
  collected.

## How to reproduce

```bash
# from backend/, inside the dev container
python scripts/benchmark_rag_retrieval.py
```
