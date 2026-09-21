from unittest.mock import MagicMock

from ai.llm.chapter_labeler import ChapterLabeler


def test_label_returns_untitled_for_empty_text():
    labeler = ChapterLabeler(llm_client=MagicMock())

    assert labeler.label("   ") == "Untitled"


def test_label_uses_llm_generated_title():
    llm_client = MagicMock()
    llm_client.generate.return_value = '"A Great Title"'

    labeler = ChapterLabeler(llm_client=llm_client)
    title = labeler.label("some transcript content")

    assert title == "A Great Title"


def test_label_passes_text_into_the_prompt():
    llm_client = MagicMock()
    llm_client.generate.return_value = "Title"

    labeler = ChapterLabeler(llm_client=llm_client)
    labeler.label("unique marker phrase xyz")

    prompt = llm_client.generate.call_args.args[0]
    assert "unique marker phrase xyz" in prompt


def test_label_falls_back_to_snippet_when_llm_raises():
    llm_client = MagicMock()
    llm_client.generate.side_effect = RuntimeError("ollama unreachable")

    labeler = ChapterLabeler(llm_client=llm_client)
    title = labeler.label("one two three four five six seven eight nine ten")

    assert title == "one two three four five six seven eight"


def test_label_falls_back_when_llm_returns_empty_string():
    llm_client = MagicMock()
    llm_client.generate.return_value = "   "

    labeler = ChapterLabeler(llm_client=llm_client)
    title = labeler.label("fallback content here")

    assert title == "fallback content here"
