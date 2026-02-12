"""Seed the database with sample data for development."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models import Project, Transcript

SAMPLE_MEETING = """Alice: Welcome everyone to the kickoff meeting for the new platform.
Bob: Thanks Alice. I've been looking at the requirements doc.
Alice: Great. First decision - we're going with a REST API. It's simpler for our v1.
Bob: Agreed. I also think we should use PostgreSQL for the database.
Alice: Yes, our infra team already supports it. Bob, can you set up CI/CD by next Friday?
Bob: Sure thing. One concern though - the 6 week timeline is tight.
Alice: Let's defer the admin panel to Phase 2 and focus on core API.
Bob: Smart. What about auth? OAuth or custom?
Alice: We haven't decided yet. Let's revisit next week after talking to the security team.
"""

SAMPLE_SPEC = """# Platform API Specification v1

## 1. Requirements

### 1.1 Functional Requirements
- REQ-001: User registration with email/password
- REQ-002: JWT-based authentication
- REQ-003: CRUD operations for projects
- REQ-004: File upload (max 10MB)

### 1.2 Non-Functional Requirements
- REQ-005: API response time < 200ms (p95)
- REQ-006: 99.9% uptime SLA
- REQ-007: GDPR compliance for user data

### 2. Technical Constraints
- Must deploy on AWS (existing infrastructure)
- PostgreSQL 16+ required
- Node.js 20+ or Python 3.11+
"""


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    project = Project(name="Sample Project", description="A sample project for development")
    db.add(project)
    db.commit()
    db.refresh(project)

    for name, content, ttype in [
        ("kickoff-meeting.txt", SAMPLE_MEETING, "meeting"),
        ("api-spec.txt", SAMPLE_SPEC, "spec"),
    ]:
        transcript = Transcript(
            project_id=project.id,
            filename=name,
            content=content,
            transcript_type=ttype,
            word_count=len(content.split()),
        )
        db.add(transcript)

    db.commit()
    db.close()
    print(f"Seeded project: {project.id}")


if __name__ == "__main__":
    seed()
