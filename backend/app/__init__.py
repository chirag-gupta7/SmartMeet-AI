import logging
import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from .config import INSECURE_SECRET_VALUES, Config
from .extensions import bcrypt, db, jwt, migrate
from .routes import register_blueprints
from .services.command_processor import set_flask_app_for_command_processor

logger = logging.getLogger(__name__)

load_dotenv()


def _validate_secrets(app: Flask) -> None:
    """Warn (and in production, refuse to start) when secret keys are left
    at insecure, predictable values (built-in placeholders or the values
    shipped in .env.example)."""
    insecure = [
        name
        for name, known_bad in INSECURE_SECRET_VALUES.items()
        if app.config.get(name) in known_bad
    ]
    if not insecure:
        return

    env = (
        app.config.get("FLASK_ENV")
        or os.getenv("FLASK_ENV")
        or "development"
    )
    message = (
        f"Insecure secret configuration: {', '.join(insecure)} "
        f"is/are still using the built-in placeholder default. "
        f"Set real random values before deploying (e.g. "
        f"`python -c \"import secrets; print(secrets.token_hex(32))\"`)."
    )

    if str(env).lower() == "production":
        raise RuntimeError(message)

    logger.warning(message)


def create_app(config_class: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class or Config())
    _validate_secrets(app)

    # Allow requests from the configured frontend origin(s) and allow
    # credentials (cookies) to be passed back and forth.
    frontend_url = (app.config.get("FRONTEND_URL") or "http://localhost:3000").rstrip("/")
    cors_origins = [frontend_url]
    if "127.0.0.1" in frontend_url:
        cors_origins.append(frontend_url.replace("127.0.0.1", "localhost"))
    elif "localhost" in frontend_url:
        cors_origins.append(frontend_url.replace("localhost", "127.0.0.1"))

    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
    )

    register_extensions(app)
    register_blueprints(app)
    register_healthcheck(app)
    set_flask_app_for_command_processor(app)

    return app


def register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)


def register_healthcheck(app: Flask) -> None:
    @app.get("/api/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}
