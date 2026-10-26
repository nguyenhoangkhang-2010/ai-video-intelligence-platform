import unicodedata

from ai.evaluation.metrics.asr import (
    EditCounts,
    align,
    char_edits,
    corpus_error_rates,
    normalize_transcript,
    word_edits,
    word_error_rate,
)


# ---- normalize_transcript ----

def test_normalize_lowercases_and_strips_punctuation():
    assert normalize_transcript("Xin chào, Thế Giới!  ") == "xin chào thế giới"


def test_normalize_unifies_decomposed_diacritics():
    decomposed = unicodedata.normalize("NFD", "tiếng Việt")

    assert decomposed != "tiếng Việt"
    assert normalize_transcript(decomposed) == "tiếng việt"


def test_normalize_keeps_tone_marks_distinct():
    assert normalize_transcript("ma má mà mả mã mạ").split() == ["ma", "má", "mà", "mả", "mã", "mạ"]


# ---- align / WER ----

def test_identical_sequences_have_no_edits():
    counts = align(["a", "b", "c"], ["a", "b", "c"])

    assert counts == EditCounts(reference_length=3)
    assert counts.rate == 0.0


def test_counts_substitution_deletion_insertion():
    assert align(["a", "b", "c"], ["a", "x", "c"]).substitutions == 1
    assert align(["a", "b", "c"], ["a", "c"]).deletions == 1
    assert align(["a", "b", "c"], ["a", "b", "y", "c"]).insertions == 1


def test_wrong_tone_is_a_word_error():
    assert word_error_rate("tôi đi chợ", "tôi đi chờ") == 1 / 3


def test_casing_and_punctuation_are_not_errors():
    assert word_error_rate("Hôm nay, trời đẹp.", "hôm nay trời đẹp") == 0.0


def test_empty_reference_rates():
    assert word_error_rate("", "") == 0.0
    assert word_error_rate("", "thừa") == 1.0


def test_wer_can_exceed_one_with_many_insertions():
    assert word_edits("a", "x y z").rate == 3.0


def test_char_edits_ignore_spaces():
    assert char_edits("ab cd", "abcd").rate == 0.0
    assert char_edits("abcd", "abce").substitutions == 1


# ---- corpus ----

def test_corpus_wer_weights_by_reference_length():
    words, _ = corpus_error_rates([
        ("một", "hai"),  # 1 error / 1 word
        ("a b c d e f g h i", "a b c d e f g h i"),  # 0 / 9
    ])

    assert words.errors == 1
    assert words.reference_length == 10
    assert words.rate == 0.1
