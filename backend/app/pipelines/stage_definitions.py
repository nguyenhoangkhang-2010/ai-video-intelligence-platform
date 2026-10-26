"""
The real, fixed list of video-processing stages and their dependency
graph.

Read directly from VideoPipelineService's stage methods' actual
parameters (not the order they happen to be called in, and not the
example graph in the Phase B design brief, which incorrectly assumed
quiz depends on summary - it does not; every stage below depends only
on transcript/transcript_segments, never on another sibling's
persisted output).
"""

METADATA = "metadata"
VISUAL = "visual"
TRANSCRIPTION = "transcription"
SUMMARY = "summary"
EMBEDDING = "embedding"
TRANSLATION = "translation"
QUIZ = "quiz"
CHAPTER = "chapter"
FLASHCARD = "flashcard"

STAGE_ORDER: tuple[str, ...] = (
    METADATA,
    VISUAL,
    TRANSCRIPTION,
    SUMMARY,
    EMBEDDING,
    TRANSLATION,
    QUIZ,
    CHAPTER,
    FLASHCARD,
)

# visual (keyframe analysis, ai.vision) runs before transcription but
# is independent of it and best-effort (never fails): when a video has
# no speech, transcription builds the transcript from visual's
# persisted segments instead of failing, so it must run first.
#
# stage_name -> the one stage it depends on, or None if independent.
# metadata and transcription are both independent of each other.
# summary/embedding/translation/quiz/chapter/flashcard are six
# siblings that each depend ONLY on transcription - never on each
# other - confirmed by reading each stage method's actual parameters
# (transcript: Transcript, or transcript_segments: list[dict] for
# chapter specifically). A failed sibling must never block another
# independent sibling from still being attempted.
STAGE_DEPENDENCIES: dict[str, str | None] = {
    METADATA: None,
    VISUAL: None,
    TRANSCRIPTION: None,
    SUMMARY: TRANSCRIPTION,
    EMBEDDING: TRANSCRIPTION,
    TRANSLATION: TRANSCRIPTION,
    QUIZ: TRANSCRIPTION,
    CHAPTER: TRANSCRIPTION,
    FLASHCARD: TRANSCRIPTION,
}
