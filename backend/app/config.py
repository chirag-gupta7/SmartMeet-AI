import os
from datetime import timedelta

# Placeholder secrets used when the env vars are unset — fine for local
# development, but create_app() warns loudly about them and refuses to boot
# with them when FLASK_ENV=production.
DEFAULT_SECRET_KEY = "change-me"
DEFAULT_JWT_SECRET_KEY = "change-me-too"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///smartmeet.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", DEFAULT_JWT_SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    CORS_ORIGINS = [FRONTEND_URL]
