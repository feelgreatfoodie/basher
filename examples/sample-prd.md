# Task Manager API - Product Requirements Document

## Overview

A simple REST API for managing personal tasks, supporting full CRUD operations. This is the foundation for a larger productivity application to be built in future phases.

## Problem Statement

Users need a straightforward way to track their tasks and todos. Current solutions are either too complex for simple use cases or don't provide the API access needed for custom integrations and automations.

## Goals

- Provide a clean, intuitive REST API for task management
- Support full CRUD operations (Create, Read, Update, Delete)
- Ensure proper data validation and meaningful error messages
- Maintain fast response times (<100ms for simple operations)
- Create a foundation for future features

## Non-Goals (Out of Scope)

- User authentication and authorization (Phase 2)
- Multiple task lists or projects (Phase 2)
- Task categories or tags (Phase 2)
- Due dates and reminders (Phase 2)
- Collaboration and sharing features (Phase 3)
- Mobile applications (Phase 3)

## User Stories

### US-001: Initialize Express Project with TypeScript
**Priority:** 1 (Critical)

As a developer, I want a properly configured Express project with TypeScript so that I can build type-safe API endpoints.

**Acceptance Criteria:**
- Project has package.json with Express, TypeScript, and necessary dependencies
- TypeScript is configured with strict mode enabled
- ESLint is configured for TypeScript
- Basic Express app starts successfully on port 3000
- npm scripts for dev, build, and start are configured

**Technical Notes:**
- Use Express 4.x
- Use TypeScript 5.x
- Include ts-node-dev for development
- Use ES modules (type: "module" in package.json)

---

### US-002: Create Task Data Model
**Priority:** 1 (Critical)

As a developer, I want a Task data model so that I can store and validate task data consistently.

**Acceptance Criteria:**
- Task type/interface is defined with proper TypeScript types
- Task has: id (string/UUID), title (string), description (string | null), status (enum), createdAt (Date), updatedAt (Date)
- Status is an enum with values: 'todo', 'in-progress', 'done'
- Title is required and has a maximum length of 200 characters
- Description is optional and has a maximum length of 1000 characters
- Validation functions are provided for task creation and updates

**Technical Notes:**
- Use Zod or similar for runtime validation
- Export types for use in other modules

---

### US-003: Implement In-Memory Task Storage
**Priority:** 1 (Critical)

As a developer, I want an in-memory storage layer so that I can persist tasks during runtime without database complexity.

**Acceptance Criteria:**
- TaskStore class/module manages task storage
- Supports: create, findAll, findById, update, delete operations
- Generates UUIDs for new tasks
- Returns appropriate errors for not-found cases
- Data persists for the lifetime of the application process

**Technical Notes:**
- Use a Map or array for storage
- This will be replaced with a database in Phase 2

---

### US-004: Add Create Task Endpoint
**Priority:** 2 (High)

As a user, I want to create tasks via the API so that I can track my work items.

**Acceptance Criteria:**
- POST /api/tasks creates a new task
- Request body accepts: title (required), description (optional), status (optional, defaults to 'todo')
- Returns 201 status with the created task (including generated id and timestamps)
- Returns 400 status with validation errors if request is invalid
- Response includes Content-Type: application/json header

**Technical Notes:**
- Use express.json() middleware for body parsing
- Validate request body before processing

---

### US-005: Add List Tasks Endpoint
**Priority:** 2 (High)

As a user, I want to retrieve all my tasks so that I can see what I need to do.

**Acceptance Criteria:**
- GET /api/tasks returns all tasks
- Response is a JSON array of task objects
- Tasks are sorted by createdAt in descending order (newest first)
- Response includes total count in a wrapper object or header
- Returns 200 status with empty array if no tasks exist

---

### US-006: Add Get Single Task Endpoint
**Priority:** 2 (High)

As a user, I want to retrieve a specific task by ID so that I can view its details.

**Acceptance Criteria:**
- GET /api/tasks/:id returns a single task
- Returns 200 status with the task object if found
- Returns 404 status with error message if task not found
- ID parameter is validated as a valid UUID format

---

### US-007: Add Update Task Endpoint
**Priority:** 2 (High)

As a user, I want to update my tasks so that I can change their title, description, or status.

**Acceptance Criteria:**
- PUT /api/tasks/:id updates an existing task
- Request body can include: title, description, status (all optional)
- Returns 200 status with the updated task
- Returns 404 status if task not found
- Returns 400 status if validation fails
- updatedAt timestamp is automatically updated

**Technical Notes:**
- Use partial validation (all fields optional)
- Only update fields that are provided

---

### US-008: Add Delete Task Endpoint
**Priority:** 3 (Medium)

As a user, I want to delete tasks so that I can remove completed or irrelevant items.

**Acceptance Criteria:**
- DELETE /api/tasks/:id removes a task
- Returns 204 status (no content) on successful deletion
- Returns 404 status if task not found
- Deletion is permanent (no soft delete for now)

---

### US-009: Add Global Error Handler
**Priority:** 3 (Medium)

As a developer, I want consistent error handling so that API consumers get predictable error responses.

**Acceptance Criteria:**
- Global error handler middleware catches all unhandled errors
- Error responses have consistent format: { error: string, details?: any }
- Validation errors return 400 status
- Not found errors return 404 status
- Unexpected errors return 500 status with generic message
- Errors are logged to console with stack traces in development

---

### US-010: Add API Tests
**Priority:** 3 (Medium)

As a developer, I want comprehensive tests so that I can verify the API works correctly and prevent regressions.

**Acceptance Criteria:**
- Test framework is configured (Jest or Vitest)
- Tests cover all CRUD endpoints
- Tests verify success cases (200, 201, 204)
- Tests verify error cases (400, 404)
- Tests verify validation rules
- All tests pass
- Tests can run via npm test

**Technical Notes:**
- Use supertest for HTTP assertions
- Test each endpoint in isolation

---

## Technical Considerations

### Architecture

```
src/
├── index.ts          # App entry point
├── app.ts            # Express app configuration
├── routes/
│   └── tasks.ts      # Task routes
├── models/
│   └── task.ts       # Task type definitions
├── store/
│   └── taskStore.ts  # In-memory storage
├── middleware/
│   └── errorHandler.ts
└── validation/
    └── taskValidation.ts
```

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/tasks | Create a task |
| GET | /api/tasks | List all tasks |
| GET | /api/tasks/:id | Get single task |
| PUT | /api/tasks/:id | Update task |
| DELETE | /api/tasks/:id | Delete task |

### Response Formats

**Success (single task):**
```json
{
  "id": "uuid",
  "title": "Task title",
  "description": "Task description",
  "status": "todo",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Success (list):**
```json
{
  "tasks": [...],
  "total": 10
}
```

**Error:**
```json
{
  "error": "Validation failed",
  "details": {
    "title": "Title is required"
  }
}
```

## Success Metrics

- All API endpoints return correct responses
- All tests pass
- Response times under 100ms for all operations
- Zero runtime TypeScript errors

## Open Questions

None for Phase 1.

## Git Branch

**Branch Name:** `basher/task-manager-api`
