from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SUPPORTED_VIDEO_FORMATS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
}

SUPPORTED_AUDIO_FORMATS = {
    ".wav",
    ".mp3",
    ".m4a",
}

MAX_FILENAME_LENGTH = 255

DEFAULT_LANGUAGE = "en"

DEFAULT_CHUNK_SIZE = 512

DEFAULT_CHUNK_OVERLAP = 64