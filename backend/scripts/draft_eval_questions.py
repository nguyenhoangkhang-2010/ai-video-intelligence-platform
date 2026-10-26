"""
Step 1 of building a human-reviewed evaluation set: let the LLM draft
questions from your own processed videos. Nothing drafted here is used
for scoring until a person approves it with
scripts/review_eval_questions.py (see ai.evaluation.review).

Run from backend/ with the backend's .env/database and Ollama reachable
(e.g. inside the api container: `docker compose exec api python
scripts/draft_eval_questions.py ...`):

    python scripts/draft_eval_questions.py --video-ids 2,4,15 --per-video 8

Writes one file per video to ai/evaluation/fixtures/drafts/
(video_<id>.json) holding the video's chunks and the pending questions.
Re-running for a video overwrites its draft file.
"""
import argparse
import json
from pathlib import Path

from ai.evaluation.review import QUESTION_PROMPT, draft_item, parse_draft, pick_chunks
from ai.llm.errors import LLMError
from ai.llm.factory import get_llm_provider
from app.database.session import SessionLocal
from app.repositories.embedding import EmbeddingRepository


DRAFTS_DIR = Path(__file__).parent.parent / "ai" / "evaluation" / "fixtures" / "drafts"


def chunks_for_video(db, video_id: int) -> list[dict]:
    rows = sorted(EmbeddingRepository(db).get_by_video_id(video_id), key=lambda row: row.chunk_index)
    return [
        {
            "video_id": row.video_id,
            "vector_id": row.vector_id,
            "chunk_index": row.chunk_index,
            "chunk_text": row.chunk_text,
            "start_time": getattr(row, "start_time", None),
            "end_time": getattr(row, "end_time", None),
        }
        for row in rows
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--video-ids", required=True, help="comma-separated video ids")
    parser.add_argument("--per-video", type=int, default=8, help="questions to draft per video")
    parser.add_argument("--out-dir", type=Path, default=DRAFTS_DIR)
    args = parser.parse_args()

    llm = get_llm_provider()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        for video_id in [int(v) for v in args.video_ids.split(",") if v.strip()]:
            chunks = chunks_for_video(db, video_id)
            if not chunks:
                print(f"video {video_id}: no embedded chunks (not processed?) - skipped")
                continue

            drafts = []
            for chunk in pick_chunks(chunks, args.per_video):
                try:
                    raw = llm.generate(QUESTION_PROMPT.format(passage=chunk["chunk_text"]))
                except LLMError as error:
                    print(f"video {video_id} chunk {chunk['chunk_index']}: LLM failed ({error}) - skipped")
                    continue
                draft = parse_draft(raw)
                if draft is None:
                    print(f"video {video_id} chunk {chunk['chunk_index']}: unusable LLM output - skipped")
                    continue
                drafts.append(draft_item(chunk, draft))

            out = args.out_dir / f"video_{video_id}.json"
            out.write_text(
                json.dumps({"video_id": video_id, "chunks": chunks, "drafts": drafts}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"video {video_id}: {len(drafts)} draft question(s) -> {out}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
