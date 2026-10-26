import pytest

from ai.evaluation.reranking_benchmark import (
    RankingTask,
    SystemScore,
    bm25_scorer,
    build_ranking_tasks,
    rank,
)


def _records():
    records = []
    for article in ("A", "B"):
        for n in range(4):
            context = f"article {article} passage {n} text"
            records.append({"title": article, "context": context, "question": f"q {article}{n} first"})
            records.append({"title": article, "context": context, "question": f"q {article}{n} second"})
    records.append({"title": "A", "context": "unanswerable", "question": "q none", "is_impossible": True})
    return records


def test_each_task_contains_its_passage_once():
    tasks = build_ranking_tasks(_records(), candidates_per_task=5)

    assert len(tasks) == 16
    for task in tasks:
        assert task.candidate_ids.count(task.relevant_id) == 1
        assert len(set(task.candidate_ids)) == len(task.candidate_ids) == 5
        assert len(task.candidate_texts) == 5


def test_negatives_prefer_same_article():
    tasks = build_ranking_tasks(_records(), candidates_per_task=4)

    for task in tasks:
        article = task.query.split()[1][0]
        assert all(f"article {article} " in text for text in task.candidate_texts)


def test_fills_from_other_articles_when_article_is_small():
    tasks = build_ranking_tasks(_records(), candidates_per_task=6)

    for task in tasks:
        articles = {text.split()[1] for text in task.candidate_texts}
        assert articles == {"A", "B"}


def test_unanswerable_questions_are_skipped():
    tasks = build_ranking_tasks(_records(), candidates_per_task=3)

    assert all(task.query != "q none" for task in tasks)
    assert all("unanswerable" not in text for task in tasks for text in task.candidate_texts)


def test_same_seed_is_reproducible_and_max_tasks_applies():
    first = build_ranking_tasks(_records(), candidates_per_task=4, max_tasks=5, seed=1)
    second = build_ranking_tasks(_records(), candidates_per_task=4, max_tasks=5, seed=1)

    assert first == second
    assert len(first) == 5


def test_rank_orders_by_score():
    task = RankingTask(query="q", candidate_ids=["x", "y", "z"], candidate_texts=["1", "3", "2"], relevant_id="y")

    assert rank(task, lambda query, texts: [float(t) for t in texts]) == ["y", "z", "x"]


def test_bm25_prefers_lexical_match():
    scores = bm25_scorer("thủ đô Hà Nội", ["Hà Nội là thủ đô", "món phở bò", "sông Hồng chảy qua"])

    assert scores[0] == max(scores)


def test_system_score_averages_metrics():
    score = SystemScore(name="s")
    score.add(["a", "b"], "a")  # rank 1
    score.add(["b", "a"], "a")  # rank 2

    assert score.tasks == 2
    assert score.mrr == pytest.approx(0.75)
    assert score.recall_at_1 == pytest.approx(0.5)
