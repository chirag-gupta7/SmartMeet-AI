from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import bcrypt, db, jwt, migrate
from .routes import register_blueprints
from .services.command_processor import set_flask_app_for_command_processor

load_dotenv()


def create_app(config_class: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class or Config())

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
