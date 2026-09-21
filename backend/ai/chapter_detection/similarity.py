import numpy as np


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """
    Cosine similarity in [-1, 1] (1 = identical direction). Returns
    0.0 for a zero-length vector rather than dividing by zero.
    """

    a = np.asarray(vector_a, dtype=np.float32)
    b = np.asarray(vector_b, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(
        np.dot(a, b) / (norm_a * norm_b)
    )
