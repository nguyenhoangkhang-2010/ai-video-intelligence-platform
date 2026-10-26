"""
Step 2 of building a human-reviewed evaluation set: go through the
LLM-drafted questions (scripts/draft_eval_questions.py) one by one and
decide. No database or model needed - it only reads and writes JSON.

    python scripts/review_eval_questions.py

For each pending question you see the passage it was drafted from, its
timestamp (open the video there to check), the proposed question and
answer, then choose:

    a  approve as-is
    e  edit the question (and optionally the answer), then approve
    r  reject (not answerable, too vague, wrong...)
    s  skip for now (stays pending)
    q  save and quit

Decisions are saved back into each draft file after every answer, so
you can stop and resume any time. Approved/edited questions are then
compiled into ai/evaluation/fixtures/reviewed_ground_truth.json, ready
for:

    python scripts/benchmark_rag_retrieval.py --fixture ai/evaluation/fixtures/reviewed_ground_truth.json
"""
import argparse
import json
from datetime import date
from pathlib import Path

from ai.evaluation.review import build_dataset


FIXTURES = Path(__file__).parent.parent / "ai" / "evaluation" / "fixtures"


def timecode(seconds) -> str:
    if seconds is None:
        return "--:--"
    seconds = int(seconds)
    return f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}" if seconds >= 3600 else f"{seconds // 60}:{seconds % 60:02d}"


def review_file(path: Path) -> bool:
    """Review one video's drafts. Returns False if the reviewer quit."""
    data = json.loads(path.read_text(encoding="utf-8"))
    chunks = {chunk["vector_id"]: chunk for chunk in data["chunks"]}
    pending = [item for item in data["drafts"] if item.get("status") == "pending"]

    for position, item in enumerate(pending, start=1):
        chunk = chunks.get(item["relevant_vector_ids"][0], {})
        print("\n" + "=" * 72)
        print(f"Video {data['video_id']} - question {position}/{len(pending)} - at {timecode(item.get('start_time'))}")
        print("-" * 72)
        print(chunk.get("chunk_text", "(chunk not found)"))
        print("-" * 72)
        print(f"Q: {item['query']}")
        print(f"A: {item.get('answer') or '(none)'}")

        while True:
            choice = input("[a]pprove  [e]dit  [r]eject  [s]kip  [q]uit > ").strip().lower()
            if choice in {"a", "e", "r", "s", "q"}:
                break

        if choice == "q":
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return False
        if choice == "a":
            item["status"] = "approved"
        elif choice == "r":
            item["status"] = "rejected"
        elif choice == "e":
            question = input("New question (empty = keep): ").strip()
            answer = input("New answer (empty = keep): ").strip()
            if question:
                item["query"] = question
            if answer:
                item["answer"] = answer
            item["status"] = "edited"

        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def compile_dataset(drafts_dir: Path, out: Path) -> None:
    documents, items = [], []
    for path in sorted(drafts_dir.glob("video_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        documents += [
            {"video_id": c["video_id"], "vector_id": c["vector_id"], "chunk_text": c["chunk_text"]}
            for c in data["chunks"]
        ]
        items += data["drafts"]

    dataset = build_dataset(
        items,
        documents,
        comment=(
            "Human-reviewed retrieval evaluation set. Questions were DRAFTED BY AN LLM from real "
            "transcript chunks (scripts/draft_eval_questions.py) and each one was approved or edited "
            "by a person (scripts/review_eval_questions.py) - rejected and unreviewed drafts are "
            f"excluded. Compiled {date.today().isoformat()}."
        ),
    )
    out.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(dataset['queries'])} reviewed question(s) over {len(documents)} chunk(s) -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--drafts-dir", type=Path, default=FIXTURES / "drafts")
    parser.add_argument("--out", type=Path, default=FIXTURES / "reviewed_ground_truth.json")
    parser.add_argument("--compile-only", action="store_true", help="skip reviewing, just rebuild the dataset")
    args = parser.parse_args()

    if not args.compile_only:
        for path in sorted(args.drafts_dir.glob("video_*.json")):
            if not review_file(path):
                break
    compile_dataset(args.drafts_dir, args.out)


if __name__ == "__main__":
    main()
