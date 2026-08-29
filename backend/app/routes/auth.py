import json
import logging
import os
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from google_auth_oauthlib.flow import InstalledAppFlow
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def _validated_preference(value: str | None) -> str:
    allowed = {"local", "device"}
    if isinstance(value, str) and value.lower() in allowed:
        return value.lower()
    return "local"


@auth_bp.post("/register")
def register():
    payload = request.get_json() or {}
    raw_name = payload.get("name")
    raw_email = payload.get("email")
    raw_password = payload.get("password")
    calendar_preference = _validated_preference(
        payload.get("calendar_preference")
        if isinstance(payload.get("calendar_preference"), str)
        else None
    )

    if (
        not isinstance(raw_name, str)
        or not isinstance(raw_email, str)
        or not isinstance(raw_password, str)
    ):
        return jsonify(
            {"message": "Name, email, and password are required"}
        ), 400

    name = raw_name.strip()
    email = raw_email.strip().lower()
    password = raw_password

    if not all([name, email, password]):
        return jsonify(
            {"message": "Name, email, and password are required"}
        ), 400

    if len(name) > 120 or len(email) > 255:
        return jsonify(
            {"message": "Input fields exceed maximum length limits"}
        ), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 409

    user = User(
        name=name, email=email, calendar_preference=calendar_preference
    )
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
    raw_email = payload.get("email")
    raw_password = payload.get("password")

    if not isinstance(raw_email, str) or not isinstance(raw_password, str):
        return jsonify({"message": "Invalid email or password"}), 401

    email = raw_email.strip().lower()
    password = raw_password

    if not email or not password:
        return jsonify({"message": "Invalid email or password"}), 401

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
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

        # Must match EXACTLY callback route in React (App.jsx: /auth/callback)
        # and one of the Authorized redirect URIs in Google Cloud Console.
        frontend_url = (
            current_app.config.get("FRONTEND_URL") or "http://localhost:3000"
        ).rstrip("/")
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
        user_info = session.get(
            "https://www.googleapis.com/userinfo/v2/me"
        ).json()
        email = user_info.get("email")
        name = user_info.get("name") or (
            email.split("@")[0] if email else None
        )

        if not email:
            return jsonify(
                {"message": "Could not retrieve email from Google"}
            ), 400

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
        raw_name = payload.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            return jsonify({"message": "Invalid name"}), 400
        new_name = raw_name.strip()
        if len(new_name) > 120:
            return jsonify(
                {"message": "Name must be 120 characters or fewer"}
            ), 400
        user.name = new_name

    if "calendar_preference" in payload:
        raw_pref = payload.get("calendar_preference")
        pref_str = raw_pref if isinstance(raw_pref, str) else None
        user.calendar_preference = _validated_preference(pref_str)

    if "timezone" in payload:
        raw_tz = payload.get("timezone")
        if not isinstance(raw_tz, str):
            return jsonify({"message": "Invalid timezone"}), 400
        tz_name = raw_tz.strip()
        try:
            ZoneInfo(tz_name)
        except Exception:
            return jsonify({"message": f"Invalid timezone: {tz_name}"}), 400
        user.timezone = tz_name

    db.session.commit()

    return jsonify({"user": user.to_dict()})
