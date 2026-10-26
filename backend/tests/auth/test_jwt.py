from datetime import timedelta

import pytest
from jose import JWTError

from app.auth.jwt import create_access_token
from app.auth.jwt import create_media_token
from app.auth.jwt import decode_token


def test_create_media_token_roundtrip_carries_scope_and_video_id():
    token = create_media_token(user_id=7, video_id=42)

    payload = decode_token(token)

    assert payload["sub"] == "7"
    assert payload["video_id"] == 42
    assert payload["scope"] == "media"


def test_create_media_token_rejects_after_real_expiry():
    """
    Not a mocked JWTError - an actually-expired token (negative
    expires_delta) must fail real decode_token verification, proving
    the expiry claim is enforced by the jose library itself.
    """
    token = create_media_token(
        user_id=7,
        video_id=42,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(JWTError):
        decode_token(token)


def test_create_media_token_is_distinct_from_access_token():
    """
    A main access token for the same user carries no scope/video_id
    claims - it must never be mistakeable for a media token by a
    caller that only inspects `sub`.
    """
    access_token = create_access_token(subject="7")

    payload = decode_token(access_token)

    assert payload.get("scope") != "media"
    assert "video_id" not in payload


def test_create_media_token_default_expiry_matches_settings():
    from app.config.settings import settings

    token = create_media_token(user_id=7, video_id=42)
    payload = decode_token(token)

    # exp is seconds since epoch; just confirm it's in the future and
    # roughly consistent with the configured short lifetime rather than
    # the main access token's much longer one.
    import time

    remaining = payload["exp"] - time.time()

    assert 0 < remaining <= settings.security.media_token_expire_seconds + 5
