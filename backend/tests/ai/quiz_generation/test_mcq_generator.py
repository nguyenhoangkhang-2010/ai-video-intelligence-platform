from unittest.mock import MagicMock

from ai.quiz_generation.mcq import MCQGenerator


def _generator(response_text):
    llm_client = MagicMock()
    llm_client.generate.return_value = response_text
    return MCQGenerator(llm_client=llm_client), llm_client


def test_generate_returns_empty_list_for_empty_text():
    generator, _ = _generator("[]")
    assert generator.generate(text="   ", count=3) == []


def test_generate_returns_empty_list_for_zero_count():
    generator, llm_client = _generator("[]")
    assert generator.generate(text="some text", count=0) == []
    llm_client.generate.assert_not_called()


def test_generate_parses_valid_mcq_json():
    response = """[
        {"question": "What is 2+2?", "options": ["3", "4", "5", "6"],
         "correct_answer": "4", "explanation": "Basic arithmetic."}
    ]"""
    generator, _ = _generator(response)

    questions = generator.generate(text="some math content", count=1)

    assert len(questions) == 1
    q = questions[0]
    assert q.question == "What is 2+2?"
    assert q.question_type == "multiple_choice"
    assert q.correct_answer == "4"
    assert q.options == ("3", "4", "5", "6")
    assert q.explanation == "Basic arithmetic."


def test_generate_drops_question_when_correct_answer_not_in_options():
    response = """[
        {"question": "Bad question", "options": ["a", "b", "c", "d"],
         "correct_answer": "not-an-option"}
    ]"""
    generator, _ = _generator(response)

    assert generator.generate(text="content", count=1) == []


def test_generate_drops_question_with_fewer_than_two_options():
    response = """[
        {"question": "Bad question", "options": ["a"],
         "correct_answer": "a"}
    ]"""
    generator, _ = _generator(response)

    assert generator.generate(text="content", count=1) == []


def test_generate_returns_empty_list_for_malformed_json():
    generator, _ = _generator("not valid json")
    assert generator.generate(text="content", count=2) == []


def test_generate_returns_empty_list_when_llm_raises():
    llm_client = MagicMock()
    llm_client.generate.side_effect = RuntimeError("ollama unreachable")
    generator = MCQGenerator(llm_client=llm_client)

    assert generator.generate(text="content", count=2) == []


def test_generate_deduplicates_identical_questions():
    response = """[
        {"question": "Same question?", "options": ["a", "b", "c", "d"],
         "correct_answer": "a"},
        {"question": "Same question?", "options": ["a", "b", "c", "d"],
         "correct_answer": "a"}
    ]"""
    generator, _ = _generator(response)

    questions = generator.generate(text="content", count=5)

    assert len(questions) == 1


def test_generate_respects_requested_count():
    response = """[
        {"question": "Q1?", "options": ["a", "b", "c", "d"],
         "correct_answer": "a"},
        {"question": "Q2?", "options": ["a", "b", "c", "d"],
         "correct_answer": "a"},
        {"question": "Q3?", "options": ["a", "b", "c", "d"],
         "correct_answer": "a"}
    ]"""
    generator, _ = _generator(response)

    questions = generator.generate(text="content", count=2)

    assert len(questions) == 2
