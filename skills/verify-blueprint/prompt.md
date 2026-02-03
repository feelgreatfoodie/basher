# /verify-blueprint Skill

Verify completeness and quality of a blueprint extraction.

## Trigger

```
/verify-blueprint [blueprint-path]
```

**Examples:**
- `/verify-blueprint ./saas-blueprint`
- `/verify-blueprint .` (current directory)
- `/verify-blueprint ~/projects/my-blueprint`

## Purpose

Runs comprehensive checks on a blueprint to ensure:
1. All required files exist
2. Content meets minimum quality standards
3. Internal links resolve correctly
4. Code templates are syntactically valid
5. PRD fragments are Basher-compatible

## Output

Generates a verification report with:
- Overall pass/fail status
- Per-domain completeness scores
- Specific issues found
- Recommendations for fixes

## Verification Checks

### 1. Structure Verification

Check that the blueprint has the required structure:

```
blueprint/
├── manifest.json           # Required
├── README.md               # Required
├── domains/                # Required
│   └── [domain]/
│       ├── README.md       # Required per domain
│       ├── patterns.md     # Required per domain
│       ├── deep-dive.md    # Required per domain
│       ├── questions.md    # Required per domain
│       ├── prd-fragment.md # Required per domain
│       └── templates/      # Required per domain (≥1 file)
├── architecture/           # Optional
├── security/               # Optional
├── process/                # Optional
└── basher/                  # Optional
```

### 2. File Size Verification

Minimum content thresholds:

| File | Minimum Size | Rationale |
|------|-------------|-----------|
| README.md | 500 chars | Must have overview + links |
| patterns.md | 5,000 chars | Must document ≥3 patterns |
| deep-dive.md | 3,000 chars | Must explain WHY |
| questions.md | 1,500 chars | Must have ≥15 questions |
| prd-fragment.md | 1,000 chars | Must have ≥3 user stories |

### 3. Content Quality Checks

#### README.md
- [ ] Has domain overview
- [ ] Has quick links section
- [ ] Has key concepts
- [ ] Has related domains
- [ ] Links resolve to existing files

#### patterns.md
- [ ] Documents at least 3 patterns
- [ ] Each pattern has: Problem, Solution, Why, Usage
- [ ] Code examples are complete (not snippets)
- [ ] Code examples have syntax highlighting

#### deep-dive.md
- [ ] Explains WHY, not just HOW
- [ ] Covers security considerations
- [ ] Documents common mistakes
- [ ] Educational tone (teaches concepts)

#### questions.md
- [ ] Organized by category
- [ ] Questions are actionable (lead to decisions)
- [ ] Covers requirements, architecture, security
- [ ] At least 15 questions

#### prd-fragment.md
- [ ] User stories follow format (As a... I want... So that...)
- [ ] Each story has acceptance criteria
- [ ] Stories have effort estimates
- [ ] Stories are sized for single sessions (2-8 hours)
- [ ] Total domain estimate is realistic

#### templates/
- [ ] At least 1 template file exists
- [ ] Templates are syntactically valid
- [ ] Templates have JSDoc comments
- [ ] Templates follow TypeScript best practices

### 4. Cross-Reference Verification

Check that:
- Internal links (relative paths) resolve
- Domain references exist
- Template imports are valid
- No broken links in markdown

### 5. PRD Compatibility

Verify prd-fragment.md works with Basher:
- Story IDs follow pattern (US-DOMAIN-NNN)
- Acceptance criteria are checkable
- Technical notes provide implementation hints
- Estimates use range format (X-Y hours)

## Process

### Step 1: Discover Domains

Find all domains in the blueprint:
```bash
ls domains/
```

### Step 2: Per-Domain Verification

For each domain, check:
```
Domain: auth
├── ✅ README.md (823 bytes) - passes minimum
├── ✅ patterns.md (12,456 bytes) - passes minimum
├── ⚠️ deep-dive.md (2,100 bytes) - BELOW MINIMUM (3,000)
├── ✅ questions.md (3,456 bytes) - passes minimum
├── ✅ prd-fragment.md (4,567 bytes) - passes minimum
└── ✅ templates/ (3 files)
    ├── auth-provider.tsx (2,345 bytes)
    ├── middleware.ts (1,234 bytes)
    └── rbac-hook.ts (987 bytes)

Issues:
1. deep-dive.md is 900 bytes below minimum
2. questions.md missing security category
```

### Step 3: Syntax Validation

For each template file:
```typescript
// Attempt to parse with TypeScript compiler
// Report any syntax errors
```

### Step 4: Link Verification

