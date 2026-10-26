"""
Speech-recognition accuracy: word error rate (WER) and character error
rate (CER), with Vietnamese-aware normalization.

WER = (substitutions + deletions + insertions) / reference words, from a
word-level Levenshtein alignment. Corpus WER sums edits and reference
words over every utterance (the standard way to report it), rather than
averaging per-utterance rates, so short clips don't dominate.

Normalization is applied to both sides before scoring, because
reference transcripts and Whisper differ in casing and punctuation in
ways that aren't recognition errors:
- Unicode NFC, so precomposed and decomposed Vietnamese diacritics
  ("ế" as one code point vs "e" + combining marks) compare equal;
- lowercase;
- punctuation removed (letters with diacritics and digits are kept);
- whitespace collapsed.
Diacritics are never stripped: "ma", "má", "mà", "mả", "mã", "mạ" are
different words in Vietnamese, and getting them wrong is a real error.
"""
import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass


_PUNCTUATION = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WHITESPACE = re.compile(r"\s+")


def normalize_transcript(text: str) -> str:
    """Normalize a transcript for scoring (see module docstring)."""
    text = unicodedata.normalize("NFC", text or "").lower()
    text = _PUNCTUATION.sub(" ", text.replace("_", " "))
    return _WHITESPACE.sub(" ", text).strip()


@dataclass(frozen=True)
class EditCounts:
    substitutions: int = 0
    deletions: int = 0
    insertions: int = 0
    reference_length: int = 0

    @property
    def errors(self) -> int:
        return self.substitutions + self.deletions + self.insertions

    @property
    def rate(self) -> float:
        """Error rate; 0.0 for an empty reference with an empty hypothesis."""
        if self.reference_length == 0:
            return 0.0 if self.errors == 0 else 1.0
        return self.errors / self.reference_length

    def __add__(self, other: "EditCounts") -> "EditCounts":
        return EditCounts(
            substitutions=self.substitutions + other.substitutions,
            deletions=self.deletions + other.deletions,
            insertions=self.insertions + other.insertions,
            reference_length=self.reference_length + other.reference_length,
        )


def align(reference: Sequence[str], hypothesis: Sequence[str]) -> EditCounts:
    """
    Minimum-edit alignment of two token sequences, returning how many
    substitutions, deletions and insertions it takes to turn
    `reference` into `hypothesis`. O(len(ref) * len(hyp)) time, one row
    of memory per side.
    """
    # Each cell: (cost, substitutions, deletions, insertions)
    previous = [(j, 0, 0, j) for j in range(len(hypothesis) + 1)]

    for i, ref_token in enumerate(reference, start=1):
        current = [(i, 0, i, 0)]
        for j, hyp_token in enumerate(hypothesis, start=1):
            if ref_token == hyp_token:
                current.append(previous[j - 1])
                continue
            sub = previous[j - 1]
            dele = previous[j]
            ins = current[j - 1]
            best = min(
                (sub[0] + 1, sub[1] + 1, sub[2], sub[3]),
                (dele[0] + 1, dele[1], dele[2] + 1, dele[3]),
                (ins[0] + 1, ins[1], ins[2], ins[3] + 1),
            )
            current.append(best)
        previous = current

    _, substitutions, deletions, insertions = previous[-1]
    return EditCounts(
        substitutions=substitutions,
        deletions=deletions,
        insertions=insertions,
        reference_length=len(reference),
    )


def word_edits(reference: str, hypothesis: str) -> EditCounts:
    return align(
        normalize_transcript(reference).split(),
        normalize_transcript(hypothesis).split(),
    )


def char_edits(reference: str, hypothesis: str) -> EditCounts:
    """Character-level edits, ignoring spaces (CER)."""
    return align(
        list(normalize_transcript(reference).replace(" ", "")),
        list(normalize_transcript(hypothesis).replace(" ", "")),
    )


def word_error_rate(reference: str, hypothesis: str) -> float:
    return word_edits(reference, hypothesis).rate


def corpus_error_rates(pairs: Iterable[tuple[str, str]]) -> tuple[EditCounts, EditCounts]:
    """
    Summed word-level and character-level edits over (reference,
    hypothesis) pairs - `.rate` on each is corpus WER / CER.
    """
    words = EditCounts()
    chars = EditCounts()
    for reference, hypothesis in pairs:
        words = words + word_edits(reference, hypothesis)
        chars = chars + char_edits(reference, hypothesis)
    return words, chars
