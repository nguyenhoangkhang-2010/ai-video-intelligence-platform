from unittest.mock import MagicMock

from ai.knowledge_graph.graph_builder import GraphBuilder
from ai.knowledge_graph.knowledge_result import KnowledgeEntity, KnowledgeRelation

ENTITY_A = KnowledgeEntity(id="id-a", label="Python", entity_type="TECHNOLOGY")
ENTITY_B = KnowledgeEntity(id="id-b", label="Guido", entity_type="PERSON")


def _builder(entity_extractor=None, relation_extractor=None):
    entity_extractor = entity_extractor or MagicMock()
    relation_extractor = relation_extractor or MagicMock()
    builder = GraphBuilder(
        llm_client=MagicMock(),
        entity_extractor=entity_extractor,
        relation_extractor=relation_extractor,
    )
    return builder, entity_extractor, relation_extractor


def test_build_returns_empty_graph_for_no_chunks():
    builder, entity_extractor, relation_extractor = _builder()

    result = builder.build(chunks=[])

    assert result.entities == ()
    assert result.relations == ()
    entity_extractor.extract.assert_not_called()


def test_build_merges_entities_across_chunks_by_deterministic_id():
    entity_extractor = MagicMock()
    entity_extractor.extract.side_effect = [
        [ENTITY_A],
        [ENTITY_A],
    ]
    relation_extractor = MagicMock()
    relation_extractor.extract.return_value = []

    builder, _, _ = _builder(entity_extractor, relation_extractor)

    result = builder.build(chunks=["chunk one", "chunk two"])

    assert len(result.entities) == 1
    assert result.entities[0].id == "id-a"


def test_build_produces_no_dangling_relations():
    entity_extractor = MagicMock()
    entity_extractor.extract.return_value = [ENTITY_A, ENTITY_B]

    relation_extractor = MagicMock()
    relation_extractor.extract.return_value = [
        KnowledgeRelation(
            source_entity_id="id-a", target_entity_id="id-b",
            relation_type="created by",
        ),
        KnowledgeRelation(
            source_entity_id="id-a", target_entity_id="id-nonexistent",
            relation_type="bogus",
        ),
    ]

    builder, _, _ = _builder(entity_extractor, relation_extractor)

    result = builder.build(chunks=["chunk with two entities"])

    assert len(result.relations) == 1
    assert result.relations[0].target_entity_id == "id-b"

    entity_ids = {entity.id for entity in result.entities}
    for relation in result.relations:
        assert relation.source_entity_id in entity_ids
        assert relation.target_entity_id in entity_ids


def test_build_deduplicates_equivalent_relations_across_chunks():
    entity_extractor = MagicMock()
    entity_extractor.extract.return_value = [ENTITY_A, ENTITY_B]

    relation = KnowledgeRelation(
        source_entity_id="id-a", target_entity_id="id-b",
        relation_type="created by",
    )
    relation_extractor = MagicMock()
    relation_extractor.extract.return_value = [relation]

    builder, _, _ = _builder(entity_extractor, relation_extractor)

    result = builder.build(chunks=["chunk one", "chunk two"])

    assert len(result.relations) == 1


def test_build_skips_relation_extraction_when_fewer_than_two_entities():
    entity_extractor = MagicMock()
    entity_extractor.extract.return_value = [ENTITY_A]

    relation_extractor = MagicMock()

    builder, _, _ = _builder(entity_extractor, relation_extractor)

    builder.build(chunks=["chunk with one entity"])

    relation_extractor.extract.assert_not_called()


def test_build_skips_empty_chunks():
    entity_extractor = MagicMock()
    relation_extractor = MagicMock()

    builder, _, _ = _builder(entity_extractor, relation_extractor)

    builder.build(chunks=["   ", ""])

    entity_extractor.extract.assert_not_called()


def test_build_passes_chunk_segment_ids_through_to_entities():
    entity_extractor = MagicMock()
    entity_extractor.extract.return_value = [ENTITY_A]
    relation_extractor = MagicMock()

    builder, _, _ = _builder(entity_extractor, relation_extractor)

    builder.build(
        chunks=["chunk one"],
        chunk_segment_ids=[(5, 6)],
    )

    call_kwargs = entity_extractor.extract.call_args.kwargs
    assert call_kwargs["source_segment_ids"] == (5, 6)
