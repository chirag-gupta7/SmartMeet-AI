import json
import logging
import os
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from google_auth_oauthlib.flow import InstalledAppFlow
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def _validated_preference(value: str | None) -> str:
    allowed = {"local", "device"}
    if value and value.lower() in allowed:
        return value.lower()
    return "local"


@auth_bp.post("/register")
def register():
    payload = request.get_json() or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")
    calendar_preference = _validated_preference(payload.get("calendar_preference"))

    if not all([name, email, password]):
        return jsonify({"message": "Name, email, and password are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 409

    user = User(name=name, email=email, calendar_preference=calendar_preference)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        # Two concurrent registrations can pass the pre-check above; the
        # unique constraint is the real guard.
        db.session.rollback()
        return jsonify({"message": "Email already registered"}), 409

    access_token = create_access_token(identity=user.id)
    return jsonify({"token": access_token, "user": user.to_dict()})


@auth_bp.post("/login")
def login():
    payload = request.get_json() or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not password or not user.check_password(password):
        return jsonify({"message": "Invalid email or password"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({"token": access_token, "user": user.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def current_user():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify({"user": user.to_dict()})


@auth_bp.post("/google")
def google_login():
    payload = request.get_json() or {}
    code = payload.get("code")

    if not code:
        return jsonify({"message": "Authorization code is required"}), 400

    try:
        creds_file = os.path.join(os.getcwd(), "credentials.json")

        # Must match EXACTLY the callback route in React (App.jsx: /auth/callback)
        # and one of the Authorized redirect URIs in Google Cloud Console.
        frontend_url = (current_app.config.get("FRONTEND_URL") or "http://localhost:3000").rstrip("/")
        redirect_uri = f"{frontend_url}/auth/callback"

        # Debug logging to track what URI is being used
        logger.debug("Google login using redirect_uri: %s", redirect_uri)

        flow = InstalledAppFlow.from_client_secrets_file(
            creds_file,
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/calendar.events",
            ],
            redirect_uri=redirect_uri,
        )

        flow.fetch_token(code=code)
        creds = flow.credentials

        session = flow.authorized_session()
        user_info = session.get("https://www.googleapis.com/userinfo/v2/me").json()
        email = user_info.get("email")
        name = user_info.get("name") or (email.split("@")[0] if email else None)

        if not email:
            return jsonify({"message": "Could not retrieve email from Google"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            import secrets

            user = User(name=name or email, email=email)
            user.set_password(secrets.token_hex(16))
            db.session.add(user)

        user.google_credentials = json.loads(creds.to_json())
        db.session.commit()

        access_token = create_access_token(identity=user.id)
        return jsonify(
            {
                "token": access_token,
                "user": user.to_dict(),
                "calendar_connected": True,
            }
        )

    except Exception as exc:  # pragma: no cover
        # Log OAuth errors server-side, but never echo raw exception text to
        # the client (it can leak redirect URIs, token endpoints, etc.).
        logger.warning("Google OAuth login failed: %s", exc)
        return jsonify(
            {"message": "Google authentication failed. Please try again."}
        ), 500


@auth_bp.patch("/me")
@jwt_required()
def update_user():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    payload = request.get_json() or {}

    if "name" in payload:
        new_name = (payload.get("name") or "").strip()
        if new_name:
            user.name = new_name

    if "calendar_preference" in payload:
        user.calendar_preference = _validated_preference(payload.get("calendar_preference"))

    if "timezone" in payload:
        tz_name = (payload.get("timezone") or "UTC").strip()
        try:
            ZoneInfo(tz_name)
        except Exception:
            return jsonify({"message": f"Invalid timezone: {tz_name}"}), 400
        user.timezone = tz_name

    db.session.commit()

    return jsonify({"user": user.to_dict()})
