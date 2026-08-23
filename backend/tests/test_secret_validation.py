import logging

import pytest

from app import create_app
from app.config import Config


class DefaultSecretsConfig(Config):
    """Config that leaves both secret keys at their insecure placeholders."""

    TESTING = True
    SECRET_KEY = "change-me"
    JWT_SECRET_KEY = "change-me-too"


class ProdDefaultSecretsConfig(DefaultSecretsConfig):
    FLASK_ENV = "production"


def test_dev_config_with_default_keys_only_warns(app, caplog):
    """Existing dev/test workflow: defaults are allowed, just loudly warned."""
    # The conftest `app` fixture uses real test secrets; build one with the
    # placeholder defaults to confirm no exception is raised.
    application = create_app(DefaultSecretsConfig)

    assert application.config["SECRET_KEY"] == "change-me"

    warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "Insecure secret configuration" in r.getMessage()
    ]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert "SECRET_KEY" in message
    assert "JWT_SECRET_KEY" in message


def test_production_with_default_keys_refuses_to_start():
    with pytest.raises(RuntimeError, match="Insecure secret configuration"):
        create_app(ProdDefaultSecretsConfig)


def test_production_with_real_secrets_starts():
    class ProdRealSecretsConfig(ProdDefaultSecretsConfig):
        SECRET_KEY = "a-real-random-secret"
        JWT_SECRET_KEY = "another-real-random-secret"
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    application = create_app(ProdRealSecretsConfig)
    assert application.config["SECRET_KEY"] == "a-real-random-secret"


def test_existing_test_config_does_not_trip_the_check(app, caplog):
    """conftest.py's TestConfig sets real (non-placeholder) keys, so the
    standard fixtures must not produce any warning."""
    warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "Insecure secret configuration" in r.getMessage()
    ]
    assert warnings == []


class EnvExampleSecretsConfig(Config):
    """Values copied verbatim from the tracked .env.example file."""

    TESTING = True
    SECRET_KEY = "super-secret-key"
    JWT_SECRET_KEY = "smartmeet-jwt-secret"


class ProdEnvExampleSecretsConfig(EnvExampleSecretsConfig):
    FLASK_ENV = "production"


def test_env_example_values_are_flagged_in_dev(caplog):
    application = create_app(EnvExampleSecretsConfig)

    warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "Insecure secret configuration" in r.getMessage()
    ]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert "SECRET_KEY" in message
    assert "JWT_SECRET_KEY" in message


def test_production_with_env_example_values_refuses_to_start():
    with pytest.raises(RuntimeError, match="Insecure secret configuration"):
        create_app(ProdEnvExampleSecretsConfig)
