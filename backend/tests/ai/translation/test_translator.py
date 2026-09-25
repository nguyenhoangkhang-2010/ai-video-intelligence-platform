from unittest.mock import MagicMock

import pytest

from ai.translation.translator import Translator


def _translator(response_text="translated text"):
    llm_client = MagicMock()
    llm_client.generate.return_value = response_text
    return Translator(llm_client=llm_client), llm_client


def test_translate_calls_llm_and_returns_its_output():
    translator, llm_client = _translator("Xin chao, day la ban dich.")

    result = translator.translate(
        text="Hello, this is a transcript.",
        target_language="vi",
        source_language="en",
    )

    assert result == "Xin chao, day la ban dich."
    llm_client.generate.assert_called_once()

    # The transcript text and target language actually reached the
    # prompt sent to the LLM.
    prompt = llm_client.generate.call_args.args[0]
    assert "Hello, this is a transcript." in prompt
    assert "vi" in prompt


def test_translate_skips_llm_when_source_already_matches_target():
    """
    This is the fix for the previous no-op bug: when the source is
    ALREADY the target language, returning the input unchanged is
    correct - the regression this guards against is the old
    Translator, which returned the input unchanged unconditionally,
    even when source_language differed from target_language.
    """
    translator, llm_client = _translator("should not be used")

    result = translator.translate(
        text="Already in English.",
        target_language="en",
        source_language="en",
    )

    assert result == "Already in English."
    llm_client.generate.assert_not_called()


def test_translate_is_case_insensitive_when_comparing_languages():
    translator, llm_client = _translator("should not be used")

    result = translator.translate(
        text="Already in English.",
        target_language="EN",
        source_language="en",
    )

    assert result == "Already in English."
    llm_client.generate.assert_not_called()


def test_translate_calls_llm_when_source_language_is_unknown():
    """
    With no source_language provided, the translator can't know the
    text is already in the target language, so it must actually
    translate rather than guessing it's a no-op.
    """
    translator, llm_client = _translator("translated")

    result = translator.translate(
        text="Some transcript text.",
        target_language="en",
    )

    assert result == "translated"
    llm_client.generate.assert_called_once()


def test_translate_calls_llm_when_source_differs_from_target():
    translator, llm_client = _translator("translated")

    result = translator.translate(
        text="Noi dung tieng Viet.",
        target_language="en",
        source_language="vi",
    )

    assert result == "translated"
    llm_client.generate.assert_called_once()


def test_translate_raises_on_empty_text():
    translator, llm_client = _translator()

    with pytest.raises(ValueError):
        translator.translate(text="   ", target_language="en")

    llm_client.generate.assert_not_called()
