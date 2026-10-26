from pydantic import BaseModel

from app.schemas.processing_job import ProcessingJobRead
from app.schemas.quiz import QuizRead
from app.schemas.summary import SummaryRead
from app.schemas.transcript import TranscriptRead
from app.schemas.translation import TranslationRead
from app.schemas.video import VideoRead


class MeetingResponse(BaseModel):
    """
    Aggregated meeting view.

    There is no separate Meeting domain in this codebase - a meeting
    recording is a Video. This composes the existing per-resource read
    schemas into a single response for a meeting workspace UI, instead
    of duplicating the video/transcript/summary/translation/quiz
    endpoints that already exist under their own resource paths.
    """

    video: VideoRead
    processing_jobs: list[ProcessingJobRead]
    transcript: TranscriptRead | None
    summaries: list[SummaryRead]
    translations: list[TranslationRead]
    quizzes: list[QuizRead]
