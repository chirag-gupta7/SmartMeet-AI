"""Tests that voice commands persist Log and Note rows (regression for the
hardcoded Log = None / Note = None bug)."""
from app.extensions import db
from app.models import Log, Note
from app.services.command_processor import VoiceCommandProcessor


def test_take_note_persists_note_for_user(app, user_factory):
    user = user_factory()
    processor = VoiceCommandProcessor(user_id=user.id)

    result = processor.take_note("Remember the standup notes")

    assert result["success"] is True
    note = Note.query.filter_by(user_id=user.id).first()
    assert note is not None
    assert "standup notes" in note.content


def test_take_note_requires_user(app):
    result = VoiceCommandProcessor().take_note("orphan note")
    assert result["success"] is False


def test_process_command_writes_log_rows(app, user_factory, monkeypatch):
    """process_command() logs start/completion to the logs table."""

    def fake_weather(self, location="New York"):
        return {"success": True, "data": {}, "user_message": "Sunny"}

    monkeypatch.setattr(VoiceCommandProcessor, "get_weather", fake_weather)

    user = user_factory()
    processor = VoiceCommandProcessor(user_id=user.id)
    result = processor.process_command("weather", location="Berlin")

    assert result["success"] is True
    logs = Log.query.filter_by(user_id=str(user.id), source="voice_command_processor").all()
    assert len(logs) >= 1
    levels = {log.level for log in logs}
    assert "INFO" in levels


def test_process_command_logs_errors_for_unknown_command(app, user_factory):
    user = user_factory()
    processor = VoiceCommandProcessor(user_id=user.id)
    result = processor.process_command("definitely_not_a_command")

    assert result["success"] is False
    log = Log.query.filter_by(user_id=str(user.id), level="WARNING").first()
    assert log is not None
    assert "unknown" in log.message.lower()
