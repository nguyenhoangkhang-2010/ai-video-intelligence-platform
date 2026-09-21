from unittest.mock import MagicMock

from ai.knowledge_graph.knowledge_result import KnowledgeEntity
from ai.knowledge_graph.relation_extraction import RelationExtractor

ENTITY_A = KnowledgeEntity(
    id="id-a", label="Python", entity_type="TECHNOLOGY",
    aliases=("Py",),
)
ENTITY_B = KnowledgeEntity(
    id="id-b", label="Guido van Rossum", entity_type="PERSON",
)


def _extractor(response_text):
    llm_client = MagicMock()
    llm_client.generate.return_value = response_text
    return RelationExtractor(llm_client=llm_client)


def test_extract_returns_empty_list_for_fewer_than_two_entities():
    extractor = _extractor("[]")
    assert extractor.extract(text="content", entities=[ENTITY_A]) == []


def test_extract_parses_valid_relation_and_maps_to_entity_ids():
    response = """[
        {"source": "Python", "target": "Guido van Rossum",
         "relation_type": "created by", "evidence": "stated in text",
         "confidence": 0.8}
    ]"""
    extractor = _extractor(response)

    relations = extractor.extract(
        text="content", entities=[ENTITY_A, ENTITY_B],
    )

    assert len(relations) == 1
    relation = relations[0]
    assert relation.source_entity_id == "id-a"
    assert relation.target_entity_id == "id-b"
    assert relation.relation_type == "created by"
    assert relation.evidence == "stated in text"
    assert relation.confidence == 0.8


def test_extract_matches_entity_by_alias():
    response = '[{"source": "Py", "target": "Guido van Rossum", "relation_type": "created by"}]'
    extractor = _extractor(response)

    relations = extractor.extract(
        text="content", entities=[ENTITY_A, ENTITY_B],
    )

    assert len(relations) == 1
    assert relations[0].source_entity_id == "id-a"


def test_extract_rejects_dangling_relation_with_unknown_source():
    response = '[{"source": "Unknown Entity", "target": "Guido van Rossum", "relation_type": "created by"}]'
    extractor = _extractor(response)

    relations = extractor.extract(
        text="content", entities=[ENTITY_A, ENTITY_B],
    )

    assert relations == []


def test_extract_rejects_dangling_relation_with_unknown_target():
    response = '[{"source": "Python", "target": "Unknown Entity", "relation_type": "created by"}]'
    extractor = _extractor(response)

    relations = extractor.extract(
        text="content", entities=[ENTITY_A, ENTITY_B],
    )

    assert relations == []


def test_extract_rejects_self_referential_relation():
    response = '[{"source": "Python", "target": "Python", "relation_type": "same as"}]'
    extractor = _extractor(response)

    relations = extractor.extract(
        text="content", entities=[ENTITY_A, ENTITY_B],
    )

    assert relations == []


def test_extract_deduplicates_equivalent_relations():
    response = """[
        {"source": "Python", "target": "Guido van Rossum", "relation_type": "created by"},
        {"source": "Python", "target": "Guido van Rossum", "relation_type": "Created By"}
    ]"""
    extractor = _extractor(response)

    relations = extractor.extract(
        text="content", entities=[ENTITY_A, ENTITY_B],
    )

    assert len(relations) == 1


def test_extract_returns_empty_list_for_malformed_json():
    extractor = _extractor("not json")
    relations = extractor.extract(
        text="content", entities=[ENTITY_A, ENTITY_B],
    )
    assert relations == []


def test_extract_returns_empty_list_when_llm_raises():
    llm_client = MagicMock()
    llm_client.generate.side_effect = RuntimeError("boom")
    extractor = RelationExtractor(llm_client=llm_client)

    relations = extractor.extract(
        text="content", entities=[ENTITY_A, ENTITY_B],
    )
    assert relations == []
