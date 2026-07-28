from app.models.translation import Translation
from app.repositories.translation import TranslationRepository
from app.schemas.translation import TranslationCreate


class TranslationService:
    """Service for Translation operations."""

    def __init__(
        self,
        repository: TranslationRepository,
    ):
        self.repository = repository

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Translation]:
        """
        Get all translations of a video.
        """
        return self.repository.get_by_video_id(
            video_id,
        )

    def get_by_video_and_language(
        self,
        video_id: int,
        language: str,
    ) -> Translation | None:
        """
        Get translation by video and language.
        """
        return self.repository.get_by_video_and_language(
            video_id,
            language,
        )

    def create_translation(
        self,
        translation_data: TranslationCreate,
    ) -> Translation:
        """
        Create translation if it does not already exist.
        """
        existing = self.repository.get_by_video_and_language(
            video_id=translation_data.video_id,
            language=translation_data.language,
        )

        if existing is not None:
            return existing

        translation = Translation(
            **translation_data.model_dump(),
        )

        return self.repository.create(
            translation,
        )

    def save_translation(
        self,
        translation_data: TranslationCreate,
    ) -> Translation:
        """
        Create or update translation.
        """
        translation = self.repository.get_by_video_and_language(
            video_id=translation_data.video_id,
            language=translation_data.language,
        )

        if translation is None:
            translation = Translation(
                **translation_data.model_dump(),
            )
            return self.repository.create(
                translation,
            )

        translation.subtitle = translation_data.subtitle

        return self.repository.update(
            translation,
        )