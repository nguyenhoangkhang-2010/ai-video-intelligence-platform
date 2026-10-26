from unittest.mock import MagicMock

from ai.quiz_generation.true_false import TrueFalseGenerator


def _generator(response_text):
    llm_client = MagicMock()
    llm_client.generate.return_value = response_text
    return TrueFalseGenerator(llm_client=llm_client)


def test_generate_returns_empty_list_for_empty_text():
    generator = _generator("[]")
    assert generator.generate(text="", count=2) == []


def test_generate_parses_boolean_correct_answer():
    response = '[{"question": "The sky is blue.", "correct_answer": true, "explanation": "Observed fact."}]'
    generator = _generator(response)

    questions = generator.generate(text="content", count=1)

    assert len(questions) == 1
    assert questions[0].correct_answer == "True"
    assert questions[0].question_type == "true_false"
    assert questions[0].options == ("True", "False")


def test_generate_parses_string_true_false_correct_answer():
    response = '[{"question": "Statement A", "correct_answer": "false"}]'
    generator = _generator(response)

    questions = generator.generate(text="content", count=1)

    assert questions[0].correct_answer == "False"


def test_generate_drops_item_with_invalid_correct_answer_value():
    response = '[{"question": "Statement A", "correct_answer": "maybe"}]'
    generator = _generator(response)

    assert generator.generate(text="content", count=1) == []


def test_generate_drops_item_missing_question():
    response = '[{"correct_answer": true}]'
    generator = _generator(response)

    assert generator.generate(text="content", count=1) == []


def test_generate_returns_empty_list_for_malformed_json():
    generator = _generator("nonsense output")
    assert generator.generate(text="content", count=2) == []


def test_generate_returns_empty_list_when_llm_raises():
    llm_client = MagicMock()
    llm_client.generate.side_effect = RuntimeError("timeout")
    generator = TrueFalseGenerator(llm_client=llm_client)

    assert generator.generate(text="content", count=2) == []


def test_generate_deduplicates_identical_statements():
    response = """[
        {"question": "Same statement", "correct_answer": true},
        {"question": "Same statement", "correct_answer": true}
    ]"""
    generator = _generator(response)

    questions = generator.generate(text="content", count=5)

    assert len(questions) == 1
