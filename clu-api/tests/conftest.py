import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


SAMPLE_TRANSCRIPT = """Alice: Welcome everyone to the kickoff meeting.
Bob: Thanks Alice. Let's discuss the API design.
Alice: I think we should use REST. It's simpler for our use case.
Bob: I agree. REST with JSON responses.
Alice: Great. Bob, can you set up the CI/CD pipeline by next Friday?
Bob: Sure, I'll handle that.
Alice: One concern - the timeline feels tight. We only have 6 weeks.
Bob: Yeah, that's a risk. We might need to cut scope on the admin panel.
Alice: Let's defer the admin panel to Phase 2 and focus on the core API first.
Bob: Agreed. What about the database? PostgreSQL or MySQL?
Alice: PostgreSQL. Our infrastructure team already supports it.
Bob: Makes sense. Any questions about authentication?
Alice: We haven't decided on OAuth provider yet. Let's revisit that next week.
"""
