import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.models import User  # noqa: E402


@pytest.fixture()
def app(tmp_path):
    """Flask app on an isolated sqlite DB; schema created directly for tests."""
    test_db_path = tmp_path / "test.db"

    class TestConfig(Config):
        TESTING = True
        SECRET_KEY = "test-secret"
        JWT_SECRET_KEY = "test-jwt-secret"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{test_db_path}"

    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        # Must run while the app context is still active (the session
        # scope is bound to the app context id).
        _db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def user_factory(app):
    def _make_user(name="Test User", email=None):
        email = email or f"{name.lower().replace(' ', '.')}@example.com"
        user = User(name=name, email=email)
        user.set_password("password123")
        _db.session.add(user)
        _db.session.commit()
        return user

    return _make_user


@pytest.fixture()
def auth_headers(app):
    from flask_jwt_extended import create_access_token

    def _headers_for(user_id):
        token = create_access_token(identity=user_id)
        return {"Authorization": f"Bearer {token}"}

    return _headers_for
