# PRD to JSON Conversion Skill

You are a PRD converter. Your task is to transform a Markdown PRD into the structured JSON format that Basher uses for autonomous execution.

## Input

Read the PRD from `./basher/prd.md`.

If the file doesn't exist, inform the user they need to create a PRD first:
```
No PRD found at ./basher/prd.md
Run /prd first to generate a PRD from your meeting notes or feature description.
```

## Output

Generate `./basher/prd.json` with the following structure:

```json
{
  "project": "project-name",
  "branchName": "basher/feature-name",
  "description": "Brief description of what this PRD implements",
  "gitStrategy": "single-branch",
  "userStories": [
    {
      "id": "US-001",
      "title": "Story title",
      "description": "As a [user], I want to [action] so that [benefit]",
      "acceptanceCriteria": [
        "Criterion 1",
        "Criterion 2",
        "Criterion 3"
      ],
      "technicalNotes": "Any implementation hints",
      "priority": 1,
      "passes": false,
      "notes": ""
    }
  ],
  "metadata": {
    "createdAt": "2024-01-15T10:30:00Z",
    "totalStories": 5,
    "completedStories": 0
  }
}
```

## Field Specifications

### Root Level

| Field | Type | Description |
|-------|------|-------------|
| `project` | string | Project name (kebab-case) |
| `branchName` | string | Git branch name from PRD |
| `description` | string | One-line summary |
| `gitStrategy` | string | `"single-branch"` or `"branch-per-story"` |
| `userStories` | array | Array of story objects |
| `metadata` | object | Tracking metadata |

### User Story Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (US-001, US-002, etc.) |
| `title` | string | Brief story title |
| `description` | string | Full user story description |
| `acceptanceCriteria` | string[] | List of acceptance criteria |
| `technicalNotes` | string | Implementation hints (optional) |
| `priority` | number | 1=Critical, 2=High, 3=Medium, 4=Low |
| `passes` | boolean | Completion status (always `false` initially) |
| `notes` | string | Notes added during implementation |

### Metadata Object

| Field | Type | Description |
|-------|------|-------------|
| `createdAt` | string | ISO 8601 timestamp |
| `totalStories` | number | Count of user stories |
| `completedStories` | number | Count where passes=true |

## Conversion Rules

1. **Story IDs** - Generate sequential IDs: US-001, US-002, etc.
2. **Priorities** - Map from PRD: Critical→1, High→2, Medium→3, Low→4
3. **All stories start with `passes: false`**
4. **Branch name** - Extract from PRD or generate from project name
5. **Git strategy** - Default to `"single-branch"` unless PRD specifies otherwise

## Validation

Before saving, validate:

- [ ] All stories have unique IDs
- [ ] All stories have at least one acceptance criterion
- [ ] Priorities are 1-4
- [ ] Branch name is valid git branch format
- [ ] No duplicate story titles

## Example Conversion

### Input (prd.md excerpt)
```markdown
## Git Branch
**Branch Name:** `basher/user-auth`

### US-001: Create Login Form
**Priority:** 1 (Critical)

As a user, I want to log in with email and password so that I can access my account.

**Acceptance Criteria:**
- [ ] Form has email and password fields
- [ ] Form validates email format
- [ ] Form shows error on invalid credentials

**Technical Notes:**
Use the existing Button and Input components from the design system.
```

### Output (prd.json excerpt)
```json
{
  "project": "user-auth",
  "branchName": "basher/user-auth",
  "description": "User authentication system",
  "gitStrategy": "single-branch",
  "userStories": [
    {
      "id": "US-001",
      "title": "Create Login Form",
      "description": "As a user, I want to log in with email and password so that I can access my account.",
      "acceptanceCriteria": [
        "Form has email and password fields",
        "Form validates email format",
        "Form shows error on invalid credentials"
      ],
      "technicalNotes": "Use the existing Button and Input components from the design system.",
      "priority": 1,
      "passes": false,
      "notes": ""
    }
  ],
  "metadata": {
    "createdAt": "2024-01-15T10:30:00Z",
    "totalStories": 1,
    "completedStories": 0
  }
}
```

## After Conversion

After generating the JSON:

1. Save to `./basher/prd.json`
2. Display a summary:

```
PRD converted to JSON: ./basher/prd.json

Project: user-auth
Branch: basher/user-auth
Stories: 5 total (0 completed)

Story Summary:
  [P1] US-001: Create Login Form
  [P1] US-002: Create Registration Form
  [P2] US-003: Add Password Reset
  [P3] US-004: Add Remember Me
  [P4] US-005: Add OAuth Support

Ready for autonomous execution!
Run: ~/.basher/basher.sh
```

3. Also initialize the progress file if it doesn't exist:

Create `./basher/progress.txt`:
```markdown
# Progress Log - [project-name]

Started: [timestamp]
Branch: [branch-name]

## Codebase Patterns
<!-- Patterns discovered during implementation will be added here -->

## Iteration Log
<!-- Each Basher iteration will append its progress here -->
```

## Error Handling

If the PRD is malformed or missing required information:

1. List the specific issues found
2. Suggest how to fix them
3. Do not generate invalid JSON

Example:
```
Cannot convert PRD - issues found:

1. Missing branch name - add "## Git Branch" section
2. US-003 has no acceptance criteria
3. US-005 has no priority specified

Please fix these issues in ./basher/prd.md and run /basher-convert again.
```
