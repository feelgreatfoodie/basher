"""Synthesis prompt builder — mirrors prompts/clu-orchestrator.md Phase 3 logic."""

SYNTHESIS_SYSTEM_PROMPT = """You are the CLU synthesis engine. You cross-reference extraction data from multiple transcripts to produce a unified analysis.

Your job:
1. Consensus ranking — requirements mentioned in 3+ transcripts get highest confidence
2. Conflict detection — different stakeholders saying contradictory things about same topic
3. Decision tracking — decisions confirmed in later meetings vs contradicted/revisited
4. Stakeholder deduplication — fuzzy matching across name variants
5. Gap analysis — concepts referenced but never defined"""

SYNTHESIS_OUTPUT_SCHEMA = """{
  "summary": {
    "totalTranscripts": 0,
    "totalParticipants": 0,
    "totalDecisions": 0,
    "totalRequirements": 0,
    "conflictsFound": 0,
    "gapsFound": 0,
    "highlights": []
  },
  "conflicts": [{ "topic": "", "positions": [{ "position": "", "supporters": [], "sources": [] }], "suggestedResolution": "" }],
  "gaps": [{ "concept": "", "referencedIn": [], "context": "" }],
  "decisions": [{ "what": "", "decidedBy": [], "confidence": "high|medium|low", "confirmedIn": [], "contradictedIn": [], "status": "confirmed|revisited|superseded" }],
  "requirements": [{ "description": "", "type": "", "priority": "", "consensus": 0, "mentionedIn": [], "mentionedBy": [] }],
  "stakeholders": [{ "name": "", "role": "", "aliases": [], "interests": [], "decisionAuthority": [] }],
  "actionItems": [{ "action": "", "owner": "", "deadline": null, "status": "", "sources": [] }]
}"""


def build_synthesis_prompt(
    extractions_json: str,
    semantic_conflicts: list[dict] | None = None,
) -> str:
    """Build the user prompt for cross-reference synthesis."""
    semantic_section = ""
    if semantic_conflicts:
        import json
        hints = json.dumps(semantic_conflicts[:20], indent=2)  # Cap at 20 hints
        semantic_section = f"""

**Semantic similarity hints (from vector search):**
The following entity pairs were flagged as semantically similar but from different sources.
Investigate each pair — they may represent conflicts, agreements, or related but distinct items.

{hints}
"""

    return f"""Cross-reference and synthesize the following extraction data from multiple transcripts.

**Instructions:**
1. Deduplicate stakeholders across transcripts (match by name variants/aliases)
2. Rank requirements by how many transcripts mention them (consensus score)
3. Detect conflicts: same topic with different positions from different people
4. Track decisions: mark as confirmed if repeated in later transcripts, revisited if contradicted
5. Identify gaps: concepts referenced but never fully defined
6. Consolidate action items, merge duplicates, track status across sources
{semantic_section}
**Output format:** Return ONLY valid JSON matching this schema:
{SYNTHESIS_OUTPUT_SCHEMA}

**Extraction data from all transcripts:**

{extractions_json}"""
