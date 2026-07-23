from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))

from app.workers.transcription_worker import TranscriptionWorker


def main():

    worker = TranscriptionWorker()
    video = ROOT_DIR / "assets/demo/source2.mp4"
    result = worker.process(
        str(video),
    )
    print("=" * 50)
    print("Language:")
    print(result["language"])
    print()
    print("Transcript:")
    print(result["text"])
    print("=" * 50)


if __name__ == "__main__":
    main()