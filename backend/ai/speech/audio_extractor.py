"""
Canonical audio extraction already lives in app.utils.audio.AudioExtractor
- a working, ffmpeg-python-backed implementation (no hardcoded ffmpeg
path; mono 16kHz WAV, matching what Whisper/VAD expect) already used
in production by app.workers.transcription_worker.TranscriptionWorker.

This module re-exports it under ai.speech so the speech intelligence
pipeline's public surface matches the intended package layout,
without duplicating the extraction logic itself (audit confirmed a
second implementation here would be exactly the duplicate pipeline
this phase was told to avoid).
"""

from app.utils.audio import AudioExtractor

__all__ = [
    "AudioExtractor",
]
