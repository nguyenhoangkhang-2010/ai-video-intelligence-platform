import base64
from unittest.mock import MagicMock

from ai.llm.errors import LLMTimeoutError, LLMUnavailableError
from ai.vision.describer import FRAME_PROMPT, FrameDescriber, parse_frame_output
from ai.vision.keyframes import Keyframe


def _frames(tmp_path, count):
    frames = []
    for index in range(count):
        path = tmp_path / f"{index}.jpg"
        path.write_bytes(f"image-{index}".encode())
        frames.append(Keyframe(time=float(index * 10), path=str(path)))
    return frames


def _client(*outputs):
    client = MagicMock()
    client.model = "qwen2.5vl:3b"
    client.generate.side_effect = list(outputs)
    return client


# ---- parse_frame_output ----

def test_parses_text_and_description():
    raw = '```json\n{"text": "Lạm phát 2024\\n3,6%", "description": "Một slide có biểu đồ."}\n```'

    assert parse_frame_output(raw) == ("Lạm phát 2024\n3,6%", "Một slide có biểu đồ.")


def test_rejects_unusable_output():
    assert parse_frame_output("không phải json") is None
    assert parse_frame_output('{"text": "", "description": ""}') is None


# ---- describe ----

def test_sends_each_frame_as_base64_image(tmp_path):
    client = _client('{"text": "A", "description": "a"}', '{"text": "", "description": "b"}')

    described = FrameDescriber(client=client).describe(_frames(tmp_path, 2))

    assert [(d.time, d.text, d.description) for d in described] == [(0.0, "A", "a"), (10.0, "", "b")]
    first_call = client.generate.call_args_list[0]
    assert first_call.args[0] == FRAME_PROMPT
    assert first_call.kwargs["images"] == [base64.b64encode(b"image-0").decode("ascii")]


def test_skips_a_frame_that_fails_or_is_unusable(tmp_path):
    client = _client(LLMTimeoutError("slow"), "garbage", '{"text": "C", "description": "c"}')

    described = FrameDescriber(client=client).describe(_frames(tmp_path, 3))

    assert [d.text for d in described] == ["C"]


def test_stops_early_when_the_model_is_unavailable(tmp_path):
    client = _client(LLMUnavailableError("HTTP 404"), '{"text": "never", "description": "x"}')

    assert FrameDescriber(client=client).describe(_frames(tmp_path, 2)) == []
    assert client.generate.call_count == 1
