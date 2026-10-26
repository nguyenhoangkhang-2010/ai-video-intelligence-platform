"""
Reproducible local performance benchmark for three representative
endpoints: media-token issuance, video metadata retrieval, and a real
RAG query (real retrieval + a real local LLM call via Ollama).

Run from INSIDE the api container, against http://localhost:8000 -
this measures the FastAPI process's own response time, not Docker's
host-port-publishing/network-bridge overhead, and is the honest,
documented environment for every number this script prints (see
docs/benchmarks/performance.md).

Deliberately dependency-free beyond `requests` (already a project
dependency) and the standard library - no new load-testing framework
was added for three endpoints run at modest concurrency.

Usage (inside the api container, backend/ as the working directory,
with a real user id and an already-processed video id that has real
embeddings):
    SECRET_KEY=... python scripts/benchmark_performance.py \
        --user-id 2 --video-id 4
"""
import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE_URL = "http://localhost:8000/api/v1"


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * pct))
    return ordered[index]


def _run_load(label: str, request_fn, total_requests: int, concurrency: int) -> dict:
    latencies: list[float] = []
    errors = 0

    def _one_call():
        start = time.perf_counter()
        try:
            status = request_fn()
            ok = 200 <= status < 300
        except Exception:
            ok = False
        elapsed = time.perf_counter() - start
        return elapsed, ok

    overall_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(_one_call) for _ in range(total_requests)]
        for future in as_completed(futures):
            elapsed, ok = future.result()
            latencies.append(elapsed)
            if not ok:
                errors += 1
    overall_elapsed = time.perf_counter() - overall_start

    return {
        "label": label,
        "total_requests": total_requests,
        "concurrency": concurrency,
        "errors": errors,
        "wall_time_s": overall_elapsed,
        "throughput_rps": total_requests / overall_elapsed if overall_elapsed > 0 else float("nan"),
        "p50_ms": _percentile(latencies, 0.50) * 1000,
        "p95_ms": _percentile(latencies, 0.95) * 1000,
        "p99_ms": _percentile(latencies, 0.99) * 1000,
        "mean_ms": statistics.mean(latencies) * 1000 if latencies else float("nan"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--video-id", type=int, required=True)
    args = parser.parse_args()

    from app.auth.jwt import create_access_token

    access_token = create_access_token(subject=str(args.user_id))
    headers = {"Authorization": f"Bearer {access_token}"}

    def media_token_call():
        r = requests.get(f"{BASE_URL}/videos/{args.video_id}/media-token", headers=headers, timeout=10)
        return r.status_code

    def video_metadata_call():
        r = requests.get(f"{BASE_URL}/videos/{args.video_id}", headers=headers, timeout=10)
        return r.status_code

    rag_queries = [
        "Video này nói về điều gì?",
        "Thông điệp chính của video là gì?",
        "Tóm tắt nội dung video này.",
    ]
    _rag_counter = {"i": 0}

    def rag_query_call():
        query = rag_queries[_rag_counter["i"] % len(rag_queries)]
        _rag_counter["i"] += 1
        r = requests.post(
            f"{BASE_URL}/search/videos/{args.video_id}/rag",
            headers=headers,
            json={"query": query},
            timeout=120,
        )
        return r.status_code

    results = []
    results.append(_run_load("media_token", media_token_call, total_requests=100, concurrency=20))
    results.append(_run_load("video_metadata", video_metadata_call, total_requests=100, concurrency=20))
    results.append(_run_load("rag_query (real LLM call)", rag_query_call, total_requests=10, concurrency=3))

    print(f"\nPerformance benchmark - measured inside the api container, "
          f"against http://localhost:8000, video_id={args.video_id}\n")
    header = f"{'endpoint':<28}{'n':>5}{'conc':>6}{'errors':>8}{'rps':>10}{'p50ms':>10}{'p95ms':>10}{'p99ms':>10}{'meanms':>10}"
    print(header)
    for r in results:
        print(
            f"{r['label']:<28}{r['total_requests']:>5}{r['concurrency']:>6}"
            f"{r['errors']:>8}{r['throughput_rps']:>10.2f}{r['p50_ms']:>10.1f}"
            f"{r['p95_ms']:>10.1f}{r['p99_ms']:>10.1f}{r['mean_ms']:>10.1f}",
        )


if __name__ == "__main__":
    main()
