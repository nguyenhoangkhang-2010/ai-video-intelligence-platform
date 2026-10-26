import pytest

from ai.chapter_detection.similarity import cosine_similarity


def test_identical_vectors_have_similarity_one():
    # float32 internally, so allow for rounding rather than exact ==.
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_orthogonal_vectors_have_similarity_zero():
    assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-6


def test_opposite_vectors_have_similarity_negative_one():
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == -1.0


def test_zero_length_vector_returns_zero_not_divide_by_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0
