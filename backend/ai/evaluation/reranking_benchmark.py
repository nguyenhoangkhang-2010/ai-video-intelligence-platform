"""
Reranker comparison on a reading-comprehension dataset.

Each answerable question becomes one ranking task: its own passage (the
one a person wrote the question from - the relevant item) mixed with
other passages, preferably from the same article (hard negatives: same
topic, wrong passage). Every system ranks the same candidates, and is
scored with the same retrieval metrics the rest of the evaluation
framework uses (ai.evaluation.metrics.retrieval).

This isolates the reranking step: it answers "given a handful of
plausible passages, which model puts the right one first?" - exactly
what the cross-encoder does in the RAG pipeline - on human-labelled
Vietnamese data instead of English MS MARCO.
"""
import random
import re
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

from ai.evaluation.metrics.retrieval import ndcg_at_k, recall_at_k, reciprocal_rank


@dataclass(frozen=True)
class RankingTask:
    query: str
    candidate_ids: list[str]
    candidate_texts: list[str]
    relevant_id: str


@dataclass
class SystemScore:
    name: str
    tasks: int = 0
    mrr: float = 0.0
    recall_at_1: float = 0.0
    ndcg_at_5: float = 0.0
    seconds: float = 0.0
    _sums: dict[str, float] = field(default_factory=lambda: defaultdict(float), repr=False)

    def add(self, ranked_ids: Sequence[str], relevant_id: str) -> None:
        relevant = [relevant_id]
        self._sums["mrr"] += reciprocal_rank(ranked_ids, relevant)
        self._sums["r1"] += recall_at_k(ranked_ids, relevant, 1)
        self._sums["ndcg5"] += ndcg_at_k(ranked_ids, relevant, 5)
        self.tasks += 1
        self.mrr = self._sums["mrr"] / self.tasks
        self.recall_at_1 = self._sums["r1"] / self.tasks
        self.ndcg_at_5 = self._sums["ndcg5"] / self.tasks


def build_ranking_tasks(
    records: Iterable[dict],
    candidates_per_task: int = 10,
    max_tasks: int | None = None,
    seed: int = 13,
) -> list[RankingTask]:
    """
    Turn SQuAD-style records ({"title", "context", "question",
    "is_impossible"?}) into ranking tasks.

    Negatives come from other passages of the same article first, then
    from other articles to fill up to `candidates_per_task`. Unanswerable
    questions are skipped (they have no correct passage). Candidate order
    is shuffled with a fixed seed so results are reproducible and no
    system benefits from the correct passage sitting first.
    """
    rng = random.Random(seed)

    passages: dict[str, int] = {}
    passages_by_title: dict[str, list[int]] = defaultdict(list)
    passage_texts: list[str] = []
    questions: list[tuple[str, int, str]] = []

    for record in records:
        if record.get("is_impossible"):
            continue
        context = (record.get("context") or "").strip()
        question = (record.get("question") or "").strip()
        if not context or not question:
            continue
        title = record.get("title") or ""
        if context not in passages:
            passages[context] = len(passage_texts)
            passage_texts.append(context)
            passages_by_title[title].append(passages[context])
        questions.append((question, passages[context], title))

    rng.shuffle(questions)
    if max_tasks is not None:
        questions = questions[:max_tasks]

    all_ids = list(range(len(passage_texts)))
    tasks = []
    for question, positive, title in questions:
        same_article = [p for p in passages_by_title[title] if p != positive]
        rng.shuffle(same_article)
        negatives = same_article[: candidates_per_task - 1]

        if len(negatives) < candidates_per_task - 1:
            chosen = set(negatives) | {positive}
            pool = [p for p in all_ids if p not in chosen]
            rng.shuffle(pool)
            negatives += pool[: candidates_per_task - 1 - len(negatives)]

        if not negatives:
            continue

        candidates = [positive, *negatives]
        rng.shuffle(candidates)
        tasks.append(
            RankingTask(
                query=question,
                candidate_ids=[f"p{p}" for p in candidates],
                candidate_texts=[passage_texts[p] for p in candidates],
                relevant_id=f"p{positive}",
            )
        )
    return tasks


_TOKEN = re.compile(r"\w+", flags=re.UNICODE)


def bm25_scorer(query: str, texts: Sequence[str]) -> list[float]:
    """Lexical baseline: BM25 over the candidate set itself."""
    from rank_bm25 import BM25Okapi

    tokenize = lambda text: _TOKEN.findall(text.lower())  # noqa: E731
    return list(BM25Okapi([tokenize(text) for text in texts]).get_scores(tokenize(query)))


def rank(task: RankingTask, scorer: Callable[[str, Sequence[str]], Sequence[float]]) -> list[str]:
    scores = scorer(task.query, task.candidate_texts)
    order = sorted(range(len(task.candidate_ids)), key=lambda i: scores[i], reverse=True)
    return [task.candidate_ids[i] for i in order]
