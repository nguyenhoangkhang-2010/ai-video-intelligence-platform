"""
Optional, lazily-loaded BERTScore wrapper.

BERTScore is a model-based generation metric: it embeds candidate and
reference text with a transformer model and compares them by cosine
similarity, capturing paraphrases/synonyms that lexical metrics like
ROUGE miss - at the cost of needing a real (potentially large)
transformer model loaded.

`bert_score` is imported lazily (only inside `_load()`, never at
module import time) so that:
  - importing this module never requires bert_score/torch/transformers
    to be installed or working.
  - constructing a BERTScoreEvaluator is cheap and never triggers a
    model load.
  - the model itself is only downloaded/loaded the first time
    `.score()` actually runs, and is reused for subsequent calls on
    the same instance.

This mirrors the existing lazy-import convention already used in this
project for other heavy/fragile ML dependencies (see
ai.reranking.cross_encoder.CrossEncoderReranker for sentence-
transformers, and ai.diarization for pyannote.audio).
"""
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)


class BERTScoreUnavailableError(RuntimeError):
    """Raised when the `bert_score` package cannot be imported/used."""


class BERTScoreEvaluator:
    """
    Model-based generation metric. Kept independent from ROUGE
    (ai.evaluation.rouge) - callers combine both explicitly rather
    than this class silently falling back to one or the other.
    """

    def __init__(
        self,
        model_name: str | None = None,
        lang: str | None = None,
    ):
        self.model_name = model_name or settings.evaluation.bertscore_model
        self.lang = lang or settings.evaluation.bertscore_lang
        self._score_fn = None

    def _load(self):
        if self._score_fn is not None:
            return self._score_fn

        try:
            from bert_score import score as bert_score_fn
        except ImportError as exc:
            raise BERTScoreUnavailableError(
                "bert_score is not installed/importable in this "
                "environment. Install the 'bert-score' package (and "
                "its transformer model dependencies) to enable "
                "BERTScore evaluation, or use "
                "ai.evaluation.rouge.RougeScorer for a deterministic, "
                "dependency-light alternative."
            ) from exc

        self._score_fn = bert_score_fn
        return self._score_fn

    def score(
        self,
        candidates: list[str],
        references: list[str],
    ) -> dict[str, list[float]]:
        """
        Return {"precision": [...], "recall": [...], "f1": [...]},
        one value per (candidate, reference) pair, in input order.

        Raises BERTScoreUnavailableError if bert_score cannot be
        imported - callers that want a soft/optional path should
        catch this explicitly rather than this method silently
        returning a fabricated score.
        """
        if len(candidates) != len(references):
            raise ValueError(
                "candidates and references must be the same length."
            )

        if not candidates:
            return {"precision": [], "recall": [], "f1": []}

        score_fn = self._load()

        kwargs = {"model_type": self.model_name} if self.model_name else {"lang": self.lang}

        logger.info(
            "Computing BERTScore for %s candidate/reference pair(s).",
            len(candidates),
        )

        precision, recall, f1 = score_fn(candidates, references, **kwargs)

        return {
            "precision": [float(value) for value in precision],
            "recall": [float(value) for value in recall],
            "f1": [float(value) for value in f1],
        }
