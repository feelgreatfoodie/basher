"""Cross-reference synthesis service via Anthropic SDK."""

import json
import logging

import anthropic

from app.config import settings
from app.prompts.synthesize import SYNTHESIS_SYSTEM_PROMPT, build_synthesis_prompt

logger = logging.getLogger(__name__)


def synthesize_extractions(
    extractions: list[dict],
    semantic_conflicts: list[dict] | None = None,
) -> dict:
    """Cross-reference all extraction data and produce unified analysis.

    If semantic_conflicts are provided (from ChromaDB similarity search),
    they are included as hints for the LLM to investigate further.
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    extractions_json = json.dumps(extractions, indent=2)
    user_prompt = build_synthesis_prompt(extractions_json, semantic_conflicts=semantic_conflicts)

    logger.info("Synthesizing %d extractions with %s", len(extractions), settings.synthesis_model)

    message = client.messages.create(
        model=settings.synthesis_model,
        max_tokens=8192,
        system=SYNTHESIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text

    # Parse JSON from response (handle markdown code blocks)
    json_text = response_text.strip()
    if json_text.startswith("```"):
        lines = json_text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        json_text = "\n".join(lines)

    synthesis = json.loads(json_text)
    return synthesis
