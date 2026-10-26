from pathlib import Path

import ffmpeg


class AudioExtractor:
    """Extract audio from video files."""

    def extract(
        self,
        video_path: str,
        output_path: str,
    ) -> str:
        """
        Extract mono 16kHz WAV audio from a video.
        Args:
            video_path: Input video file.
            output_path: Output wav file.
        Returns:
            Output wav path.
        """
        Path(output_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        (
            ffmpeg
            .input(video_path)
            .output(
                output_path,
                ac=1,
                ar=16000,
                format="wav",
            )
            .overwrite_output()
            .run(
                quiet=True,
            )
        )
        return output_path