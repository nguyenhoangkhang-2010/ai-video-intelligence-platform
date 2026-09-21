from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import Response

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_flashcard_service
from app.api.deps import get_video_service

from app.services.flashcard import FlashcardService
from app.services.video import VideoService

from app.schemas.flashcard import FlashcardRead

from ai.flashcards.anki_export import AnkiExporter
from ai.flashcards.flashcard_result import Flashcard as FlashcardExportCard


router = APIRouter(
    prefix="/videos",
    tags=["Flashcards"],
)


@router.get(
    "/{video_id}/flashcards",
    response_model=list[FlashcardRead],
)
def get_video_flashcards(
    video_id: int,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
):
    """
    Get flashcards generated for a video, in creation order.

    Raises 404 (via video_service.get_video) if the video does not
    exist or does not belong to the current user. An empty list is a
    valid response.
    """

    # check ownership
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    return flashcard_service.get_by_video_id(
        video_id=video_id,
    )


@router.get(
    "/{video_id}/flashcards/export",
)
def export_video_flashcards(
    video_id: int,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
):
    """
    Export a video's flashcards as a UTF-8 TSV file, importable
    directly into Anki (Import File - Notes separated by newline,
    Fields separated by tab). Reuses ai.flashcards.anki_export.
    AnkiExporter exactly as implemented, with no new dependency
    (e.g. genanki/.apkg) introduced.
    """

    # check ownership
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    flashcards = flashcard_service.get_by_video_id(
        video_id=video_id,
    )

    export_cards = [
        FlashcardExportCard(
            front=flashcard.question,
            back=flashcard.answer,
            difficulty=flashcard.difficulty,
        )
        for flashcard in flashcards
    ]

    content = AnkiExporter().export_to_string(export_cards)

    return Response(
        content=content,
        media_type="text/tab-separated-values; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="video-{video_id}-flashcards.tsv"'
            ),
        },
    )
