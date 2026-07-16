import pytest
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Meeting, User


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_meeting_index_and_queries(app):
    """Verify that indices exist on owner_id and start_time,

    and query operations function correctly on the Meeting model.
    """
    with app.app_context():
        # Verify indices exist in metadata
        meetings_table = db.metadata.tables["meetings"]
        indexes = {idx.name for idx in meetings_table.indexes}

        assert "ix_meetings_owner_id" in indexes
        assert "ix_meetings_start_time" in indexes

        # Insert some dummy users and meetings
        user1 = User(name="User 1", email="user1@example.com")
        user1.set_password("securepassword")
        db.session.add(user1)
        db.session.commit()

        import datetime
        from datetime import timezone

        # Create multiple meetings for benchmarking query
        now = datetime.datetime.now(timezone.utc)
        for i in range(10):
            meeting = Meeting(
                title=f"Meeting {i}",
                description="Test performance description",
                start_time=now + datetime.timedelta(hours=i),
                duration_minutes=30,
                owner_id=user1.id,
            )
            db.session.add(meeting)

        db.session.commit()

        # Execute filtered & ordered queries that benefit from indexes
        # 1. Filtering by owner_id
        # 2. Ordering by start_time
        results = (
            Meeting.query.filter_by(owner_id=user1.id)
            .order_by(Meeting.start_time.asc())
            .all()
        )

        assert len(results) == 10
        assert results[0].title == "Meeting 0"
        assert results[9].title == "Meeting 9"
