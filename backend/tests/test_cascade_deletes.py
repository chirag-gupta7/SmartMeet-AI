from datetime import datetime, timedelta

from sqlalchemy import text

from app.extensions import db
from app.models import Log, Meeting, Note, User


def test_raw_sql_user_delete_cascades_to_related_rows(app):
    """Deleting a user via raw SQL (bypassing the ORM cascade) must still
    remove their meetings, notes, and logs thanks to the DB-level
    ON DELETE CASCADE foreign keys."""

    with app.app_context():
        user = User(name="Cascade Test", email="cascade@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        meeting = Meeting(
            title="Cascade meeting",
            start_time=datetime.utcnow() + timedelta(hours=1),
            duration_minutes=30,
            owner_id=user.id,
        )
        note = Note(content="cascade note", user_id=user.id)
        log = Log(level="info", message="cascade log", user_id=user.id)
        orphan_log = Log(level="info", message="no owner", user_id=None)
        db.session.add_all([meeting, note, log, orphan_log])
        db.session.commit()

        uid = user.id

        # Bypass the ORM entirely.
        db.session.expire_all()
        db.session.execute(text("DELETE FROM users WHERE id = :id"), {"id": uid})
        db.session.commit()

        assert (
            db.session.execute(
                text("SELECT COUNT(*) FROM meetings WHERE owner_id = :id"), {"id": uid}
            ).scalar()
            == 0
        )
        assert (
            db.session.execute(
                text("SELECT COUNT(*) FROM notes WHERE user_id = :id"), {"id": uid}
            ).scalar()
            == 0
        )
        assert (
            db.session.execute(
                text("SELECT COUNT(*) FROM logs WHERE user_id = :id"), {"id": uid}
            ).scalar()
            == 0
        )

        # The unrelated log without a user must be untouched. Its PK is a
        # uuid4 string, so query by message instead of relying on the expired
        # ORM object's attributes.
        remaining = db.session.execute(
            text("SELECT COUNT(*) FROM logs WHERE message = 'no owner'")
        ).scalar()
        assert remaining == 1


def test_orm_delete_still_cascades(app):
    """The existing ORM-level cascade keeps working alongside the DB one."""
    with app.app_context():
        user = User(name="ORM Cascade", email="orm-cascade@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        db.session.add_all(
            [
                Meeting(
                    title="ORM meeting",
                    start_time=datetime.utcnow() + timedelta(hours=2),
                    duration_minutes=15,
                    owner_id=user.id,
                ),
                Note(content="orm note", user_id=user.id),
                Log(level="info", message="orm log", user_id=user.id),
            ]
        )
        db.session.commit()

        db.session.delete(user)
        db.session.commit()

        assert Meeting.query.count() == 0
        assert Note.query.count() == 0
        assert Log.query.count() == 0
