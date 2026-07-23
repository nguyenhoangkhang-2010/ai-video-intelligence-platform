from abc import ABC
from abc import abstractmethod


class BaseTranscriber(ABC):
    """Base class for speech-to-text engines."""

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
    ):
        """
        Convert audio into text.
        """
        raise NotImplementedError