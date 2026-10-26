"""
Generic, domain-agnostic knowledge graph representations.

Entity/relation types are free-form strings supplied by the LLM, not a
fixed enum - the architecture must support arbitrary domains, so no
type value (e.g. PERSON, CONCEPT, TECHNOLOGY) is ever special-cased in
code; such values only ever appear as examples in prompts.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgeEntity:
    """A single extracted, normalized entity."""

    id: str
    label: str
    entity_type: str
    aliases: tuple[str, ...] = field(default_factory=tuple)
    description: str | None = None
    source_segment_ids: tuple[int, ...] = field(default_factory=tuple)
    confidence: float | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeRelation:
    """A directed relation between two already-extracted entities."""

    source_entity_id: str
    target_entity_id: str
    relation_type: str
    evidence: str | None = None
    source_segment_ids: tuple[int, ...] = field(default_factory=tuple)
    confidence: float | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeGraphResult:
    """The full extracted knowledge graph for a piece of source content."""

    entities: tuple[KnowledgeEntity, ...]
    relations: tuple[KnowledgeRelation, ...]
    metadata: dict = field(default_factory=dict)
