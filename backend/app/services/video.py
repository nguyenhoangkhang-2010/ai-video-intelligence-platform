from app.repositories.video import VideoRepository
from app.types.video_metadata import VideoMetadata

from fastapi import HTTPException
from fastapi import status

from app.models.video import Video

class VideoService:
    """Service for video business logic."""

    def __init__(
        self,
        repository: VideoRepository,
    ):
        self.repository = repository

    def get_user_videos(
        self,
        user_id: int,
    ):
        return self.repository.get_by_owner(
            owner_id=user_id,
        )
        
    def get_video(
        self,
        video_id: int,
        user_id: int,
    ):
        """
        Get a video by ID for the current user.
        """
        video = self.repository.get_by_id_and_owner(
            video_id=video_id,
            owner_id=user_id,
        )

        if video is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )

        return video
    
    def upload_video(
        self,
        owner_id: int,
        title: str,
        filename: str,
        language: str,
        duration: int,
    ) -> Video:
        """
        Save uploaded video metadata.
        """

        video = Video(
            owner_id=owner_id,
            title=title,
            filename=filename,
            language=language,
            duration=duration,
            status="uploaded",
        )

        return self.repository.create(video)
    
    def delete_video(
        self,
        video_id: int,
        user_id: int,
    ):
        success = self.repository.delete_by_owner(
            video_id=video_id,
            owner_id=user_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )

        return {
            "message": "Video deleted successfully",
        }
        
    def update_video(
        self,
        video_id: int,
        user_id: int,
        title: str | None,
        language: str | None,
    ):
        video = self.repository.get_by_id_and_owner(
            video_id=video_id,
            owner_id=user_id,
        )

        if video is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )

        if title is not None:
            video.title = title

        if language is not None:
            video.language = language

        return self.repository.update(video)
    
    def update_duration(
        self,
        video_id: int,
        duration: int,
    ) -> Video:
        """
        Update video duration after metadata extraction.
        """
        video = self.repository.get_by_id(video_id)

        if video is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )

        video.duration = duration

        return self.repository.update(video)
    
    def update_metadata(
        self,
        video_id: int,
        metadata: VideoMetadata,
    ) -> Video:
        """
        Update video metadata extracted by FFprobe.
        """
        video = self.repository.get_by_id(video_id)
        if video is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )
        video.duration = metadata.duration
        return self.repository.update(video)