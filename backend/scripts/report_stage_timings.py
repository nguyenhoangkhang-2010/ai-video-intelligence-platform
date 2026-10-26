"""
How long each processing stage really took, per video, from the
pipeline's own records (processing_stages.started_at/finished_at of
each video's latest processing job). No instrumentation or re-run
needed: every processed video is already a measurement.

Run where the backend's database is reachable, e.g. inside the api
container (the image doesn't ship scripts/, so copy it in first):

    docker compose cp backend/scripts/report_stage_timings.py api:/app/backend/scripts/
    docker compose exec api python scripts/report_stage_timings.py --video-ids 19,20

Prints a markdown table: one column per video, one row per stage,
plus the total and the share spent in LLM-backed stages.
"""
import argparse
from collections import defaultdict
from collections.abc import Iterable

# Stages whose time is (almost) all LLM generation - see
# app/pipelines/video_pipeline.py.
LLM_STAGES = frozenset({"summary", "translation", "quiz", "chapter", "flashcard"})

STAGE_ORDER = (
    "metadata", "transcription", "summary", "embedding",
    "translation", "quiz", "chapter", "flashcard",
)

QUERY = """
    SELECT v.id AS video_id, v.duration AS video_seconds, s.stage_name AS stage,
           EXTRACT(EPOCH FROM s.finished_at - s.started_at) AS seconds
    FROM processing_stages s
    JOIN processing_jobs j ON j.id = s.processing_job_id
    JOIN videos v ON v.id = j.video_id
    WHERE v.id = ANY(:video_ids)
      AND upper(s.status) = 'COMPLETED'
      AND s.started_at IS NOT NULL AND s.finished_at IS NOT NULL
      AND j.id = (SELECT max(j2.id) FROM processing_jobs j2 WHERE j2.video_id = v.id)
"""


def fmt(seconds: float) -> str:
    seconds = int(round(seconds))
    return f"{seconds // 60}m {seconds % 60:02d}s" if seconds >= 60 else f"{seconds}s"


def render(rows: Iterable[dict]) -> str:
    """Markdown table from rows of {video_id, video_seconds, stage, seconds}."""
    by_video: dict[int, dict[str, float]] = defaultdict(dict)
    lengths: dict[int, float] = {}
    for row in rows:
        by_video[row["video_id"]][row["stage"]] = float(row["seconds"])
        lengths[row["video_id"]] = float(row["video_seconds"] or 0)

    videos = sorted(by_video)
    if not videos:
        return "No completed stages found for those videos."

    stages = [s for s in STAGE_ORDER if any(s in by_video[v] for v in videos)]
    stages += sorted({s for v in videos for s in by_video[v]} - set(stages))

    header = "| Stage | " + " | ".join(f"Video {v} ({fmt(lengths[v])} long)" for v in videos) + " |"
    lines = [header, "|---" * (len(videos) + 1) + "|"]
    for stage in stages:
        cells = [fmt(by_video[v][stage]) if stage in by_video[v] else "-" for v in videos]
        lines.append(f"| {stage} | " + " | ".join(cells) + " |")

    totals = {v: sum(by_video[v].values()) for v in videos}
    llm = {v: sum(t for s, t in by_video[v].items() if s in LLM_STAGES) for v in videos}
    lines.append("| **Total** | " + " | ".join(f"**{fmt(totals[v])}**" for v in videos) + " |")
    lines.append(
        "| LLM stages share | "
        + " | ".join(f"{llm[v] / totals[v]:.0%}" if totals[v] else "-" for v in videos)
        + " |"
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--video-ids", required=True, help="comma-separated video ids")
    args = parser.parse_args()

    from sqlalchemy import text

    from app.database.session import SessionLocal

    video_ids = [int(v) for v in args.video_ids.split(",") if v.strip()]
    db = SessionLocal()
    try:
        rows = db.execute(text(QUERY), {"video_ids": video_ids}).mappings().all()
    finally:
        db.close()
    print(render(rows))


if __name__ == "__main__":
    main()
