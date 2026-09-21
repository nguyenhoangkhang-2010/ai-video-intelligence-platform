from ai.evaluation.rouge import RougeScorer


def test_score_returns_one_for_identical_text():
    scorer = RougeScorer(rouge_types=["rouge1", "rougeL"])

    scores = scorer.score("the cat sat on the mat", "the cat sat on the mat")

    assert scores["rouge1"] == 1.0
    assert scores["rougeL"] == 1.0


def test_score_returns_lower_value_for_partial_overlap():
    scorer = RougeScorer(rouge_types=["rouge1"])

    scores = scorer.score("the dog ran fast", "the cat sat on the mat")

    assert 0.0 <= scores["rouge1"] < 1.0


def test_score_returns_zero_for_empty_candidate():
    scorer = RougeScorer(rouge_types=["rouge1", "rougeL"])

    scores = scorer.score("", "the cat sat on the mat")

    assert scores == {"rouge1": 0.0, "rougeL": 0.0}


def test_score_returns_zero_for_empty_reference():
    scorer = RougeScorer(rouge_types=["rouge1"])

    scores = scorer.score("the cat sat", "   ")

    assert scores == {"rouge1": 0.0}


def test_score_returns_all_configured_rouge_types():
    scorer = RougeScorer(rouge_types=["rouge1", "rouge2", "rougeL"])

    scores = scorer.score("a b c d", "a b c d")

    assert set(scores.keys()) == {"rouge1", "rouge2", "rougeL"}


def test_default_rouge_types_are_used_when_none_specified():
    scorer = RougeScorer()

    assert scorer.rouge_types == ("rouge1", "rouge2", "rougeL")
