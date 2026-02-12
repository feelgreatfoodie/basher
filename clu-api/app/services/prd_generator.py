"""PRD generation from analysis results."""

import json
import logging

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

PRD_SYSTEM_PROMPT = """You are a technical writer. Convert analysis results into a Basher-compatible PRD document.

The PRD format:
- Title and overview
- User stories with acceptance criteria
- Technical considerations
- Open questions (from unresolved conflicts)

Output clean markdown that can be fed directly to /basher-convert."""


def generate_prd(analysis_results: dict) -> str:
    """Generate a Basher-compatible PRD markdown from analysis results."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    user_prompt = f"""Convert this CLU analysis into a Basher-compatible PRD.

**Rules:**
- Highest-consensus requirements become the first user stories
- Unresolved conflicts become "Open Questions" section
- Technical constraints become "Technical Considerations"
- Each user story needs acceptance criteria

**Analysis data:**

{json.dumps(analysis_results, indent=2)}"""

    logger.info("Generating PRD with %s", settings.synthesis_model)

    message = client.messages.create(
        model=settings.synthesis_model,
        max_tokens=8192,
        system=PRD_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return message.content[0].text
