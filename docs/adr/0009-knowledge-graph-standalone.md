# 0009 - Knowledge graph extraction kept standalone, not wired into the mandatory pipeline

## Status
Accepted.

## Context
`ai/knowledge_graph/` implements entity extraction, relation
extraction, and graph building, with real unit tests
(`tests/ai/knowledge_graph/`). It is not referenced anywhere in
`app/pipelines/stage_definitions.py` or `video_pipeline.py` - every
video's mandatory 8-stage pipeline runs without it.

## Decision
Keep it that way. There is no evidenced product requirement today
for every uploaded video to produce a knowledge graph - adding it as
a 9th mandatory stage would mean every upload pays its compute cost
(entity/relation extraction over the full transcript) for a feature
nothing in the product currently surfaces or consumes.

## Consequences
- The module exists, is tested, and is ready to be wired in as an
  explicit, optional stage (or an on-demand endpoint) the moment a
  real feature needs it - this is deliberately not "unused dead
  code," it's a capability built ahead of its integration.
- Until something consumes it, it adds test-maintenance cost (keeping
  `tests/ai/knowledge_graph/` passing as its dependencies evolve) with
  no corresponding product value - worth revisiting (either wire it
  in, or remove it) if it sits unconsumed for long enough that its
  upkeep cost stops being justified by "ready when needed."
