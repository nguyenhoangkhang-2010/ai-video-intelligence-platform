from unittest.mock import MagicMock

from app.workers.translation_worker import TranslationWorker


def _worker(translated_text="translated"):
    translator = MagicMock()
    translator.translate.return_value = translated_text

    worker = TranslationWorker()
    worker.translator = translator

    return worker, translator


def test_process_passes_source_language_through_to_translator():
    worker, translator = _worker("ket qua dich")

    result = worker.process(
        transcript="Original transcript text.",
        target_language="en",
        source_language="vi",
    )

    translator.translate.assert_called_once_with(
        "Original transcript text.",
        "en",
        source_language="vi",
    )
    assert result == {"language": "en", "subtitle": "ket qua dich"}


def test_process_defaults_source_language_to_none():
    worker, translator = _worker()

    worker.process(
        transcript="Some text.",
        target_language="en",
    )

    translator.translate.assert_called_once_with(
        "Some text.",
        "en",
        source_language=None,
    )