```
Checking links in domains/auth/README.md...
✅ ./patterns.md exists
✅ ./deep-dive.md exists
❌ ./security.md NOT FOUND
✅ ../database/README.md exists
```

### Step 5: Generate Report

## Report Format

```
═══════════════════════════════════════════════════════
BLUEPRINT VERIFICATION REPORT
═══════════════════════════════════════════════════════
Blueprint: ./saas-blueprint
Verified: 2026-01-23T15:30:00Z

OVERALL STATUS: ⚠️ WARNINGS (85% complete)

───────────────────────────────────────────────────────
DOMAIN SUMMARY
───────────────────────────────────────────────────────
Domain          Files   Templates   Issues   Status
auth            6/6     3           0        ✅ PASS
database        6/6     5           0        ✅ PASS
api             4/6     0           2        ❌ FAIL
ui              4/6     0           2        ❌ FAIL
realtime        6/6     2           0        ✅ PASS
notifications   6/6     3           1        ⚠️ WARN
compliance      6/6     2           0        ✅ PASS
testing         6/6     4           0        ✅ PASS

───────────────────────────────────────────────────────
ISSUES FOUND
───────────────────────────────────────────────────────

CRITICAL (must fix):
1. [api] Missing: deep-dive.md
2. [api] Missing: questions.md
3. [api] Missing: prd-fragment.md
4. [api] Missing: templates/ directory
5. [ui] Missing: deep-dive.md
6. [ui] Missing: questions.md
7. [ui] Missing: prd-fragment.md
8. [ui] Missing: templates/ directory

WARNINGS (should fix):
1. [notifications] deep-dive.md below minimum (2,800/3,000 chars)
2. [realtime] Broken link in README.md: ./websocket-patterns.md

INFO (optional):
1. [auth] patterns.md has TODO comment on line 234
2. [database] security-rules.txt could use more comments

───────────────────────────────────────────────────────
STATISTICS
───────────────────────────────────────────────────────
Total Domains:      8
Complete Domains:   6 (75%)
Files Generated:    44/48 (92%)
Templates:          19 files
Total Content:      156,789 bytes

PRD Fragment Summary:
- Total User Stories: 62
- Total Estimate: 145-210 hours
- Average Story Size: 2.5-3.4 hours ✅

───────────────────────────────────────────────────────
RECOMMENDATIONS
───────────────────────────────────────────────────────
1. Run /extract-domain api ./source to complete api domain
2. Run /extract-domain ui ./source to complete ui domain
3. Expand notifications/deep-dive.md (+200 chars needed)
4. Fix broken link in realtime/README.md

───────────────────────────────────────────────────────
NEXT STEPS
───────────────────────────────────────────────────────
After fixing critical issues, run:
  /verify-blueprint ./saas-blueprint

When all checks pass:
  /compose-prd auth database api ui realtime
═══════════════════════════════════════════════════════
```

## Exit Codes

For scripting purposes:

| Code | Meaning |
|------|---------|
| 0 | All checks pass |
| 1 | Warnings present (non-critical) |
| 2 | Critical issues found |
| 3 | Blueprint structure invalid |

## Integration

### With CI/CD

```yaml
# .github/workflows/verify.yml
- name: Verify Blueprint
  run: claude /verify-blueprint ./saas-blueprint
```

### With Pre-commit

```bash
# Before committing changes to blueprint
/verify-blueprint . || echo "Fix issues before committing"
```

### With Extract Domain

After extracting a new domain:
```
/extract-domain payments ./source
/verify-blueprint .  # Verify the extraction
```

## Customization

### Strict Mode

```
/verify-blueprint --strict ./saas-blueprint
```

Strict mode:
- Warnings become errors
- Requires all optional directories
- Enforces higher minimum content sizes

### Single Domain

```
/verify-blueprint --domain auth ./saas-blueprint
```

Verify only one domain (faster for iterative work).

### Output Format

```
/verify-blueprint --format json ./saas-blueprint
```

Output as JSON for programmatic consumption.

## Error Recovery

### Common Issues and Fixes

1. **Missing Files**
   - Run `/extract-domain [domain] ./source`
   - Or create manually using templates

2. **Content Too Short**
   - Review domain source code for more patterns
   - Expand explanations in deep-dive.md
   - Add more questions to questions.md

3. **Broken Links**
   - Update links to correct paths
   - Remove references to non-existent files
   - Create missing referenced files

4. **Invalid Syntax**
   - Check template files for TypeScript errors
   - Ensure proper imports
   - Validate JSX syntax

## Notes

- Run verification after any significant changes
- Address critical issues before using with Basher
- Warnings indicate areas for improvement
- Use `--strict` before publishing blueprint
