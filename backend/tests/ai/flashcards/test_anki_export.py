from ai.flashcards.anki_export import AnkiExporter
from ai.flashcards.flashcard_result import Flashcard


def test_export_to_string_preserves_order_and_uses_tab_separator():
    exporter = AnkiExporter()
    cards = [
        Flashcard(front="Q1", back="A1"),
        Flashcard(front="Q2", back="A2"),
    ]

    content = exporter.export_to_string(cards)

    lines = content.split("\n")
    assert lines == ["Q1\tA1", "Q2\tA2"]


def test_export_to_string_escapes_tabs_and_newlines_in_fields():
    exporter = AnkiExporter()
    cards = [
        Flashcard(front="Question\twith\ttabs", back="Answer\nwith\nnewlines"),
    ]

    content = exporter.export_to_string(cards)

    # Exactly one field-separator tab per line (front/back), any tabs
    # that were part of the original field content must be gone.
    assert content.count("\t") == 1
    assert "\n" not in content.strip()


def test_export_to_string_preserves_unicode_content():
    exporter = AnkiExporter()
    cards = [
        Flashcard(front="Câu hỏi tiếng Việt?", back="Câu trả lời có dấu"),
    ]

    content = exporter.export_to_string(cards)

    assert "Câu hỏi tiếng Việt?" in content
    assert "Câu trả lời có dấu" in content


def test_export_writes_utf8_file_and_returns_path(tmp_path):
    exporter = AnkiExporter()
    cards = [
        Flashcard(front="Front unicode: đ", back="Back unicode: ệ"),
    ]
    output_path = tmp_path / "cards.tsv"

    result_path = exporter.export(cards, output_path)

    assert result_path == output_path
    content = output_path.read_text(encoding="utf-8")
    assert content == "Front unicode: đ\tBack unicode: ệ\n"


def test_export_handles_empty_card_list(tmp_path):
    exporter = AnkiExporter()
    output_path = tmp_path / "empty.tsv"

    exporter.export([], output_path)

    assert output_path.read_text(encoding="utf-8") == ""


def test_export_creates_parent_directories(tmp_path):
    exporter = AnkiExporter()
    output_path = tmp_path / "nested" / "dir" / "cards.tsv"

    exporter.export([Flashcard(front="F", back="B")], output_path)

    assert output_path.exists()
