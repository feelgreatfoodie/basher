# Writing Good PRDs for Basher

The quality of Basher's output depends heavily on the quality of your Product Requirements Document. This guide will help you write PRDs that lead to successful autonomous implementation.

---

## The Golden Rule: Small Tasks

**The most important principle:** Every user story must be completable in a single Claude session.

Claude has a "context window" — a limit on how much it can think about at once. If a task is too big, Claude will run out of context before finishing, leading to incomplete or broken code.

### Good Task Size

These tasks can typically complete in one session:

- "Create a User model with email and password fields"
- "Add POST /login endpoint with validation"
- "Create LoginForm component with email and password inputs"
- "Add unit tests for the authentication service"
- "Configure ESLint for the project"

### Bad Task Size

These tasks are too big:

- "Build the authentication system"
- "Create the entire frontend"
- "Implement the API"
- "Add all the tests"

### How to Split Large Features

Break features along natural boundaries:

**Data Layer:**
- Create database schema
- Add data models
- Write database migrations

**API Layer:**
- Add endpoint for creating resources
- Add endpoint for reading resources
- Add endpoint for updating resources
- Add endpoint for deleting resources
- Add input validation
- Add error handling

**UI Layer:**
- Create form component
- Create list component
- Create detail view component
- Add loading states
- Add error states

**Integration:**
- Connect frontend to API
- Add state management
- Add routing

---

## Writing Clear User Stories

### The Format

```
As a [type of user],
I want to [do something],
So that [benefit/reason].
```

### Good Examples

```
As a user,
I want to log in with my email and password,
So that I can access my account.
```

```
As an administrator,
I want to see a list of all users,
So that I can manage user accounts.
```

### Bad Examples

```
As a user, I want the app to work.
(Too vague — what does "work" mean?)
```

```
Implement login functionality.
(Not a user story — doesn't explain who or why)
```

---

## Writing Good Acceptance Criteria

Acceptance criteria define "done." They should be:

- **Specific** — No ambiguity
- **Testable** — Can verify pass/fail
- **Complete** — Cover all requirements
- **Minimal** — 2-5 criteria per story

### Good Criteria

```
Acceptance Criteria:
- Form has email field with email validation
- Form has password field (minimum 8 characters)
- Submit button is disabled until form is valid
- Successful login redirects to dashboard
- Failed login shows error message
```

### Bad Criteria

```
Acceptance Criteria:
- Login should work
- Handle errors
- Look good
```

(Too vague — what does "work" mean? What errors? What's "good"?)

---

## Priority Guidelines

Assign priorities to ensure tasks execute in the right order.

| Priority | Meaning | Examples |
|----------|---------|----------|
| 1 (Critical) | Must complete first, blocks other work | Project setup, core models |
| 2 (High) | Important, should complete early | Main features, primary APIs |
| 3 (Medium) | Standard priority | Secondary features, nice-to-haves |
| 4 (Low) | Can defer, not essential | Polish, optimizations |

### Dependency Rules

- **Data models** before **API endpoints**
- **API endpoints** before **UI components**
- **Core features** before **enhancement features**
- **Happy paths** before **error handling** (sometimes)

### Example Priority Assignment

For a task manager:

1. **P1:** Initialize project structure
2. **P1:** Create Task model
3. **P2:** Add create task endpoint
4. **P2:** Add list tasks endpoint
5. **P2:** Add update task endpoint
6. **P3:** Add delete task endpoint
7. **P3:** Add filtering/sorting
8. **P4:** Add pagination

---

## Technical Notes

Add technical notes when Claude needs specific guidance:

### When to Add Notes

- Specific libraries to use (or avoid)
- Design patterns to follow
- File locations or naming conventions
- Integration requirements
- Performance constraints

### Good Technical Notes

```
Technical Notes:
- Use the existing AuthService from src/services/auth.ts
- Follow the repository pattern used in UserRepository
- Store sessions in Redis, not memory
- Maximum response time: 200ms
```

### What NOT to Put in Notes

- Implementation details (let Claude figure it out)
- Obvious things (like "write clean code")
- Contradictory instructions

---

## Converting Meeting Notes to PRDs

If you're working from meeting transcripts, here's how to extract a good PRD:

### 1. Identify Decisions

Look for statements like:
- "We should..."
- "Let's go with..."
- "We need..."
- "Must have..."

### 2. Identify Open Questions

Look for:
- Unresolved debates
- "We'll figure that out later"
- Questions without answers

Put these in the "Open Questions" section.

### 3. Identify Scope

Look for:
- "Phase 2"
- "Later"
- "Out of scope"
- "Not now"

Put these in "Non-Goals."

### 4. Extract Features

Convert casual language to user stories:

**Meeting note:** "Users need to be able to log in"

**User story:**
```
As a user,
I want to log in with email and password,
So that I can access my account.
```

---

## Example: Complete PRD

Here's a well-structured PRD:

```markdown
# Task Manager API - PRD

## Overview
A REST API for managing personal tasks, supporting CRUD operations.

## Goals
- Simple, clean API design
- Fast response times
- Proper error handling

## Non-Goals (Out of Scope)
- User authentication (Phase 2)
- Multiple task lists (Phase 2)
- Due dates and reminders (Phase 2)

## User Stories

### US-001: Initialize Express project
**Priority:** 1 (Critical)

As a developer,
I want a properly configured Express project,
So that I can build API endpoints.

**Acceptance Criteria:**
- package.json with necessary dependencies
- TypeScript configuration
- ESLint configuration
- Basic Express app that starts on port 3000

**Technical Notes:**
Use Express 4.x with TypeScript.

---

### US-002: Create Task model
**Priority:** 1 (Critical)

As a developer,
I want a Task data model,
So that I can store and validate task data.

**Acceptance Criteria:**
- Task has id (UUID), title, description, status, createdAt
- Status enum: todo, in-progress, done
- Title is required, max 200 characters
- Description is optional, max 1000 characters

---

### US-003: Add create task endpoint
**Priority:** 2 (High)

As a user,
I want to create tasks via API,
So that I can track my work.

**Acceptance Criteria:**
- POST /api/tasks creates a new task
- Returns 201 with created task
- Returns 400 if validation fails
- Auto-generates id and createdAt

**Technical Notes:**
Use the validation middleware pattern from existing code.

---

[Continue for remaining stories...]

## Git Branch
**Branch Name:** `basher/task-manager-api`
```

---

## Common Mistakes to Avoid

### 1. Vague Acceptance Criteria
❌ "It should work properly"
✅ "Returns 200 status with JSON body containing user data"

### 2. Missing Dependencies
❌ US-003 (API endpoint) at Priority 1, US-002 (data model) at Priority 2
✅ Data model at Priority 1, API endpoint at Priority 2

### 3. Too Many Stories
❌ 50 stories in one PRD
✅ 5-15 stories per feature; split large features into phases

### 4. No Technical Context
❌ "Add login" with no details about auth method
✅ "Add login with JWT tokens stored in httpOnly cookies"

### 5. Mixing Features
❌ One story that adds both API endpoint AND UI component
✅ Separate stories for API and UI

---

## Checklist Before Running Basher

Before converting your PRD to JSON, verify:

- [ ] All stories have clear acceptance criteria
- [ ] Stories are small enough (completable in one session)
- [ ] Priorities respect dependencies
- [ ] Technical notes clarify ambiguities
- [ ] Non-goals are documented
- [ ] Branch name is specified
- [ ] No duplicate or conflicting requirements
