from dataclasses import dataclass


@dataclass(frozen=True)
class WhisperModelConfig:
    model_name: str
    device: str
    compute_type: str


DEFAULT_WHISPER = WhisperModelConfig(
    model_name="large-v3",
    device="cuda",
    compute_type="float16",
)