from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))


from app.database.session import SessionLocal

from app.repositories.transcript import TranscriptRepository
from app.services.transcript import TranscriptService
from app.workers.transcription_worker import TranscriptionWorker


def main():

    db = SessionLocal()

    repository = TranscriptRepository(db)
    service = TranscriptService(repository)

    worker = TranscriptionWorker(service)

    video = ROOT_DIR / "assets" / "demo" / "source2.mp4"

    transcript = worker.process(
        video_id=6,
        video_path=str(video),
    )

    print("=" * 60)
    print("Transcript ID :", transcript.id)
    print("Video ID      :", transcript.video_id)
    print("Language      :", transcript.language)
    print("Word Count    :", transcript.word_count)
    print()
    print(transcript.text)
    print("=" * 60)

    db.close()


if __name__ == "__main__":
    main()