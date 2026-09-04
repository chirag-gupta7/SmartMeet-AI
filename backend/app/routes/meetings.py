from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Meeting
from ..timeutils import to_naive_utc

meetings_bp = Blueprint("meetings", __name__)


@meetings_bp.get("")
@jwt_required()
def list_meetings():
    user_id = get_jwt_identity()
    meetings = (
        Meeting.query.filter_by(owner_id=user_id)
        .order_by(Meeting.start_time.asc())
        .all()
    )
    return jsonify({"meetings": [m.to_dict() for m in meetings]})


@meetings_bp.post("")
@jwt_required()
def create_meeting():
    payload = request.get_json() or {}
    user_id = get_jwt_identity()

    raw_title = payload.get("title")
    start_time = payload.get("start_time")
    description = payload.get("description")

    if (
        not isinstance(raw_title, str)
        or not raw_title.strip()
        or not start_time
    ):
        return jsonify({"message": "Title and start_time are required"}), 400

    title = raw_title.strip()
    if len(title) > 255:
        return jsonify(
            {"message": "Title must be 255 characters or fewer"}
        ), 400

    if description is not None:
        if not isinstance(description, str):
            return jsonify({"message": "Description must be a string"}), 400
        if len(description) > 10000:
            return jsonify(
                {"message": "Description must be 10,000 characters or fewer"}
            ), 400

    try:
        duration = int(payload.get("duration", 30))
    except (TypeError, ValueError):
        return jsonify(
            {"message": "duration must be an integer number of minutes"}
        ), 400
    if duration <= 0:
        return jsonify(
            {"message": "duration must be a positive number of minutes"}
        ), 400

    try:
        start_dt = to_naive_utc(datetime.fromisoformat(start_time))
    except ValueError:
        return jsonify({"message": "start_time must be ISO8601"}), 400

    meeting = Meeting(
        title=title,
        description=description,
        start_time=start_dt,
        duration_minutes=duration,
        owner_id=user_id,
    )

    db.session.add(meeting)
    db.session.commit()

    return jsonify({"meeting": meeting.to_dict()}), 201


@meetings_bp.put("/<meeting_id>")
@jwt_required()
def update_meeting(meeting_id: str):
    payload = request.get_json() or {}
    user_id = get_jwt_identity()

    meeting = Meeting.query.filter_by(
        id=meeting_id, owner_id=user_id
    ).first_or_404()

    if "title" in payload:
        raw_title = payload.get("title")
        if not isinstance(raw_title, str) or not raw_title.strip():
            return jsonify({"message": "Title cannot be empty"}), 400
        new_title = raw_title.strip()
        if len(new_title) > 255:
            return jsonify(
                {"message": "Title must be 255 characters or fewer"}
            ), 400
        meeting.title = new_title

    if "description" in payload:
        raw_desc = payload.get("description")
        if raw_desc is not None:
            if not isinstance(raw_desc, str):
                return jsonify(
                    {"message": "Description must be a string"}
                ), 400
            if len(raw_desc) > 10000:
                return jsonify(
                    {
                        "message": (
                            "Description must be 10,000 characters or fewer"
                        )
                    }
                ), 400
            meeting.description = raw_desc
        else:
            meeting.description = None

    if "duration" in payload:
        try:
            duration = int(payload["duration"])
        except (TypeError, ValueError):
            return jsonify(
                {"message": "duration must be an integer number of minutes"}
            ), 400
        if duration <= 0:
            return jsonify(
                {"message": "duration must be a positive number of minutes"}
            ), 400
        meeting.duration_minutes = duration
    if "start_time" in payload:
        try:
            meeting.start_time = to_naive_utc(
                datetime.fromisoformat(payload["start_time"])
            )
        except ValueError:
            return jsonify({"message": "start_time must be ISO8601"}), 400

    db.session.commit()

    return jsonify({"meeting": meeting.to_dict()})


@meetings_bp.delete("/<meeting_id>")
@jwt_required()
def delete_meeting(meeting_id: str):
    user_id = get_jwt_identity()
    meeting = Meeting.query.filter_by(
        id=meeting_id, owner_id=user_id
    ).first_or_404()

    db.session.delete(meeting)
    db.session.commit()

    return jsonify({"deleted": meeting_id})
