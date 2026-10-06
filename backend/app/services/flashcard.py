from app.models.flashcard import Flashcard
from app.repositories.flashcard import FlashcardRepository
from app.schemas.flashcard import FlashcardCreate


class FlashcardService:
    """Service for Flashcard operations."""

    def __init__(
        self,
        repository: FlashcardRepository,
    ):
        self.repository = repository

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Flashcard]:
        """
        Get all flashcards of a video.
        """
        return self.repository.get_by_video_id(
            video_id,
        )

    def delete_by_video_id(
        self,
        video_id: int,
    ) -> None:
        """
        Delete all flashcards belonging to a video.
        """
        self.repository.delete_by_video_id(
            video_id,
        )

    def create_flashcard(
        self,
        flashcard_data: FlashcardCreate,
    ) -> Flashcard:
        """
        Create a flashcard.
        """
        flashcard = Flashcard(
            **flashcard_data.model_dump(),
        )

        return self.repository.create(
            flashcard,
        )

    def replace_for_video(
        self,
        video_id: int,
        flashcards_data: list[FlashcardCreate],
    ) -> list[Flashcard]:
        """
        Atomically replace every flashcard row for `video_id` with
        `flashcards_data` - see FlashcardRepository.replace_for_video
        for the consistency guarantee this provides.
        """
        new_rows = [
            Flashcard(**data.model_dump())
            for data in flashcards_data
        ]

        return self.repository.replace_for_video(
            video_id,
            new_rows,
        )
