from unittest.mock import MagicMock

from ai.quiz_generation.short_answer import ShortAnswerGenerator


def _generator(response_text):
    llm_client = MagicMock()
    llm_client.generate.return_value = response_text
    return ShortAnswerGenerator(llm_client=llm_client)


def test_generate_returns_empty_list_for_empty_text():
    generator = _generator("[]")
    assert generator.generate(text="", count=2) == []


def test_generate_parses_valid_short_answer_json():
    response = '[{"question": "What is the capital?", "correct_answer": "Hanoi", "explanation": "Stated directly."}]'
    generator = _generator(response)

    questions = generator.generate(text="content", count=1)

    assert len(questions) == 1
    assert questions[0].question == "What is the capital?"
    assert questions[0].correct_answer == "Hanoi"
    assert questions[0].question_type == "short_answer"
    assert questions[0].options is None


def test_generate_drops_item_with_empty_answer():
    response = '[{"question": "Q?", "correct_answer": "   "}]'
    generator = _generator(response)

    assert generator.generate(text="content", count=1) == []


def test_generate_drops_item_missing_answer_field():
    response = '[{"question": "Q?"}]'
    generator = _generator(response)

    assert generator.generate(text="content", count=1) == []


def test_generate_returns_empty_list_for_malformed_json():
    generator = _generator("not json")
    assert generator.generate(text="content", count=2) == []


def test_generate_returns_empty_list_when_llm_raises():
    llm_client = MagicMock()
    llm_client.generate.side_effect = RuntimeError("boom")
    generator = ShortAnswerGenerator(llm_client=llm_client)

    assert generator.generate(text="content", count=2) == []


def test_generate_deduplicates_identical_questions():
    response = """[
        {"question": "Same?", "correct_answer": "A"},
        {"question": "Same?", "correct_answer": "A"}
    ]"""
    generator = _generator(response)

    assert len(generator.generate(text="content", count=5)) == 1
