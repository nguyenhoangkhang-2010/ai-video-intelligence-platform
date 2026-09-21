import logging

from ai.diarization.speaker_diarization import SpeakerSegment


logger = logging.getLogger(__name__)


class SpeakerMapper:
    """
    Normalizes raw diarization labels (e.g. "SPEAKER_00", "SPEAKER_01"
    - whatever the diarization model assigns, in whatever order) into
    stable, generic labels ("Speaker 1", "Speaker 2", ...), numbered
    by order of first appearance in the audio.

    Never invents person identities (no "Teacher"/"Student"-style
    mapping) - there is no metadata anywhere in this project that
    could justify that, and doing so would be exactly the hardcoded
    business relationship this phase was told to avoid. If richer
    identity metadata becomes available later, this is the one place
    that would need to change.
    """

    def map(
        self,
        segments: list[SpeakerSegment],
    ) -> list[SpeakerSegment]:
        if not segments:
            return []

        label_by_raw_speaker: dict[str, str] = {}

        # Determine numbering by chronological first appearance,
        # regardless of the input list's own order.
        for segment in sorted(segments, key=lambda s: s.start):
            if segment.speaker not in label_by_raw_speaker:
                label_by_raw_speaker[segment.speaker] = (
                    f"Speaker {len(label_by_raw_speaker) + 1}"
                )

        logger.info(
            "Mapped %s raw speaker label(s) to %s normalized label(s).",
            len(label_by_raw_speaker),
            len(set(label_by_raw_speaker.values())),
        )

        return [
            SpeakerSegment(
                speaker=label_by_raw_speaker[segment.speaker],
                start=segment.start,
                end=segment.end,
            )
            for segment in segments
        ]
