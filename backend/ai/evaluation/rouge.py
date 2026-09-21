"""
Deterministic ROUGE-N / ROUGE-L wrapper around the `rouge_score`
library (already an installed project dependency - pure Python, no
model download, no network call).

ROUGE measures n-gram/longest-common-subsequence overlap between a
generated candidate and a reference text - useful as a fast,
reproducible, purely lexical baseline for summary/translation/label
generation quality, but it has no notion of meaning: paraphrases score
low even when perfectly correct, and it is not a substitute for
semantic evaluation (see ai.evaluation.bertscore for a model-based
alternative).
"""
from rouge_score import rouge_scorer

DEFAULT_ROUGE_TYPES = ("rouge1", "rouge2", "rougeL")


class RougeScorer:
    """
    Thin, import-safe wrapper around rouge_score.rouge_scorer.RougeScorer.

    Deterministic: the same (candidate, reference) pair always
    produces the same scores, with no external calls involved.
    """

    def __init__(
        self,
        rouge_types: list[str] | None = None,
        use_stemmer: bool = True,
    ):
        self.rouge_types = tuple(rouge_types) if rouge_types else DEFAULT_ROUGE_TYPES
        self._scorer = rouge_scorer.RougeScorer(
            list(self.rouge_types), use_stemmer=use_stemmer,
        )

    def score(
        self,
        candidate: str,
        reference: str,
    ) -> dict[str, float]:
        """
        Return {rouge_type: f-measure} for each configured rouge type.

        An empty candidate or reference has no meaningful overlap, so
        this returns 0.0 for every rouge type rather than letting the
        underlying library raise or return a misleading score.
        """
        if not candidate or not candidate.strip():
            return {rouge_type: 0.0 for rouge_type in self.rouge_types}
        if not reference or not reference.strip():
            return {rouge_type: 0.0 for rouge_type in self.rouge_types}

        scores = self._scorer.score(reference, candidate)

        return {
            rouge_type: scores[rouge_type].fmeasure
            for rouge_type in self.rouge_types
        }
