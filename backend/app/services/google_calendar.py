import logging
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from flask import current_app

from ..extensions import db
from ..models import User
from ..timeutils import parse_iso_datetime

logger = logging.getLogger(__name__)

NOT_CONNECTED_ERROR = "Google Calendar not connected. Please connect your Google account first."


def _build_service(access_token: str):
    """Create a Google Calendar service client using a raw access token."""
    if not access_token:
        return None

    try:
        creds = Credentials(token=access_token)
        return build("calendar", "v3", credentials=creds, cache_discovery=False)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to initialize Google Calendar service: %s", exc)
        return None


def list_upcoming_events(
    access_token: str, max_results: int = 10, days_ahead: int = 7
) -> List[Dict[str, Any]]:
    """Return upcoming events from the primary calendar."""
    service = _build_service(access_token)
    if not service:
        return []

    time_min = datetime.now(timezone.utc).isoformat()
    time_max = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).isoformat()

    try:
        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return result.get("items", [])
    except HttpError as exc:
        logger.warning("Google Calendar list failed: %s", exc)
        return []


def create_event(access_token: str, event_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create an event in the user's primary calendar."""
    service = _build_service(access_token)
    if not service:
        return None

    try:
        created = (
            service.events()
            .insert(calendarId="primary", body=event_payload, sendUpdates="all")
            .execute()
        )
        return created
    except HttpError as exc:
        logger.warning("Google Calendar insert failed: %s", exc)
        return None


def get_auth_url() -> str:
    """Generate a Google OAuth URL for the frontend to open.

    The default redirect URI must match the React route that handles the
    callback (App.jsx: /auth/callback) - the old ':3000/oauth2callback'
    default pointed at a route that does not exist, dropping the auth code.
    GOOGLE_REDIRECT_URI can still override it for deployments.
    """
    creds_file = os.path.join(os.getcwd(), "credentials.json")
    frontend_url = (
        current_app.config.get("FRONTEND_URL") or "http://localhost:3000"
    ).rstrip("/")
    flow = InstalledAppFlow.from_client_secrets_file(
        creds_file,
        scopes=["https://www.googleapis.com/auth/calendar.events"],
    )
    flow.redirect_uri = os.environ.get(
        "GOOGLE_REDIRECT_URI", f"{frontend_url}/auth/callback"
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return auth_url


def get_service_for_user(user_id: str):
    """Return a calendar service using stored user credentials, or None if not connected."""
    user = db.session.get(User, user_id)
    if not user or not user.google_credentials:
        return None

    try:
        creds = Credentials.from_authorized_user_info(user.google_credentials)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            user.google_credentials = json.loads(creds.to_json())
            db.session.commit()

        return build("calendar", "v3", credentials=creds, cache_discovery=False)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to load calendar creds for user %s: %s", user_id, exc)
        return None


# ------------------------- Per-user operations -------------------------
# These wrap get_service_for_user() so every request runs against the
# credentials of the authenticated user instead of shared token files.


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a raw Google Calendar event into the app's canonical shape."""
    start = event.get("start", {})
    end = event.get("end", {})
    start_val = start.get("dateTime") or start.get("date")
    end_val = end.get("dateTime") or end.get("date")
    summary = event.get("summary") or "Untitled Event"
    is_all_day = bool(start_val) and "T" not in start_val
    date_str = start_val
    start_time = None
    end_time = None

    try:
        if start_val and "T" in start_val:
            # BOLT OPTIMIZATION: Use parse_iso_datetime from app.timeutils to
            # avoid unnecessary string allocations (.replace('Z', ...)).
            start_dt = parse_iso_datetime(start_val)
            date_str = start_dt.strftime("%B %d, %Y")
            start_time = start_dt.strftime("%I:%M %p")
        if end_val and "T" in end_val:
            end_dt = parse_iso_datetime(end_val)
            end_time = end_dt.strftime("%I:%M %p")
    except (ValueError, TypeError) as exc:
        logger.warning("Could not parse event times for %s: %s", event.get("id"), exc)

    return {
        "id": event.get("id"),
        "summary": summary,
        "date": date_str,
        "start_time": start_time,
        "end_time": end_time,
        "is_all_day": is_all_day,
        "htmlLink": event.get("htmlLink"),
        "location": event.get("location"),
    }


def list_upcoming_events_for_user(
    user_id: str,
    max_results: Optional[int] = 10,
    days_ahead: Optional[int] = 7,
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Return upcoming events for a user's primary calendar, or None when the
    user has no stored Google credentials. Events are normalized. Explicit
    time_min/time_max override the derived now/now+days_ahead window.
    """
    service = get_service_for_user(user_id)
    if service is None:
        return None

    now = datetime.now(timezone.utc)
    query_kwargs: Dict[str, Any] = {
        "calendarId": "primary",
        "singleEvents": True,
        "orderBy": "startTime",
    }
    query_kwargs["timeMin"] = (
        time_min.isoformat() if time_min else now.isoformat()
    )
    if time_max:
        query_kwargs["timeMax"] = time_max.isoformat()
    elif days_ahead is not None:
        query_kwargs["timeMax"] = (now + timedelta(days=days_ahead)).isoformat()
    if max_results is not None:
        query_kwargs["maxResults"] = max_results

    try:
        result = service.events().list(**query_kwargs).execute()
    except HttpError as exc:
        logger.warning("Google Calendar list failed for user %s: %s", user_id, exc)
        raise

    return [normalize_event(evt) for evt in result.get("items", [])]


def create_quick_event_for_user(user_id: str, text: str, timezone_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Create an event from natural language via quickAdd, falling back to the
    manual parser when Google rejects the text. Mirrors the result shape of
    the old shared-credential flow. ``timezone_name`` is the user's IANA
    timezone used to interpret natural-language dates in the fallback path.
    """
    service = get_service_for_user(user_id)
    if service is None:
        return {"success": False, "error": NOT_CONNECTED_ERROR}

    text = (text or "").strip()
    from .calendar_event_parser import create_event_manual_parse

    try:
        created = service.events().quickAdd(calendarId="primary", text=text).execute()
    except HttpError as exc:
        if exc.resp.status == 400:
            logger.info("quickAdd failed (%s); falling back to manual parse", exc)
            return create_event_manual_parse(
                text, lambda: get_service_for_user(user_id), timezone_name=timezone_name
            )
        raise

    norm = normalize_event(created)
    message = (
        f"Event created: '{norm['summary']}' on {norm.get('date')}"
        + (f" at {norm['start_time']}" if norm.get("start_time") else "")
    )
    return {"success": True, "event": norm, "message": message}


def query_freebusy_for_user(
    user_id: str, time_min: datetime, time_max: datetime
) -> Optional[List[Dict[str, str]]]:
    """
    Return busy time blocks for the user's primary calendar between
    time_min and time_max, or None when the user is not connected.
    """
    service = get_service_for_user(user_id)
    if service is None:
        return None

    result = (
        service.freebusy()
        .query(
            body={
                "timeMin": time_min.isoformat(),
                "timeMax": time_max.isoformat(),
                "items": [{"id": "primary"}],
            }
        )
        .execute()
    )
    return result.get("calendars", {}).get("primary", {}).get("busy", [])


def get_primary_calendar_for_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Return the user's primary calendarList entry, or None when not connected."""
    service = get_service_for_user(user_id)
    if service is None:
        return None

    calendars = service.calendarList().list(maxResults=10).execute()
    for entry in calendars.get("items", []):
        if entry.get("primary"):
            return entry
    entry = (calendars.get("items") or [None])[0]
    return entry


__all__ = [
    "list_upcoming_events",
    "create_event",
    "get_auth_url",
    "get_service_for_user",
    "normalize_event",
    "list_upcoming_events_for_user",
    "create_quick_event_for_user",
    "query_freebusy_for_user",
    "get_primary_calendar_for_user",
]
