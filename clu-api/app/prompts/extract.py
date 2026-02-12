"""Extraction prompt builder — mirrors prompts/clu-subagent-extract.md logic."""

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
) -> str:
    """Build the user prompt for per-transcript extraction."""
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
