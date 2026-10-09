import pytest

from app.config.settings import AppSettings, DatabaseSettings, SecuritySettings, Settings


REAL_LOOKING_SECRET = "a" * 32  # long enough, contains none of the placeholder markers
EXAMPLE_PLACEHOLDER_SECRET = "CHANGE_ME_TO_A_LONG_RANDOM_VALUE"  # verbatim from .env.example


def _settings(environment: str, secret_key: str) -> Settings:
    return Settings(
        app=AppSettings(environment=environment),
        security=SecuritySettings(secret_key=secret_key),
        database=DatabaseSettings(database_url="sqlite:///./test.db"),
    )


def test_rejects_the_exact_env_example_placeholder_in_production():
    """
    Regression test for the real gap this closes: .env.example's own
    SECRET_KEY value is exactly 32 characters, so it satisfies
    min_length=32 while being a publicly-known value in this repo -
    an operator who forgets to change it would otherwise deploy a
    production instance signing every JWT with a secret anyone can
    read on GitHub.
    """
    with pytest.raises(ValueError, match="placeholder"):
        _settings("production", EXAMPLE_PLACEHOLDER_SECRET)


@pytest.mark.parametrize(
    "placeholder_value",
    [
        "CHANGE_ME_TO_A_LONG_RANDOM_VALUE",
        "changeme-changeme-changeme-changeme",
        "this_is_an_example_secret_value_ok",
        "insecure_default_secret_key_value!",
        "please_replace_me_before_deploying",
        "TODO_set_a_real_secret_key_value!!",
    ],
)
def test_rejects_various_placeholder_markers_in_production(placeholder_value):
    assert len(placeholder_value) >= 32
    with pytest.raises(ValueError, match="placeholder"):
        _settings("production", placeholder_value)


def test_accepts_a_real_looking_secret_in_production():
    settings = _settings("production", REAL_LOOKING_SECRET)
    assert settings.security.secret_key == REAL_LOOKING_SECRET


def test_does_not_reject_the_placeholder_outside_production():
    """
    development/testing must keep working with .env.example's
    defaults unchanged - that's exactly what local development is
    expected to use them for.
    """
    for environment in ("development", "testing"):
        settings = _settings(environment, EXAMPLE_PLACEHOLDER_SECRET)
        assert settings.security.secret_key == EXAMPLE_PLACEHOLDER_SECRET
