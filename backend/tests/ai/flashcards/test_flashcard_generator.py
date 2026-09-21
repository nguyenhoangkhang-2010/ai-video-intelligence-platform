from unittest.mock import MagicMock

from ai.flashcards.flashcard_generator import FlashcardGenerator


def _generator(response_text):
    llm_client = MagicMock()
    llm_client.generate.return_value = response_text
    return FlashcardGenerator(llm_client=llm_client), llm_client


def test_generate_returns_empty_result_for_empty_text():
    generator, llm_client = _generator("[]")

    result = generator.generate(text="   ", count=3)

    assert result.cards == ()
    llm_client.generate.assert_not_called()


def test_generate_returns_empty_result_for_zero_count():
    generator, llm_client = _generator("[]")

    result = generator.generate(text="some content", count=0)

    assert result.cards == ()
    llm_client.generate.assert_not_called()


def test_generate_parses_valid_flashcards():
    response = """[
        {"front": "What is X?", "back": "X is a concept."},
        {"front": "What is Y?", "back": "Y is another concept."}
    ]"""
    generator, _ = _generator(response)

    result = generator.generate(text="lesson content", count=5)

    assert len(result.cards) == 2
    assert result.cards[0].front == "What is X?"
    assert result.cards[0].back == "X is a concept."


def test_generate_drops_card_missing_back_field():
    response = '[{"front": "Q only"}]'
    generator, _ = _generator(response)

    assert generator.generate(text="content", count=5).cards == ()


def test_generate_drops_card_with_empty_front():
    response = '[{"front": "   ", "back": "answer"}]'
    generator, _ = _generator(response)

    assert generator.generate(text="content", count=5).cards == ()


def test_generate_returns_empty_result_for_malformed_json():
    generator, _ = _generator("not json at all")

    assert generator.generate(text="content", count=5).cards == ()


def test_generate_returns_empty_result_when_llm_raises():
    llm_client = MagicMock()
    llm_client.generate.side_effect = RuntimeError("unreachable")
    generator = FlashcardGenerator(llm_client=llm_client)

    assert generator.generate(text="content", count=5).cards == ()


def test_generate_deduplicates_identical_fronts():
    response = """[
        {"front": "Same front", "back": "answer 1"},
        {"front": "Same front", "back": "answer 2"}
    ]"""
    generator, _ = _generator(response)

    result = generator.generate(text="content", count=5)

    assert len(result.cards) == 1


def test_generate_respects_requested_count():
    response = """[
        {"front": "A", "back": "1"},
        {"front": "B", "back": "2"},
        {"front": "C", "back": "3"}
    ]"""
    generator, _ = _generator(response)

    result = generator.generate(text="content", count=2)

    assert len(result.cards) == 2
