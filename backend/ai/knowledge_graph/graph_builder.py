"""Orchestrates entity + relation extraction into a KnowledgeGraphResult."""
import logging

from ai.knowledge_graph.entity_extraction import EntityExtractor
from ai.knowledge_graph.knowledge_result import (
    KnowledgeEntity,
    KnowledgeGraphResult,
    KnowledgeRelation,
)
from ai.knowledge_graph.relation_extraction import RelationExtractor
from ai.llm.ollama_client import OllamaClient
from app.config.settings import settings

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Builds a generic KnowledgeGraphResult from one or more chunks of
    source text (e.g. per-chapter transcript spans). Collects entities
    across chunks, deduplicates them by their deterministic ID,
    extracts relations per chunk against that chunk's own entities,
    and validates the final relation set against the fully merged
    entity set so no relation can reference an entity that was later
    dropped (e.g. by the confidence threshold).

    Does not persist to any graph database - no such persistence layer
    exists yet in this project, so the result is kept purely in-memory/
    domain-level for reuse by a later persistence phase.
    """

    def __init__(
        self,
        llm_client: OllamaClient | None = None,
        entity_extractor: EntityExtractor | None = None,
        relation_extractor: RelationExtractor | None = None,
    ):
        shared_client = llm_client or OllamaClient()

        self.entity_extractor = entity_extractor or EntityExtractor(
            llm_client=shared_client,
        )
        self.relation_extractor = relation_extractor or RelationExtractor(
            llm_client=shared_client,
        )

    def build(
        self,
        chunks: list[str],
        chunk_segment_ids: list[tuple[int, ...]] | None = None,
    ) -> KnowledgeGraphResult:
        if not chunks:
            return KnowledgeGraphResult(entities=(), relations=())

        if chunk_segment_ids is None:
            chunk_segment_ids = [() for _ in chunks]

        if not settings.knowledge_graph.enabled:
            logger.info(
                "Knowledge graph LLM generation disabled; returning an "
                "empty graph.",
            )
            return KnowledgeGraphResult(entities=(), relations=())

        entities_by_id: dict[str, KnowledgeEntity] = {}
        relations: list[KnowledgeRelation] = []
        seen_relation_keys: set[tuple[str, str, str]] = set()

        for chunk_text, segment_ids in zip(chunks, chunk_segment_ids):
            if not chunk_text or not chunk_text.strip():
                continue

            chunk_entities = self.entity_extractor.extract(
                text=chunk_text,
                source_segment_ids=segment_ids,
            )
            chunk_entities = [
                entity
                for entity in chunk_entities
                if _passes_confidence(entity.confidence)
            ]

            for entity in chunk_entities:
                existing = entities_by_id.get(entity.id)
                entities_by_id[entity.id] = (
                    entity if existing is None else _merge(existing, entity)
                )

            if len(chunk_entities) < 2:
                continue

            chunk_relations = self.relation_extractor.extract(
                text=chunk_text,
                entities=chunk_entities,
                source_segment_ids=segment_ids,
            )

            for relation in chunk_relations:
                if not _passes_confidence(relation.confidence):
                    continue

                key = (
                    relation.source_entity_id,
                    relation.target_entity_id,
                    relation.relation_type.strip().lower(),
                )
                if key in seen_relation_keys:
                    continue
                seen_relation_keys.add(key)
                relations.append(relation)

        # Final validation pass: drop any relation whose endpoints did
        # not survive into the merged entity set (e.g. filtered out by
        # confidence threshold above).
        valid_relations = tuple(
            relation
            for relation in relations
            if relation.source_entity_id in entities_by_id
            and relation.target_entity_id in entities_by_id
        )

        return KnowledgeGraphResult(
            entities=tuple(entities_by_id.values()),
            relations=valid_relations,
            metadata={"chunk_count": len(chunks)},
        )


def _passes_confidence(
    confidence: float | None,
) -> bool:
    if confidence is None:
        return True
    return confidence >= settings.knowledge_graph.min_confidence


def _merge(
    existing: KnowledgeEntity,
    new: KnowledgeEntity,
) -> KnowledgeEntity:
    merged_aliases = tuple(
        dict.fromkeys(existing.aliases + new.aliases),
    )
    merged_segment_ids = tuple(
        dict.fromkeys(existing.source_segment_ids + new.source_segment_ids),
    )
    return KnowledgeEntity(
        id=existing.id,
        label=existing.label,
        entity_type=existing.entity_type,
        aliases=merged_aliases,
        description=existing.description or new.description,
        source_segment_ids=merged_segment_ids,
        confidence=(
            max(existing.confidence, new.confidence)
            if existing.confidence is not None and new.confidence is not None
            else existing.confidence or new.confidence
        ),
    )
