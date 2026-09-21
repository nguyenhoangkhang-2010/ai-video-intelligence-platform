from unittest.mock import MagicMock

from ai.knowledge_graph.entity_extraction import EntityExtractor, make_entity_id


def _extractor(response_text):
    llm_client = MagicMock()
    llm_client.generate.return_value = response_text
    return EntityExtractor(llm_client=llm_client)


def test_extract_returns_empty_list_for_empty_text():
    extractor = _extractor("[]")
    assert extractor.extract(text="   ") == []


def test_extract_parses_valid_entities():
    response = """[
        {"label": "Python", "entity_type": "TECHNOLOGY",
         "aliases": ["Python 3"], "description": "A programming language.",
         "confidence": 0.9}
    ]"""
    extractor = _extractor(response)

    entities = extractor.extract(text="some content about Python")

    assert len(entities) == 1
    entity = entities[0]
    assert entity.label == "Python"
    assert entity.entity_type == "TECHNOLOGY"
    assert entity.aliases == ("Python 3",)
    assert entity.description == "A programming language."
    assert entity.confidence == 0.9


def test_extract_drops_item_missing_label():
    response = '[{"entity_type": "CONCEPT"}]'
    extractor = _extractor(response)

    assert extractor.extract(text="content") == []


def test_extract_drops_item_missing_entity_type():
    response = '[{"label": "Something"}]'
    extractor = _extractor(response)

    assert extractor.extract(text="content") == []


def test_extract_returns_empty_list_for_malformed_json():
    extractor = _extractor("not json")
    assert extractor.extract(text="content") == []


def test_extract_returns_empty_list_when_llm_raises():
    llm_client = MagicMock()
    llm_client.generate.side_effect = RuntimeError("boom")
    extractor = EntityExtractor(llm_client=llm_client)

    assert extractor.extract(text="content") == []


def test_extract_deduplicates_same_entity_by_normalized_identity():
    response = """[
        {"label": "Python", "entity_type": "TECHNOLOGY"},
        {"label": "  python  ", "entity_type": "technology"}
    ]"""
    extractor = _extractor(response)

    entities = extractor.extract(text="content")

    assert len(entities) == 1


def test_extract_merges_aliases_and_descriptions_on_duplicate():
    response = """[
        {"label": "Python", "entity_type": "TECHNOLOGY",
         "aliases": ["py"]},
        {"label": "python", "entity_type": "TECHNOLOGY",
         "aliases": ["python3"], "description": "A language."}
    ]"""
    extractor = _extractor(response)

    entities = extractor.extract(text="content")

    assert len(entities) == 1
    entity = entities[0]
    assert set(entity.aliases) == {"py", "python3"}
    assert entity.description == "A language."


def test_extract_assigns_source_segment_ids():
    response = '[{"label": "X", "entity_type": "CONCEPT"}]'
    extractor = _extractor(response)

    entities = extractor.extract(text="content", source_segment_ids=(3, 4))

    assert entities[0].source_segment_ids == (3, 4)


def test_make_entity_id_is_deterministic_for_same_normalized_identity():
    id1 = make_entity_id("Python", "TECHNOLOGY")
    id2 = make_entity_id("  python  ", "technology")

    assert id1 == id2


def test_make_entity_id_differs_for_different_entity_types():
    id1 = make_entity_id("Python", "TECHNOLOGY")
    id2 = make_entity_id("Python", "PERSON")

    assert id1 != id2
