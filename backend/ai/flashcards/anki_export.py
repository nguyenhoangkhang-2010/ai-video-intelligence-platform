"""
Reusable, dependency-free exporter for flashcards in a standard
Anki-compatible format.

No genanki/.apkg dependency is present anywhere in this project's
requirements, so this exporter targets Anki's plain-text import
format instead: tab-separated front/back columns, UTF-8 encoded, one
card per line. This is a format Anki's "Import File" natively
understands (Notes separated by newline, Fields separated by tab)
without introducing any new dependency. Export is a pure
file-producing operation with no HTTP/API coupling, so it can be
reused from a script, a future endpoint, or a test equally.
"""
from pathlib import Path

from ai.flashcards.flashcard_result import Flashcard

_FIELD_SEPARATOR = "\t"
_RECORD_SEPARATOR = "\n"


class AnkiExporter:
    """Exports flashcards to Anki-importable tab-separated plain text."""

    def export(
        self,
        cards: list[Flashcard],
        output_path: str | Path,
    ) -> Path:
        """
        Write `cards` to `output_path` as a UTF-8 TSV file (front\tback
        per line, one line per card, input order preserved). Returns
        the resolved output path.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            self._format_card(card)
            for card in cards
        ]

        content = _RECORD_SEPARATOR.join(lines)
        if content:
            content += _RECORD_SEPARATOR

        path.write_text(content, encoding="utf-8")

        return path

    def export_to_string(
        self,
        cards: list[Flashcard],
    ) -> str:
        """Same as export(), but returns the TSV content as a string."""
        lines = [
            self._format_card(card)
            for card in cards
        ]
        return _RECORD_SEPARATOR.join(lines)

    @staticmethod
    def _format_card(
        card: Flashcard,
    ) -> str:
        front = _escape_field(card.front)
        back = _escape_field(card.back)
        return f"{front}{_FIELD_SEPARATOR}{back}"


def _escape_field(
    value: str,
) -> str:
    """
    Anki's TSV import treats tab as the field separator and newline as
    the record separator, so both must be neutralized inside a field
    value without altering its meaning or losing Unicode content.
    """
    return (
        value
        .replace("\\", "\\\\")
        .replace("\t", " ")
        .replace("\r\n", " ")
        .replace("\n", " ")
    )
