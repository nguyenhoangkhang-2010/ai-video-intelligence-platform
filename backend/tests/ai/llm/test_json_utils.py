from ai.llm.json_utils import extract_json


def test_extract_json_parses_plain_json_array():
    result = extract_json('[{"a": 1}, {"a": 2}]')
    assert result == [{"a": 1}, {"a": 2}]


def test_extract_json_parses_json_wrapped_in_markdown_fence():
    text = '```json\n[{"a": 1}]\n```'
    assert extract_json(text) == [{"a": 1}]


def test_extract_json_parses_fence_without_json_language_tag():
    text = '```\n{"a": 1}\n```'
    assert extract_json(text) == {"a": 1}


def test_extract_json_extracts_object_from_surrounding_commentary():
    text = 'Sure, here is the result:\n{"a": 1}\nHope that helps!'
    assert extract_json(text) == {"a": 1}


def test_extract_json_returns_none_for_empty_text():
    assert extract_json("") is None
    assert extract_json("   ") is None


def test_extract_json_returns_none_for_malformed_json():
    assert extract_json("this is not json at all") is None


def test_extract_json_returns_none_for_truncated_json():
    assert extract_json('[{"a": 1}, {"a": 2}') is None
