import numpy as np
import pytest

from ai.embedding import index_builder as index_builder_module
from ai.embedding import index_metadata as index_metadata_module
from ai.embedding.vector_store import VectorStore


@pytest.fixture
def vector_store_factory(tmp_path, monkeypatch):
    """
    Build real VectorStore instances backed by an isolated temp
    directory instead of the real project storage/faiss/ location.

    IndexBuilder accepts an index_path override, but IndexMetadata
    does not - it always resolves its path from the module-level
    STORAGE_DIR in ai.embedding.index_metadata. So both modules'
    STORAGE_DIR are monkeypatched (auto-restored by pytest after the
    test) to point at tmp_path, which is what actually isolates every
    test from real application storage and from each other. No
    embedding model, no network, no mocking of FAISS itself - this
    exercises the real ai.embedding.vector_store code path.
    """
    monkeypatch.setattr(index_builder_module, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(index_metadata_module, "STORAGE_DIR", tmp_path)

    def _make(dimension: int = 4) -> VectorStore:
        return VectorStore(dimension=dimension)

    return _make


def _vec(*values) -> list[float]:
    return [float(v) for v in values]


def test_add_is_idempotent_for_duplicate_vector_ids(vector_store_factory):
    store = vector_store_factory()

    vec_a = _vec(1, 1, 1, 1)
    vec_b = _vec(2, 2, 2, 2)

    store.add(vectors=[vec_a, vec_b], vector_ids=["a", "b"])
    assert store.total_vectors() == 2

    # Fresh instance, same storage - simulates a different Celery
    # worker/process reloading from disk.
    reloaded = vector_store_factory()
    assert reloaded.total_vectors() == 2

    # Retry the identical batch (e.g. task redelivery/reprocessing):
    # must not grow the index.
    reloaded.add(vectors=[vec_a, vec_b], vector_ids=["a", "b"])
    assert reloaded.total_vectors() == 2

    # Current documented behavior: add() SKIPS an already-present
    # vector_id rather than replacing its stored value - assert that
    # exact behavior, not an assumed "replace" semantic.
    different_vec_a = _vec(9, 9, 9, 9)
    reloaded.add(vectors=[different_vec_a], vector_ids=["a"])
    assert reloaded.total_vectors() == 2

    stored_a = reloaded.index.reconstruct(reloaded.metadata.get_index("a"))
    assert np.allclose(stored_a, vec_a)
    assert not np.allclose(stored_a, different_vec_a)

    # A mixed batch (one duplicate id + one genuinely new id) only
    # appends the new one.
    vec_c = _vec(3, 3, 3, 3)
    reloaded.add(vectors=[vec_b, vec_c], vector_ids=["b", "c"])
    assert reloaded.total_vectors() == 3
    assert reloaded.metadata.exists("c")


def test_replace_removes_targeted_vectors_and_adds_new_ones(vector_store_factory):
    store = vector_store_factory()

    vec_a1 = _vec(1, 0, 0, 0)
    vec_b1 = _vec(0, 1, 0, 0)
    vec_c1 = _vec(0, 0, 1, 0)
    store.replace(
        remove_vector_ids=set(),
        vectors=[vec_a1, vec_b1, vec_c1],
        vector_ids=["a", "b", "c"],
    )
    assert store.total_vectors() == 3

    # An unrelated video's vectors, seeded the same way.
    vec_other_1 = _vec(5, 5, 0, 0)
    vec_other_2 = _vec(0, 5, 5, 0)
    store.replace(
        remove_vector_ids=set(),
        vectors=[vec_other_1, vec_other_2],
        vector_ids=["other-1", "other-2"],
    )
    assert store.total_vectors() == 5

    # Reprocess the first video: it now only has 2 chunks ("c" is
    # gone), and "a"/"b" carry NEW content.
    vec_a2 = _vec(1, 1, 1, 1)
    vec_b2 = _vec(2, 2, 2, 2)
    store.replace(
        remove_vector_ids={"a", "b", "c"},
        vectors=[vec_a2, vec_b2],
        vector_ids=["a", "b"],
    )

    assert store.total_vectors() == 4  # 2 kept ("other-*") + 2 new

    # Removed vector is no longer resolvable via metadata (query
    # operation) at all.
    assert store.metadata.get_index("c") is None
    assert not store.metadata.exists("c")

    # New vectors are retrievable and hold the NEW content.
    idx_a = store.metadata.get_index("a")
    idx_b = store.metadata.get_index("b")
    assert idx_a is not None and idx_b is not None
    assert np.allclose(store.index.reconstruct(idx_a), vec_a2)
    assert np.allclose(store.index.reconstruct(idx_b), vec_b2)

    # The unrelated video's vectors survive untouched.
    idx_other_1 = store.metadata.get_index("other-1")
    idx_other_2 = store.metadata.get_index("other-2")
    assert idx_other_1 is not None and idx_other_2 is not None
    assert np.allclose(store.index.reconstruct(idx_other_1), vec_other_1)
    assert np.allclose(store.index.reconstruct(idx_other_2), vec_other_2)

    # Removed vector is also unreachable via a raw FAISS query: the
    # real FAISS index (not mocked) is queried directly to confirm no
    # position maps back to "c".
    total = store.total_vectors()
    distances, indices = store.index.search(
        np.asarray([vec_c1], dtype=np.float32), total,
    )
    returned_vector_ids = {
        store.metadata.get_vector_id(int(position))
        for position in indices[0]
        if position != -1
    }
    assert "c" not in returned_vector_ids
    assert None not in returned_vector_ids


def test_repeated_replace_with_same_arguments_is_idempotent(vector_store_factory):
    store = vector_store_factory()

    vec_a = _vec(1, 1, 1, 1)
    vec_b = _vec(2, 2, 2, 2)
    store.replace(
        remove_vector_ids=set(),
        vectors=[vec_a, vec_b],
        vector_ids=["a", "b"],
    )
    assert store.total_vectors() == 2

    # Simulate re-running the exact same replacement operation twice
    # in a row (e.g. a retried processing job): the observable state
    # must not accumulate duplicates or drift.
    for _ in range(2):
        store.replace(
            remove_vector_ids={"a", "b"},
            vectors=[vec_a, vec_b],
            vector_ids=["a", "b"],
        )

    assert store.total_vectors() == 2
    idx_a = store.metadata.get_index("a")
    idx_b = store.metadata.get_index("b")
    assert np.allclose(store.index.reconstruct(idx_a), vec_a)
    assert np.allclose(store.index.reconstruct(idx_b), vec_b)


def test_metadata_stays_consistent_with_index_across_reload(vector_store_factory):
    store = vector_store_factory()

    vectors = [_vec(i, i, i, i) for i in range(5)]
    vector_ids = [f"id-{i}" for i in range(5)]
    store.add(vectors=vectors, vector_ids=vector_ids)

    store.replace(
        remove_vector_ids={"id-2"},
        vectors=[_vec(9, 9, 9, 9)],
        vector_ids=["id-5"],
    )

    total = store.total_vectors()
    assert total == 5  # 4 kept + 1 new, one removed from the original 5

    # No holes: every FAISS position resolves to a real vector_id.
    for position in range(total):
        assert store.metadata.get_vector_id(position) is not None

    # Forward/reverse mapping round-trips for every id expected to
    # still be present.
    for vector_id in ["id-0", "id-1", "id-3", "id-4", "id-5"]:
        position = store.metadata.get_index(vector_id)
        assert position is not None
        assert store.metadata.get_vector_id(position) == vector_id

    assert not store.metadata.exists("id-2")

    # A fresh instance reloading from disk sees exactly the same,
    # consistent state.
    reloaded = vector_store_factory()
    assert reloaded.total_vectors() == total
    for vector_id in ["id-0", "id-1", "id-3", "id-4", "id-5"]:
        assert reloaded.metadata.exists(vector_id)
    assert not reloaded.metadata.exists("id-2")
