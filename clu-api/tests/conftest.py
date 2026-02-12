import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db, SessionLocal
from app.main import app
from app.models.api_key import ApiKey

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)

# Test API key (raw value and hash)
TEST_API_KEY = "test-api-key-for-clu"
TEST_API_KEY_HASH = hashlib.sha256(TEST_API_KEY.encode()).hexdigest()
TEST_TENANT_ID = "tenant-test-001"


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        # Seed a test API key
        api_key = ApiKey(
            key_hash=TEST_API_KEY_HASH,
            tenant_id=TEST_TENANT_ID,
            name="Test Key",
            is_active=True,
            rate_limit=100,
        )
        session.add(api_key)
        session.commit()
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

    # Override both the route-level and middleware-level DB access
    app.dependency_overrides[get_db] = override_get_db

    # Monkey-patch SessionLocal so auth middleware uses the test DB
    import app.middleware.auth as auth_mod
    original_session_local = auth_mod.SessionLocal
    auth_mod.SessionLocal = TestingSessionLocal

    with TestClient(app) as c:
        # Inject auth header by default
        c.headers["Authorization"] = f"Bearer {TEST_API_KEY}"
        yield c

    auth_mod.SessionLocal = original_session_local
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client(db):
    """A test client with no auth headers for testing auth rejection."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    import app.middleware.auth as auth_mod
    original_session_local = auth_mod.SessionLocal
    auth_mod.SessionLocal = TestingSessionLocal

    with TestClient(app) as c:
        yield c

    auth_mod.SessionLocal = original_session_local
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
