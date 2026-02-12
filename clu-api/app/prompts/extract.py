"""Extraction prompt builder — mirrors prompts/clu-subagent-extract.md logic."""

import logging

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a CLU extraction engine. You extract structured data from a single transcript.

Be exhaustive — extract EVERYTHING, even implied constraints and subtle references.
Use exact quotes for supporting evidence.
Distinguish confidence: explicit decisions are "high", implied ones are "medium" or "low".
Identify participant roles from context if not stated.
Flag ambiguous items as open questions."""

EXTRACTION_SCHEMA = """{
  "source": { "name": "<filename>", "type": "<type>", "wordCount": <count> },
  "participants": [{ "name": "Full Name", "role": "PM|Engineer|Designer|Stakeholder|Executive|Unknown", "aliases": [], "inferredFromContext": false }],
  "decisions": [{ "what": "description", "decidedBy": [], "confidence": "high|medium|low", "supportingQuotes": [], "context": "", "revisits": false }],
  "actionItems": [{ "action": "description", "owner": "Name or Unassigned", "deadline": null, "status": "open|in-progress|done", "supportingQuote": "" }],
  "requirements": [{ "description": "", "type": "functional|non-functional|constraint", "priority": "critical|high|medium|low", "mentionedBy": [], "supportingQuotes": [], "category": "auth|data|api|ui|infrastructure|security|performance|other" }],
  "technicalConstraints": [{ "constraint": "", "explicit": true, "source": "", "supportingQuote": "" }],
  "openQuestions": [{ "question": "", "raisedBy": "", "context": "", "suggestedAnswers": [] }],
  "risks": [{ "risk": "", "flaggedBy": "", "severity": "critical|high|medium|low", "mitigation": null }],
  "deferredItems": [{ "item": "", "deferredTo": "", "reason": "", "supportingQuote": "" }]
}"""


def build_extraction_prompt(
    filename: str,
    content: str,
    transcript_type: str,
    word_count: int,
    template_name: str | None = None,
) -> str:
    """Build the user prompt for per-transcript extraction.

    If template_name is provided, loads the template from the extraction_templates
    service and uses its schema and guidelines instead of the default full extraction.
    """
    if template_name:
        try:
            from app.services.extraction_templates import (
                get_template,
                build_schema_for_template,
                get_template_guidelines,
            )
            template = get_template(template_name)
            schema_str = build_schema_for_template(template_name)
            guidelines = get_template_guidelines(template_name)
            sections = template.get("sections", [])
            section_hint = f"**Focus sections:** {', '.join(sections)}\n" if sections else ""

            return f"""Extract structured data from this transcript using the **{template['name']}** template.

**Transcript:** {filename}
**Type:** {transcript_type}
**Word Count:** {word_count}

**Template:** {template['name']} — {template.get('description', '')}
{section_hint}
**Guidelines:** {guidelines}

**Extraction guidelines by type:**
- meeting: Focus on decisions, action items, who said what, agreements vs disagreements
- interview: Requirements from stakeholder perspective, priorities, pain points
- slack: Quick decisions, links to resources, informal agreements
- spec: Formal requirements, technical constraints, acceptance criteria
- other: Best effort across all categories

**Output format:** Return ONLY valid JSON matching this schema:
{schema_str}

**Transcript content:**

{content}"""
        except ValueError:
            logger.warning("Template '%s' not found, using default extraction", template_name)

    return f"""Extract structured data from this transcript.

**Transcript:** {filename}
**Type:** {transcript_type}
**Word Count:** {word_count}

**Extraction guidelines by type:**
- meeting: Focus on decisions, action items, who said what, agreements vs disagreements
- interview: Requirements from stakeholder perspective, priorities, pain points
- slack: Quick decisions, links to resources, informal agreements
- spec: Formal requirements, technical constraints, acceptance criteria
- other: Best effort across all categories

**Output format:** Return ONLY valid JSON matching this schema:
{EXTRACTION_SCHEMA}

**Transcript content:**

{content}"""
