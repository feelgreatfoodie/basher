# /clu-prd - Generate PRD from CLU Analysis

Transform an existing CLU analysis into a Basher-compatible PRD. Requires that `/clu` or `/clu-analyze` has already been run.

## Usage

```
/clu-prd                                    # Generate PRD from ./clu/analysis.json
/clu-prd --conflict-mode strongest-consensus  # Auto-resolve conflicts by consensus strength
/clu-prd --conflict-mode open-questions       # Add conflicts as open questions (default)
/clu-prd --conflict-mode ask-user             # Ask user to resolve each conflict
```

## Prerequisites

- `./clu/analysis.json` must exist (run `/clu-analyze` or `/clu` first)
- `./clu/requirements.md` and `./clu/conflicts.md` should exist for reference

## What It Does

Reads the structured analysis from CLU and generates a Basher-compatible PRD at `./basher/prd.md`.

## Process

### Step 1: Load Analysis

Read `./clu/analysis.json` and validate it contains:
- Requirements (at least 1)
- Decisions
- Stakeholders
- Conflicts (may be 0)

If `analysis.json` doesn't exist or is empty:
```
Error: No CLU analysis found at ./clu/analysis.json

Run /clu-analyze first to extract and synthesize your transcripts.
```

### Step 2: Map Requirements to User Stories

Transform consolidated requirements into Basher user stories:

| Source Priority | Basher Priority | Criteria |
|-----------------|-----------------|----------|
| Consensus (3+ sources) | Priority 1 (Critical) | Broad agreement, foundational |
| High (2 sources) | Priority 2 (High) | Multiple stakeholders, important |
| Standard (1 source, critical) | Priority 2 (High) | Single source but critical need |
| Standard (1 source) | Priority 3 (Medium) | Standard requirements |
| Low / deferred | Priority 4 (Low) | Nice-to-have, explicitly deferred |

For each requirement, generate a user story:

```markdown
### US-001: [Requirement description as title]

**Priority:** [1-4]

As a [inferred user type from stakeholder context],
I want to [requirement description]
so that [inferred benefit from context/quotes].

**Acceptance Criteria:**
- [ ] [Derived from requirement details]
- [ ] [Derived from technical constraints]
- [ ] [Derived from supporting quotes]

**Technical Notes:**
- [Relevant technical constraints]
- [Relevant decisions]
- Source: [transcript names where this was discussed]

**Consensus:** Mentioned in [N] transcripts by [stakeholder names]
```

### Step 3: Handle Conflicts

Based on `--conflict-mode`:

**`open-questions` (default):**
Add unresolved conflicts to the PRD's "Open Questions" section:
```markdown
## Open Questions

### OQ-1: [Conflict topic]
Position A ([N] sources): "[summary]" -- [names]
Position B ([N] sources): "[summary]" -- [names]
Impact: [What depends on this decision]
```

**`strongest-consensus`:**
Auto-resolve by picking the position with more sources/higher authority stakeholders. Note the resolution:
```markdown
**Technical Notes:**
- Resolved via consensus: [chosen position] ([N] sources vs [N])
- Dissenting view: [summary of other position] -- [names]
```

**`ask-user`:**
For each conflict, prompt the user:
```
CONFLICT 1 of [N]: [Topic]
Position A ([N] sources): "[summary]" -- [names]
Position B ([N] sources): "[summary]" -- [names]
Suggested: Position [A/B] (stronger consensus)

[a] Accept A  [b] Accept B  [c] Custom  [d] Defer to Open Questions
>
```

### Step 4: Add Context Sections

Add to the PRD from analysis data:

**Technical Considerations:**
- All technical constraints from extractions
- Architecture decisions from decision log

**Dependencies:**
- Infer story dependencies from requirement relationships
- Data layer stories before API stories before UI stories

**Open Questions:**
- Gaps from `gaps.md`
- Unresolved conflicts (if using open-questions mode)

### Step 5: Calculate Estimates

Estimate story sizes based on:
- Number of acceptance criteria
- Technical complexity signals
- Dependency count

Target: 2-8 hours per story (Basher's sweet spot).

Split stories that seem too large.

### Step 6: Write PRD

Save to `./basher/prd.md` in the exact format expected by `/basher-convert`:

```markdown
# [Project Name] - Product Requirements Document

## Overview
[Synthesized from analysis - what we're building and why]

## Problem Statement
[Derived from stakeholder concerns and requirements]

## Goals
- [From consensus requirements]

## Non-Goals (Out of Scope)
- [From deferred items]

## User Stories
[All generated stories, numbered US-001 through US-NNN]

## Technical Considerations
[From constraints and decisions]

## Success Metrics
[From requirements and stakeholder concerns]

## Open Questions
[From conflicts and gaps]

## Git Branch
**Branch Name:** `basher/[project-name]`
```

### Step 7: Summary

```
PRD Generated from CLU Analysis

Source: ./clu/analysis.json
Output: ./basher/prd.md

Summary:
- Total Stories: [N]
- Priority 1 (Critical): [N] stories
- Priority 2 (High): [N] stories
- Priority 3 (Medium): [N] stories
- Priority 4 (Low): [N] stories
- Open Questions: [N] (from [N] conflicts + [N] gaps)

Conflict handling: [mode used]

Next steps:
1. Review ./basher/prd.md
2. Resolve Open Questions if needed
3. Run /basher-convert to generate prd.json
4. Run basher.sh to start autonomous implementation
```

## Integration with Basher

The generated PRD follows Basher's exact format:
- Stories sized for single Claude sessions (2-8 hours)
- Clear acceptance criteria for automated verification
- Dependencies specified for ordering
- Technical notes for implementation guidance

After generation:
```bash
claude /basher-convert    # Generate prd.json
~/.basher/basher.sh       # Start autonomous build
```

## Traceability

Every user story in the PRD includes source references back to the original transcripts. This enables:
- Verifying requirements match stakeholder intent
- Tracing decisions to their origin
- Understanding why a story exists
