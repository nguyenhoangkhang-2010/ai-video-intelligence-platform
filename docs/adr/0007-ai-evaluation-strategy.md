# 0007 - Deterministic-first AI evaluation, model-based metrics opt-in, no hardcoded domain data

## Status
Accepted (implemented: `ai/evaluation/`, `scripts/run_evaluation.py`, `ai/evaluation/fixtures/golden_dataset.json`).

## Context
This product's AI output (retrieval, RAG answers, summaries/
translations/quiz content) needs a way to measure quality that's
reproducible in CI and doesn't require a live LLM, a GPU, or a
labeled dataset someone fabricated to make a number look good.

## Decision
Layer evaluation into three tiers, deliberately kept separate rather
than collapsed into one "quality score":

1. **Deterministic metrics** (Precision@K/Recall@K/MRR/NDCG for
   retrieval; ROUGE for generation; lexical-overlap faithfulness/
   relevance for RAG) - pure functions, no model, no network, always
   available. These run in CI today via a small, hand-authored,
   version-controlled regression dataset (`fixtures/golden_dataset.json`
   + `tests/ai/evaluation/test_golden_dataset.py`) that locks in the
   evaluation framework's own wiring (dataset -> `BenchmarkRunner` ->
   real metric classes), not this deployment's actual content quality.
2. **Model-based metrics** (BERTScore, an LLM judge) - real, 
   implemented, but lazily imported and never exercised in CI; they
   need a transformer model or a live Ollama instance, which CI
   intentionally never depends on.
3. **Real-deployment scoring** (`scripts/run_evaluation.py`) - scores
   THIS deployment's actual retrieval/RAG quality against a real,
   already-processed video, using ground-truth relevance judgments a
   human has to author by hand. The script refuses to ship a fake
   dataset for this - `fixtures/example_*.json` are schema templates
   with an explicit "fabricating this produces a meaningless score"
   warning, not a one is ever treated as real data.

Every evaluation data structure (`ai/evaluation/models.py`) is generic
over IDs/text/scores - nothing in the evaluation framework itself
knows what a video, a company, or a job title is.

## Consequences
- CI gets fast, deterministic, meaningful regression coverage of the
  evaluation code itself with zero flakiness and zero external
  dependency.
- This deployment's *actual* retrieval/RAG quality is never measured
  automatically - it requires a person to run the script against a
  real video and author real relevance judgments. This is a
  deliberate cost: an automated "quality score" built from fabricated
  or synthetic ground truth would be actively misleading, not merely
  incomplete.
- Model-based metrics (BERTScore, LLM judge) exist and are tested in
  isolation, but nothing currently runs them on a schedule - revisit
  if/when a GPU-backed CI runner or a dedicated eval environment
  exists.
