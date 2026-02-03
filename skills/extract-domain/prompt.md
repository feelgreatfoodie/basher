# /extract-domain Skill

Extract a domain from any codebase into the standardized blueprint format.

## Trigger

```
/extract-domain [domain-name] [source-path]
```

**Examples:**
- `/extract-domain auth ./my-project`
- `/extract-domain payments ./saas-app`
- `/extract-domain notifications .`

## Purpose

Extracts implementation patterns, code templates, and knowledge from an existing codebase into the standardized 6-file domain structure used in the saas-blueprint.

## Output Structure

For each domain extraction, generate:

```
domains/[domain-name]/
├── README.md           # Domain overview with quick links
├── patterns.md         # Implementation patterns with annotated code
├── deep-dive.md        # Educational: WHY these patterns work
├── questions.md        # 15-25 planning questions
├── prd-fragment.md     # Basher-compatible user stories
└── templates/          # Reusable code snippets
    └── [template-files]
```

## Process

### Step 1: Codebase Analysis

Search the source codebase for files related to the domain:

```
For "auth" domain, search for:
- Files: auth*, login*, register*, session*, middleware*, rbac*, permission*
- Directories: /auth, /lib/auth, /services/auth, /hooks/useAuth*
- Imports: firebase-auth, next-auth, clerk, auth0, jwt
- Patterns: custom claims, role checks, protected routes
```

### Step 2: Pattern Extraction

For each significant pattern found:

1. **Identify the Pattern**
   - What problem does it solve?
   - What alternatives were considered?
   - Why was this approach chosen?

2. **Extract Code Examples**
   - Full working code with comments
   - Include imports and dependencies
   - Note any configuration required

3. **Document Trade-offs**
   - Pros and cons
   - When to use vs. alternatives
   - Performance considerations

### Step 3: Generate Standard Files

#### README.md Template
```markdown
# [Domain] Domain

## Overview
[2-3 sentences describing what this domain covers]

## Quick Links
- [Patterns](./patterns.md) - Implementation patterns
- [Deep Dive](./deep-dive.md) - Why these patterns work
- [Questions](./questions.md) - Planning checklist
- [PRD Fragment](./prd-fragment.md) - User stories for Basher

## Key Concepts
- **[Concept 1]**: [Brief explanation]
- **[Concept 2]**: [Brief explanation]

## Related Domains
- [Related Domain 1] - [How it relates]
- [Related Domain 2] - [How it relates]

## Templates
- `templates/[file].ts` - [Description]
```

#### patterns.md Template
```markdown
# [Domain] Patterns

## Pattern 1: [Pattern Name]

### Problem
[What problem does this solve?]

### Solution
[Code block with full implementation]

### Why This Works
[Explanation of the design decisions]

### Usage
[Example of how to use this pattern]

### Variations
[Alternative implementations or configurations]
```

#### deep-dive.md Template
```markdown
# [Domain] Deep Dive

## Understanding [Domain]

[Educational explanation of the domain concepts]

## Why [Pattern]?

[Explain the reasoning behind key architectural decisions]

## Common Mistakes

[What to avoid and why]

## Security Considerations

[Security implications specific to this domain]
```

#### questions.md Template
```markdown
# [Domain] Planning Questions

## Requirements Discovery
1. [Question about requirements]
2. [Question about requirements]

## Architecture Decisions
1. [Question about architecture]
2. [Question about architecture]

## Integration
1. [Question about integration]
2. [Question about integration]

## Security
1. [Question about security]
2. [Question about security]
```

#### prd-fragment.md Template
```markdown
# [Domain] PRD Fragment

## User Stories

### US-[DOMAIN]-001: [Title]
**As a** [user type]
**I want to** [capability]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Technical Notes:**
- [Implementation hint]

**Estimated Effort:** [X-Y hours]

---
[More user stories...]

## Total Estimate
- **Minimum:** X hours
- **Maximum:** Y hours
```

### Step 4: Verification Gate

After generating all files, verify completeness:

```
□ README.md exists and has >500 characters
□ patterns.md exists and has >5000 characters
□ deep-dive.md exists and has >3000 characters
□ questions.md exists and has >1500 characters
□ prd-fragment.md exists and has user stories
□ templates/ has at least 1 .ts/.tsx file
□ All internal links resolve
□ Code examples are syntactically valid
```

### Step 5: Report

Output a summary:

```
Domain Extraction Complete: [domain-name]

Files Generated:
✅ README.md (823 bytes)
✅ patterns.md (12,456 bytes)
✅ deep-dive.md (8,234 bytes)
✅ questions.md (3,456 bytes)
✅ prd-fragment.md (4,567 bytes)
✅ templates/
   - [file1].ts (2,345 bytes)
   - [file2].ts (1,234 bytes)

User Stories: 8
Estimated Hours: 18-28

Patterns Documented:
1. [Pattern 1]
2. [Pattern 2]
3. [Pattern 3]

Source Files Analyzed:
- /path/to/file1.ts
- /path/to/file2.tsx
```

## Quality Guidelines

### Pattern Documentation
- Include full, working code - not snippets
- Add line-by-line comments for complex logic
- Show both happy path and error handling
- Include TypeScript types

### Questions
- Focus on decisions that impact architecture
- Include questions about scale and performance
- Cover security implications
- Ask about integration points

### User Stories
- Size for single Claude Code sessions (2-8 hours)
- Include clear acceptance criteria
- Add technical implementation hints
- Provide realistic hour estimates

### Templates
- Production-ready code quality
- Follow the source project's conventions
- Include error handling
- Add JSDoc comments

## Domain Categories

Common domains to extract:

| Domain | Focus Areas |
|--------|-------------|
| auth | Authentication, authorization, sessions, RBAC |
| database | Schema, queries, migrations, security rules |
| api | Routes, middleware, validation, error handling |
| ui | Components, forms, state, styling |
| realtime | WebSockets, subscriptions, optimistic updates |
| notifications | In-app, email, push, templates |
| compliance | GDPR, audit, data export/deletion |
| testing | Unit, integration, E2E, fixtures |
| payments | Stripe, subscriptions, invoicing |
| search | Full-text, filters, facets, pagination |
| files | Upload, storage, processing, CDN |
| analytics | Events, tracking, dashboards |

## Error Handling

If extraction encounters issues:

1. **Insufficient Source Code**
   - Report which patterns couldn't be extracted
   - Suggest alternative approaches
   - Generate skeleton files with TODOs

2. **Ambiguous Patterns**
   - Document multiple approaches found
   - Ask for clarification on preferred approach
   - Include trade-off analysis

3. **Missing Dependencies**
   - List required packages not found
   - Note configuration that may be missing
   - Provide setup instructions

## Notes

- Always respect the source project's patterns and conventions
- Prefer extracting actual code over generating generic examples
- Include source file paths in documentation for reference
- Note any assumptions made during extraction
