"""Configurable extraction templates for CLU analysis.

Templates define which entity types to extract and the JSON schema
the LLM should follow. Ships with three built-in templates:
  - default: all categories (full extraction)
  - requirements-only: requirements, constraints, open questions
  - decisions-only: decisions, action items, deferred items

Custom templates can be loaded from JSON files.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Built-in templates embedded for zero-config usage.
# These mirror the JSON files in templates/extraction-templates/.
BUILT_IN_TEMPLATES: dict[str, dict] = {
    "default": {
        "name": "default",
        "description": "Full extraction — all categories.",
        "sections": [
            "participants",
            "decisions",
            "actionItems",
            "requirements",
            "technicalConstraints",
            "openQuestions",
            "risks",
            "deferredItems",
        ],
        "guidelines": "Extract EVERYTHING across all categories. Be exhaustive.",
    },
    "requirements-only": {
        "name": "requirements-only",
        "description": "Requirements-focused extraction.",
        "sections": ["requirements", "technicalConstraints", "openQuestions"],
        "guidelines": (
            "Focus exclusively on requirements, technical constraints, and open questions. "
            "Categorize requirements by type and priority. Include supporting quotes."
        ),
    },
    "decisions-only": {
        "name": "decisions-only",
        "description": "Decisions-focused extraction.",
        "sections": ["participants", "decisions", "actionItems", "deferredItems"],
        "guidelines": (
            "Focus on decisions and their outcomes. Track who decided what, "
            "confidence levels, and any deferred items. Include supporting quotes."
        ),
    },
}

# Full schema definition for all possible sections.
SECTION_SCHEMAS: dict[str, dict | list] = {
    "participants": [
        {
            "name": "Full Name",
            "role": "PM|Engineer|Designer|Stakeholder|Executive|Unknown",
            "aliases": [],
            "inferredFromContext": False,
        }
    ],
    "decisions": [
        {
            "what": "description",
            "decidedBy": [],
            "confidence": "high|medium|low",
            "supportingQuotes": [],
            "context": "",
            "revisits": False,
        }
    ],
    "actionItems": [
        {
            "action": "description",
            "owner": "Name or Unassigned",
            "deadline": None,
            "status": "open|in-progress|done",
            "supportingQuote": "",
        }
    ],
    "requirements": [
        {
            "description": "",
            "type": "functional|non-functional|constraint",
            "priority": "critical|high|medium|low",
            "mentionedBy": [],
            "supportingQuotes": [],
            "category": "auth|data|api|ui|infrastructure|security|performance|other",
        }
    ],
    "technicalConstraints": [
        {
            "constraint": "",
            "explicit": True,
            "source": "",
            "supportingQuote": "",
        }
    ],
    "openQuestions": [
        {
            "question": "",
            "raisedBy": "",
            "context": "",
            "suggestedAnswers": [],
        }
    ],
    "risks": [
        {
            "risk": "",
            "flaggedBy": "",
            "severity": "critical|high|medium|low",
            "mitigation": None,
        }
    ],
    "deferredItems": [
        {
            "item": "",
            "deferredTo": "",
            "reason": "",
            "supportingQuote": "",
        }
    ],
}


def list_templates() -> list[dict]:
    """Return metadata for all available templates."""
    return [
        {"name": t["name"], "description": t["description"], "sections": t["sections"]}
        for t in BUILT_IN_TEMPLATES.values()
    ]


def get_template(name: str) -> dict:
    """Get a template by name. Raises ValueError if not found."""
    template = BUILT_IN_TEMPLATES.get(name)
    if template is None:
        available = ", ".join(BUILT_IN_TEMPLATES.keys())
        raise ValueError(f"Unknown template '{name}'. Available: {available}")
    return template


def load_template_from_file(path: str) -> dict:
    """Load a custom template from a JSON file and register it."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")

    with open(file_path) as f:
        template = json.load(f)

    # Validate required fields
    for field in ("name", "sections"):
        if field not in template:
            raise ValueError(f"Template missing required field: {field}")

    # Validate sections are known
    unknown = set(template["sections"]) - set(SECTION_SCHEMAS.keys())
    if unknown:
        raise ValueError(f"Unknown sections in template: {unknown}")

    BUILT_IN_TEMPLATES[template["name"]] = template
    logger.info("Loaded custom template '%s' from %s", template["name"], path)
    return template


def build_schema_for_template(template_name: str) -> str:
    """Build a JSON schema string containing only the sections in the template."""
    template = get_template(template_name)
    sections = template["sections"]

    schema = {"source": {"name": "<filename>", "type": "<type>", "wordCount": "<count>"}}
    for section in sections:
        if section in SECTION_SCHEMAS:
            schema[section] = SECTION_SCHEMAS[section]

    return json.dumps(schema, indent=2)


def get_template_guidelines(template_name: str) -> str:
    """Get extraction guidelines for a template."""
    template = get_template(template_name)
    return template.get("guidelines", "")
