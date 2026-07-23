from pathlib import Path
import sys

# backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# project root (để sau này nếu cần import ai)
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from app.utils.audio import AudioExtractor

def main():
    extractor = AudioExtractor()
    video = ROOT_DIR / "assets" / "demo" / "source2.mp4"
    output = ROOT_DIR / "assets" / "demo" / "source2.wav"
    extractor.extract(
        str(video),
        str(output),
    )
    print("Done!")
    print(output)


if __name__ == "__main__":
    main()