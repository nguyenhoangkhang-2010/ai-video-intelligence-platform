from unittest.mock import MagicMock

from app.workers.quiz_worker import QuizWorker
from ai.quiz_generation.quiz_result import QuizQuestion, QuizResult


def test_process_returns_empty_list_for_empty_transcript():
    worker = QuizWorker(quiz_generator=MagicMock())

    assert worker.process(transcript="   ") == []


def test_process_adapts_quiz_questions_to_dicts():
    quiz_generator = MagicMock()
    quiz_generator.generate.return_value = QuizResult(
        questions=(
            QuizQuestion(
                question="Q1?", question_type="multiple_choice",
                correct_answer="A", options=("A", "B", "C", "D"),
            ),
            QuizQuestion(
                question="Q2?", question_type="short_answer",
                correct_answer="B",
            ),
        ),
    )
    worker = QuizWorker(quiz_generator=quiz_generator)

    quizzes = worker.process(transcript="some transcript")

    assert quizzes == [
        {
            "type": "multiple_choice", "question": "Q1?",
            "answer": "A", "options": "A,B,C,D",
        },
        {
            "type": "short_answer", "question": "Q2?",
            "answer": "B", "options": None,
        },
    ]


def test_process_returns_empty_list_when_generation_fails():
    quiz_generator = MagicMock()
    quiz_generator.generate.side_effect = RuntimeError("llm down")
    worker = QuizWorker(quiz_generator=quiz_generator)

    assert worker.process(transcript="some transcript") == []


def test_process_returns_empty_list_when_quiz_disabled(monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings.quiz, "enabled", False)
    quiz_generator = MagicMock()
    worker = QuizWorker(quiz_generator=quiz_generator)

    assert worker.process(transcript="some transcript") == []
    quiz_generator.generate.assert_not_called()
