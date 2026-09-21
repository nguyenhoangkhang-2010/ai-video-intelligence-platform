"""
Knowledge extraction domain logic: EntityExtractor, RelationExtractor,
GraphBuilder (see the sibling modules in this package), producing a
generic, data-driven KnowledgeGraphResult (entities/relations - never
a hardcoded entity/relation type list, see knowledge_result.py).

Deliberately NOT exposed via any API endpoint and NOT persisted to
the database as of this audit (backend-completion phase). Decision:

  - No KnowledgeEntity/KnowledgeRelation tables, no migration, and no
    new graph database (Neo4j or otherwise) were introduced. Building
    real persistence would mean a new pipeline stage (compute once
    during video processing, not on every read) plus new
    model/repository/service/schema/endpoint layers - a genuinely new
    capability, not a hardening of an existing one.
  - Computing the graph on-demand inside a GET handler was also
    rejected: EntityExtractor/RelationExtractor each call the LLM
    (Ollama) per chunk, so a synchronous "GET /videos/{id}/
    knowledge-graph" would be slow, non-deterministic between calls,
    and costly - not acceptable behavior for a read endpoint.
  - The domain implementation itself is complete and reusable as-is
    (GraphBuilder.build(chunks) -> KnowledgeGraphResult) whenever a
    future phase decides to add the pipeline stage + persistence this
    would need. Nothing here needs to change to support that later.

Do not add a new database, a new endpoint, or an on-demand-compute
endpoint for this without first adding real persistence - see the
"Knowledge Graph" section of docs/deployment.md and the backend
completion report for this decision's full rationale.
"""
