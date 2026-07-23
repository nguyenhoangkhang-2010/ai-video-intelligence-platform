from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from backend.ai.speech import FasterWhisperTranscriber


def main():
    audio = ROOT_DIR / "assets" / "demo" / "source2.mp4"
    transcriber = FasterWhisperTranscriber()
    result = transcriber.transcribe(str(audio))
    print("=" * 50)
    print("Language:", result["language"])
    print()
    print("Transcript:")
    print(result["text"])
    print("=" * 50)


if __name__ == "__main__":
    main()