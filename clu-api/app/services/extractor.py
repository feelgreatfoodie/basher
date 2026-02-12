"""Per-transcript extraction service via Anthropic SDK."""

import json
import logging

import anthropic

from app.config import settings
from app.prompts.extract import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt

logger = logging.getLogger(__name__)


def extract_transcript(
    filename: str,
    content: str,
    transcript_type: str,
    word_count: int,
) -> dict:
    """Extract structured data from a single transcript using Claude."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Use Opus for large transcripts (>50K words), Sonnet otherwise
    model = settings.synthesis_model if word_count > 50000 else settings.extraction_model

    user_prompt = build_extraction_prompt(filename, content, transcript_type, word_count)

    logger.info("Extracting %s (%d words) with %s", filename, word_count, model)

    message = client.messages.create(
        model=model,
        max_tokens=8192,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text

    # Parse JSON from response (handle markdown code blocks)
    json_text = response_text.strip()
    if json_text.startswith("```"):
        lines = json_text.split("\n")
        lines = lines[1:]  # Remove opening ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Remove closing ```
        json_text = "\n".join(lines)

    extraction = json.loads(json_text)
    return {"data": extraction, "model_used": model}
