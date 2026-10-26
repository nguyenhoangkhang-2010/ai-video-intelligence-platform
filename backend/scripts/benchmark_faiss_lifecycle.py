"""
Measures the real cost of VectorStore's per-request full-index-reload
pattern (ai/embedding/vector_store.py::VectorStore.__init__ calls
self.builder.load_index() unconditionally on every construction, and
SemanticSearchService constructs a fresh VectorStore per request via
get_rag_pipeline - see ADR 0008) at synthetic scales this deployment's
real index (currently ~37KB, 7 vectors) is nowhere near.

Uses the real IndexBuilder/faiss.write_index/faiss.read_index code
path, pointed at a throwaway path (never touches the real production
index at storage/faiss/video.index) with real random 1024-dim
float32 vectors (BGE-M3's real embedding dimension) - clearly
synthetic data, used only because this deployment has nowhere near
enough real embedded content to reach these sizes, as documented in
docs/benchmarks/rag-evaluation.md.

Usage (inside the api container, backend/ as the working directory):
    python scripts/benchmark_faiss_lifecycle.py
"""
import statistics
import tempfile
import time
from pathlib import Path

import numpy as np

from ai.embedding.index_builder import IndexBuilder

DIMENSION = 1024
SCALES = [1_000, 10_000, 50_000, 100_000]
SEARCH_REPEATS = 20


def _build_synthetic_index(n_vectors: int, index_path: Path):
    builder = IndexBuilder(dimension=DIMENSION, index_path=index_path)
    index = builder.create_index()
    rng = np.random.default_rng(seed=42)
    vectors = rng.standard_normal((n_vectors, DIMENSION)).astype(np.float32)
    index.add(vectors)
    builder.save_index(index)
    return builder, vectors[0:1]


def main() -> None:
    print(f"\nFAISS lifecycle benchmark - SYNTHETIC data (real IndexBuilder/"
          f"faiss.write_index/faiss.read_index code path, random {DIMENSION}-dim "
          f"vectors). This deployment's real index has 7 vectors; these sizes "
          f"are synthetic stand-ins for what a larger deployment's index would "
          f"look like.\n")
    header = f"{'n_vectors':>10}{'index_size_mb':>15}{'load_time_ms':>15}{'search_time_ms':>16}{'total_ms':>12}"
    print(header)

    with tempfile.TemporaryDirectory() as tmp_dir:
        for n_vectors in SCALES:
            index_path = Path(tmp_dir) / f"bench_{n_vectors}.index"
            builder, query_vector = _build_synthetic_index(n_vectors, index_path)

            index_size_mb = index_path.stat().st_size / (1024 * 1024)

            load_times = []
            search_times = []
            for _ in range(SEARCH_REPEATS):
                load_start = time.perf_counter()
                index = builder.load_index()
                load_times.append(time.perf_counter() - load_start)

                search_start = time.perf_counter()
                index.search(query_vector, 5)
                search_times.append(time.perf_counter() - search_start)

            load_ms = statistics.median(load_times) * 1000
            search_ms = statistics.median(search_times) * 1000
            print(
                f"{n_vectors:>10}{index_size_mb:>15.2f}{load_ms:>15.2f}"
                f"{search_ms:>16.2f}{(load_ms + search_ms):>12.2f}",
            )


if __name__ == "__main__":
    main()
