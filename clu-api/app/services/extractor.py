"""Per-transcript extraction service via Anthropic SDK."""

import json
import logging

import anthropic

from app.config import settings
from app.prompts.extract import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from app.services.cache import get_cached_extraction, set_cached_extraction

logger = logging.getLogger(__name__)


def _parse_json_response(response_text: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
    json_text = response_text.strip()
    if json_text.startswith("```"):
        lines = json_text.split("\n")
        lines = lines[1:]  # Remove opening ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Remove closing ```
        json_text = "\n".join(lines)
    return json.loads(json_text)


def extract_transcript(
    filename: str,
    content: str,
    transcript_type: str,
    word_count: int,
    template_name: str | None = None,
) -> dict:
    """Extract structured data from a single transcript using Claude."""
    # Use Opus for large transcripts (>50K words), Sonnet otherwise
    model = settings.synthesis_model if word_count > 50000 else settings.extraction_model

    # Check Redis cache first
    cached = get_cached_extraction(content, model)
    if cached is not None:
        logger.info("Using cached extraction for %s", filename)
        return {"data": cached, "model_used": model, "cached": True}

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    user_prompt = build_extraction_prompt(
        filename, content, transcript_type, word_count, template_name=template_name
    )

    logger.info("Extracting %s (%d words) with %s", filename, word_count, model)

    message = client.messages.create(
        model=model,
        max_tokens=8192,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text
    extraction = _parse_json_response(response_text)

    # Cache the result in Redis
    set_cached_extraction(content, model, extraction)

    return {"data": extraction, "model_used": model, "cached": False}
