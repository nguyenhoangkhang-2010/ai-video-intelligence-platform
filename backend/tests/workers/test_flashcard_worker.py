from unittest.mock import MagicMock

from app.workers.flashcard_worker import FlashcardWorker
from ai.flashcards.flashcard_result import Flashcard, FlashcardResult


def test_process_returns_empty_list_for_empty_transcript():
    worker = FlashcardWorker(flashcard_generator=MagicMock())

    assert worker.process(transcript="") == []


def test_process_adapts_flashcards_to_dicts():
    flashcard_generator = MagicMock()
    flashcard_generator.generate.return_value = FlashcardResult(
        cards=(
            Flashcard(front="Front1", back="Back1"),
            Flashcard(front="Front2", back="Back2", difficulty="hard"),
        ),
    )
    worker = FlashcardWorker(flashcard_generator=flashcard_generator)

    flashcards = worker.process(transcript="some transcript")

    assert flashcards == [
        {"question": "Front1", "answer": "Back1", "difficulty": "medium"},
        {"question": "Front2", "answer": "Back2", "difficulty": "hard"},
    ]


def test_process_returns_empty_list_when_generation_fails():
    flashcard_generator = MagicMock()
    flashcard_generator.generate.side_effect = RuntimeError("llm down")
    worker = FlashcardWorker(flashcard_generator=flashcard_generator)

    assert worker.process(transcript="some transcript") == []


def test_process_returns_empty_list_when_flashcards_disabled(monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings.flashcard, "enabled", False)
    flashcard_generator = MagicMock()
    worker = FlashcardWorker(flashcard_generator=flashcard_generator)

    assert worker.process(transcript="some transcript") == []
    flashcard_generator.generate.assert_not_called()
