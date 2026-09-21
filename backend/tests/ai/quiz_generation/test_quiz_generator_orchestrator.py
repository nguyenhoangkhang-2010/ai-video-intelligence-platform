from unittest.mock import MagicMock

from ai.quiz_generation.quiz_generator import QuizGenerator
from ai.quiz_generation.quiz_result import QuizQuestion


def _make_generator():
    mcq_generator = MagicMock()
    true_false_generator = MagicMock()
    short_answer_generator = MagicMock()

    generator = QuizGenerator(
        llm_client=MagicMock(),
        mcq_generator=mcq_generator,
        true_false_generator=true_false_generator,
        short_answer_generator=short_answer_generator,
    )

    return generator, mcq_generator, true_false_generator, short_answer_generator


def test_generate_returns_empty_result_for_empty_text():
    generator, mcq, tf, sa = _make_generator()

    result = generator.generate(text="   ")

    assert result.questions == ()
    mcq.generate.assert_not_called()
    tf.generate.assert_not_called()
    sa.generate.assert_not_called()


def test_generate_combines_all_three_question_types():
    generator, mcq, tf, sa = _make_generator()

    mcq.generate.return_value = [
        QuizQuestion(
            question="mcq?", question_type="multiple_choice",
            correct_answer="a", options=("a", "b"),
        ),
    ]
    tf.generate.return_value = [
        QuizQuestion(
            question="tf?", question_type="true_false",
            correct_answer="True",
        ),
    ]
    sa.generate.return_value = [
        QuizQuestion(
            question="sa?", question_type="short_answer",
            correct_answer="answer",
        ),
    ]

    result = generator.generate(
        text="source content",
        mcq_count=1, true_false_count=1, short_answer_count=1,
    )

    assert len(result.questions) == 3
    types = {q.question_type for q in result.questions}
    assert types == {"multiple_choice", "true_false", "short_answer"}


def test_generate_skips_disabled_question_types():
    generator, mcq, tf, sa = _make_generator()
    mcq.generate.return_value = []

    generator.generate(
        text="source content",
        mcq_count=0, true_false_count=0, short_answer_count=0,
    )

    mcq.generate.assert_not_called()
    tf.generate.assert_not_called()
    sa.generate.assert_not_called()


def test_generate_truncates_source_text_to_configured_max_chars():
    generator, mcq, tf, sa = _make_generator()
    mcq.generate.return_value = []
    tf.generate.return_value = []
    sa.generate.return_value = []

    long_text = "x" * 100_000

    generator.generate(
        text=long_text,
        mcq_count=1, true_false_count=0, short_answer_count=0,
    )

    passed_text = mcq.generate.call_args.kwargs["text"]
    assert len(passed_text) <= 100_000
    assert len(passed_text) < len(long_text)
