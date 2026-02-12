# CLU User Guide

> **Codified Likeness Utility** — Turn 10 messy transcripts into one clear build plan.

CLU ingests multiple transcripts (meeting notes, interviews, Slack threads, spec documents — as `.txt`, `.md`, `.pdf`, or `.docx` files), extracts structured data from each, cross-references across all sources, and produces actionable reports. Optionally generates a Basher-compatible PRD for autonomous code generation.

**v1.0 Highlights:** PDF/DOCX ingestion, incremental analysis, interactive conflict resolution wizard, configurable extraction templates, full JSON API.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [The Pipeline](#the-pipeline)
3. [Input: Transcripts](#input-transcripts)
4. [Skills Reference](#skills-reference)
5. [Output Files](#output-files)
6. [Configuration](#configuration)
7. [Extraction Templates](#extraction-templates)
8. [Running CLU](#running-clu)
9. [Incremental Analysis](#incremental-analysis)
10. [Conflict Resolution Wizard](#conflict-resolution-wizard)
11. [Review Checkpoints](#review-checkpoints)
12. [End-to-End Example](#end-to-end-example)
13. [Troubleshooting](#troubleshooting)
14. [Technology Learning Module](#technology-learning-module)

---

## Quick Start

```bash
# 1. Initialize in your project (creates ./clu/ directories)
~/.basher/basher-init.sh

# 2. Add transcripts
cp meeting-notes.txt ./clu/transcripts/
cp design-review.txt ./clu/transcripts/

# 3. Run analysis
claude /clu

# 4. Review results
cat ./clu/SUMMARY.md
cat ./clu/conflicts.md
```

That's it. CLU handles the extraction, cross-referencing, and report generation.

---

## The Pipeline

```
Phase 1: Ingest          Phase 2: Extract           Phase 3: Synthesize        Phase 4: PRD (optional)
──────────────────       ──────────────────         ──────────────────         ──────────────────
Scan transcripts    ──►  Sonnet subagents      ──►  Opus orchestrator     ──►  analysis.json
Auto-detect types        (up to 3 parallel)          Cross-reference            → prd.md
Generate manifest        Extract 8 entity types      Consensus ranking          → prd.json
                         → extraction JSONs           Conflict detection
                                                      Gap analysis
                                                      → Reports + analysis.json
```

### Phase 1: Ingest & Discover

CLU scans `./clu/transcripts/` for supported files (`.txt`, `.md`, `.pdf`, `.docx`). PDF and DOCX files are automatically converted to text using PyMuPDF and python-docx respectively. For each file, it:
- Auto-detects the type (meeting, interview, slack, spec, other)
- Counts words to determine model selection
- Generates a `manifest.json` with metadata

### Phase 2: Extract (Parallel)

Each transcript is processed individually by a Sonnet subagent. Up to 3 subagents run concurrently. Files exceeding 50,000 words are assigned to Opus instead.

**Extracted entities:**
- Participants (name, role, aliases for cross-transcript dedup)
- Decisions (what, who decided, confidence level, supporting quotes)
- Action items (action, owner, deadline, status)
- Requirements (description, type, priority, who mentioned it)
- Technical constraints (explicit and implied)
- Open questions (unresolved discussions)
- Risks/concerns (flagged issues with severity)
- Deferred items (explicitly pushed to later phases)

Output: `./clu/extractions/{transcript-name}.json`

### Phase 3: Synthesize

The Opus orchestrator reads all extraction JSONs and performs cross-reference analysis:

- **Consensus ranking** — Requirements mentioned in 3+ transcripts get highest confidence
- **Conflict detection** — Different stakeholders saying contradictory things about the same topic
- **Decision tracking** — Decisions confirmed in later meetings vs. contradicted/revisited
- **Stakeholder deduplication** — Fuzzy matching across "Alice", "Alice (PM)", "A. Johnson"
- **Gap analysis** — Concepts referenced but never defined

### Phase 4: PRD Generation (Optional)

When enabled, takes `analysis.json` and generates a Basher-compatible `prd.md`:
- Consensus requirements become user stories (highest consensus = highest priority)
- Unresolved conflicts become "Open Questions"
- Technical constraints become "Technical Considerations"

---

## Input: Transcripts

### Supported Formats

- `.txt` files — Plain text transcripts
- `.md` files — Markdown-formatted notes
- `.pdf` files — PDF documents (text extracted via PyMuPDF)
- `.docx` files — Word documents (text extracted via python-docx)

### Transcript Types (Auto-Detected)

| Type | Detection Heuristics | Examples |
|------|---------------------|----------|
| `meeting` | Participant names with colons, dialogue patterns | Meeting minutes, standup notes |
| `interview` | Q&A patterns, interviewer/interviewee roles | User interviews, research sessions |
| `slack` | Timestamp patterns, thread markers | Slack exports, chat logs |
| `spec` | Technical terminology density, section headers | Design docs, architecture reviews |
| `other` | Default fallback | Bullet points, free-form notes |

### Best Practices for Transcripts

1. **Include speaker names** — "Alice: We need REST" is more useful than "We need REST"
2. **Keep context** — Don't strip metadata like dates, participant lists, or agenda
3. **Separate clearly** — One file per meeting/conversation/document
4. **Name descriptively** — `kickoff-meeting-jan15.txt` beats `notes.txt`

### Directory Structure

```
./clu/transcripts/
├── kickoff-meeting.txt          # Initial project discussion
├── architecture-review.txt      # Technical deep-dive
├── user-interviews.txt          # Stakeholder feedback
├── slack-api-discussion.md      # Async team conversation
├── design-doc.pdf               # PDF design document
├── requirements-spec.docx       # Word requirements doc
└── manifest.json                # Auto-generated (don't edit manually)
```

---

## Skills Reference

### `/clu` — Full Pipeline

Runs the complete CLU pipeline: extract + synthesize + optionally generate PRD.

```
claude /clu                    # Default: analysis only
claude /clu --prd              # Include PRD generation
claude /clu --dir ./path       # Custom transcript directory
```

### `/clu-analyze` — Analysis Only

Same as `/clu` but explicitly skips PRD generation. Use when you want reports but not a Basher build plan.

```
claude /clu-analyze
```

### `/clu-prd` — PRD from Analysis

Generates a Basher-compatible PRD from an existing `analysis.json`. Use after you've reviewed and resolved conflicts.

```
claude /clu-prd
```

**Conflict handling modes:**
- `open-questions` (default) — Unresolved conflicts become open questions in the PRD
- `strongest-consensus` — Auto-resolve in favor of the position with more sources
- `ask-user` — Prompt for resolution on each conflict

---

## Output Files

### Level 1: Act On This

These require immediate attention:

| File | Contents |
|------|----------|
| `SUMMARY.md` | Executive summary: transcript count, extraction stats, consensus highlights, conflict count, gap count |
| `conflicts.md` | Each contradiction with both positions, source citations, and suggested resolution |
| `gaps.md` | Concepts referenced in discussions but never defined (e.g., "the auth system" with no spec) |

### Level 2: Verified Consensus

Consolidated, actionable information:

| File | Contents |
|------|----------|
| `decisions.md` | Chronological decision log — what was decided, by whom, whether it was confirmed or contradicted later |
| `requirements.md` | All requirements ranked by consensus (mentioned in N sources), categorized by domain |
| `stakeholders.md` | Who cares about what, decision authority, contact frequency |
| `action-items.md` | Action items with owners, deadlines, source transcripts, status |

### Level 3: Reference

Machine-readable data and raw extractions:

| File | Contents |
|------|----------|
| `analysis.json` | Full structured synthesis — all entities, cross-references, consensus scores |
| `extractions/*.json` | Per-transcript raw extraction JSONs (one per input file) |

---

## Configuration

### File: `./clu/clu.config.json`

```json
{
  "clu": {
    "maxConcurrent": 3,
    "extractorModel": "sonnet",
    "synthesizerModel": "opus",
    "autoManifest": true,
    "prdGeneration": false,
    "conflictHandling": "open-questions"
  }
}
```

### Options

| Setting | Default | Description |
|---------|---------|-------------|
| `maxConcurrent` | `3` | Maximum parallel extraction subagents. Increase for more transcripts, decrease if hitting rate limits. |
| `extractorModel` | `"sonnet"` | Model for per-transcript extraction. Sonnet is fast and cost-effective. |
| `synthesizerModel` | `"opus"` | Model for cross-reference synthesis. Opus handles complex reasoning better. |
| `autoManifest` | `true` | Auto-generate transcript manifest before extraction. Set to `false` to use a manually curated manifest. |
| `prdGeneration` | `false` | Auto-generate Basher-compatible PRD after synthesis. Override per-run with `--prd` flag. |
| `conflictHandling` | `"open-questions"` | How to handle unresolved conflicts in PRD: `open-questions`, `strongest-consensus`, or `ask-user`. |

---

## Extraction Templates

Templates control which entity types the LLM extracts, letting you focus on what matters and reduce token usage.

### Built-in Templates

| Template | Sections | Best For |
|----------|----------|----------|
| `default` | All 8 entity types | Comprehensive analysis |
| `requirements-only` | requirements, technicalConstraints, openQuestions | PRD generation, spec analysis |
| `decisions-only` | participants, decisions, actionItems, deferredItems | Decision logs, governance tracking |

### Using Templates

**Via API:**
```bash
curl -X POST /api/v1/projects/{id}/analyze \
  -H "Content-Type: application/json" \
  -d '{"extraction_template": "requirements-only"}'
```

**List available templates:**
```bash
curl /api/v1/templates/extraction
```

### Custom Templates

Create a JSON file following this structure:

```json
{
  "name": "my-template",
  "description": "What this template is for",
  "sections": ["decisions", "risks"],
  "guidelines": "Focus on decisions and risk identification."
}
```

Valid sections: `participants`, `decisions`, `actionItems`, `requirements`, `technicalConstraints`, `openQuestions`, `risks`, `deferredItems`.

Template files can also be placed in `templates/extraction-templates/` for reuse.

---

## Running CLU

### Via Claude Code Skills (Interactive)

Best for first-time use and when you want to review results interactively:

```bash
claude           # Start Claude Code
/clu             # Run full pipeline
```

### Via Bash Script (Autonomous / AFK)

Best for running CLU unattended or in CI:

```bash
# Basic analysis
~/.basher/clu.sh

# With PRD generation
~/.basher/clu.sh --prd

# Custom transcript directory
~/.basher/clu.sh --dir ~/project-notes

# Skip CacheBash MCP check
~/.basher/clu.sh --no-mcp-check
```

### Script Options

| Flag | Description |
|------|-------------|
| `--prd` | Generate Basher-compatible PRD after analysis |
| `--wizard` | Launch interactive conflict resolution wizard |
| `--dir PATH` | Path to transcripts directory (default: `./clu/transcripts`) |
| `--no-mcp-check` | Skip CacheBash MCP configuration check |
| `-h, --help` | Show usage information |

---

## Incremental Analysis

After your initial analysis, you can add new transcripts and re-analyze without re-extracting everything.

### How It Works

1. Only **new transcripts** (those without existing extractions) are extracted
2. **All extractions** (new + cached) are re-indexed in ChromaDB
3. **Synthesis re-runs** on the complete dataset for an updated cross-reference
4. Results include metadata: `incremental: true`, `new_transcripts`, `total_transcripts`

### Via API

```bash
# Add new transcripts to the project
curl -X POST /api/v1/projects/{id}/transcripts \
  -F "file=@new-meeting.txt"

# Run incremental analysis (requires a previous completed analysis)
curl -X POST /api/v1/projects/{id}/analyze/incremental
```

### When to Use

- New meeting notes arrive after initial analysis
- A stakeholder sends follow-up requirements
- You want to add context without re-extracting 10+ existing transcripts

Incremental analysis saves time and API costs by only calling the LLM for new content.

---

## Conflict Resolution Wizard

An interactive CLI for resolving conflicts found by CLU analysis.

### Running the Wizard

```bash
# Via clu.sh
~/.basher/clu.sh --wizard

# Directly
scripts/clu-wizard.sh --dir ./clu
```

### What It Does

The wizard reads `analysis.json`, presents each unresolved conflict, and lets you:

- **[A/B/...]** Accept a specific position
- **[c]** Enter a custom resolution
- **[d]** Defer to Open Questions
- **[s]** Skip (leave unresolved)

### Output

Resolutions are saved back to `analysis.json` and `conflicts.md` is regenerated with resolved conflicts shown as strikethrough.

### Workflow

```
clu.sh --wizard
  → Reads analysis.json
  → For each unresolved conflict:
      Shows topic, positions, sources, suggested resolution
      Asks for your choice
      Saves resolution to analysis.json
  → Regenerates conflicts.md
  → Shows summary (resolved/skipped)
```

After resolving conflicts, run `/clu-prd` to generate a PRD that incorporates your decisions.

---

## Review Checkpoints

CLU has 4 review checkpoints. When running via `clu.sh` with CacheBash enabled, you can review from your phone.

| Checkpoint | When | What You Can Do |
|------------|------|-----------------|
| 1. Manifest | After transcript discovery | Exclude files, correct metadata, adjust types |
| 2. Extractions | After Phase 2 | Review per-transcript extractions, correct errors |
| 3. Analysis | After Phase 3 | Resolve conflicts, edit reports, adjust priorities |
| 4. PRD | After Phase 4 | Edit stories before `/basher-convert` |

### Resolving Conflicts

Conflicts are the most important output. Each conflict in `conflicts.md` shows:

```
## Conflict 1: API Protocol

**Position A** (2 sources): "Use REST"
  - Alice (meeting-jan15.txt): "REST is simpler and our team knows it"
  - API Spec (api-spec.md): "RESTful endpoints for all resources"

**Position B** (1 source): "Use GraphQL"
  - Bob (slack-thread.md): "GraphQL would reduce over-fetching"

**Suggested Resolution**: Position A (stronger consensus)
```

After reviewing, you can:
1. Run the **conflict resolution wizard**: `clu.sh --wizard` (recommended)
2. Edit `conflicts.md` directly with your resolution
3. Re-run `/clu-prd` to generate an updated PRD
4. Or use the `ask-user` conflict handling mode for interactive resolution

---

## End-to-End Example

### Real-World Test: User Management API

This example is from an actual live test of the full CLU → Basher pipeline. Three transcripts with planted contradictions went through the complete pipeline and produced a working API.

#### The Transcripts

**`meeting-kickoff.txt`** — Project kickoff (2 participants: Alice PM, Bob Developer)
```
Alice: Let's build a REST API for user management.
Bob: Sounds good. Node.js and Express?
Alice: Yes. Email and password auth first, OAuth can wait.
Bob: What about a database?
Alice: Start simple. We can figure that out.
```

**`design-review.txt`** — Technical deep-dive (3 participants: Alice, Bob, Charlie Architect)
```
Charlie: Have we considered GraphQL? It would reduce over-fetching.
Alice: We decided on REST in the kickoff. Let's keep it simple.
Charlie: Fine, but we should add rate limiting on all public endpoints.
Bob: Agreed. Standard rate limits, maybe 100 requests per minute.
```

**`stakeholder-feedback.md`** — Stakeholder requirements (5 participants including VP Engineering, Security Lead)
```
VP Engineering: I want 95% test coverage minimum. No exceptions.
Security Lead: All passwords must be hashed with bcrypt. And we need
OAuth support for the launch — not later, for launch.
CEO: I told Alice OAuth can wait until v2. Let's ship fast.
```

Note the **planted conflicts**: REST vs GraphQL (Charlie vs team), and OAuth timing (CEO vs Security Lead).

#### Step 1: Set Up

```bash
mkdir user-api && cd user-api && git init
~/.basher/basher-init.sh
cp meeting-kickoff.txt design-review.txt stakeholder-feedback.md ./clu/transcripts/
```

#### Step 2: Analyze

```bash
claude /clu-analyze
```

CLU runs 3 Sonnet subagents in parallel, each extracting structured data. Then Opus cross-references everything.

**Results:**
- 30 entities extracted across 3 transcripts
- 8 unique participants (deduplicated across sources)
- 13 requirements ranked by consensus
- 8 decisions tracked chronologically
- **2 conflicts detected:**
  1. **API Protocol**: REST (2 sources, Alice + Bob) vs GraphQL (1 source, Charlie)
  2. **OAuth Timing**: "OAuth later" (CEO, Alice) vs "OAuth for launch" (Security Lead)
- **5 gaps identified:** database technology, rate limit specifics, deployment strategy, enterprise client definition, dark mode specs

#### Step 3: Review Conflicts

```bash
cat ./clu/conflicts.md
```

Each conflict shows both positions with source citations and suggested resolution based on consensus strength. In this case:
- REST wins (2 sources vs 1)
- OAuth timing remains an open question (authority conflict: CEO vs Security Lead)

#### Step 4: Generate PRD

```bash
claude /clu-prd
```

CLU maps 13 requirements into 6 user stories:

| Priority | Story | Consensus |
|----------|-------|-----------|
| P1 | US-001: Initialize Node.js + Express | 3 sources |
| P1 | US-002: User data model and database layer | 2 sources |
| P1 | US-003: User CRUD REST API endpoints | 3 sources |
| P2 | US-004: Email/password authentication | 2 sources |
| P2 | US-005: Rate limiting on public endpoints | 1 source (Charlie) |
| P2 | US-006: Test infrastructure and coverage | 1 source (VP Eng, but critical) |

The OAuth conflict becomes an "Open Question" in the PRD rather than a premature decision.

#### Step 5: Convert and Build

```bash
claude /basher-convert     # PRD → prd.json
~/.basher/basher.sh        # Autonomous implementation
```

Basher runs 6 iterations (one per story):
- Each iteration starts a fresh Claude session
- Reads `progress.txt` for learnings from previous iterations
- Implements one story, runs quality gates, commits

#### Results

```
BASHER COMPLETE - All stories implemented!

Branch: basher/user-management-api
Commits: 13
Test suites: 6
Tests: 89 passing
Coverage: 99.58% statements, 96.26% branches, 100% functions
```

**What was built:**
- Express 5.2.1 REST API with app/server separation
- SQLite database (better-sqlite3) with WAL mode
- Full CRUD endpoints with pagination and validation
- JWT authentication with bcrypt password hashing
- In-memory rate limiting (100 unauth, 200 auth req/min)
- Jest 30 test suite with 95%+ coverage thresholds

**Knowledge captured in `progress.txt`:**
- Express 5 vs 4 gotchas (error handler signatures, JSON parse error types)
- ESLint 10 flat config requirements (Node 24 globals: fetch, setInterval, etc.)
- SQLite unique constraint error codes
- Pattern: `app.listen(0)` for random port assignment in tests

The full pipeline: 3 messy transcripts → CLU analysis → 6 user stories → 89 passing tests.

---

## Troubleshooting

### "No supported files found"

**Problem:** CLU can't find transcripts.

**Solution:**
```bash
ls ./clu/transcripts/           # Check files exist
# Supported formats: .txt, .md, .pdf, .docx
```

### Extractions are missing entities

**Problem:** CLU didn't extract something you expected.

**Solution:**
1. Check the raw extraction: `cat ./clu/extractions/{file}.json`
2. The entity may be implied rather than explicit — CLU marks these with lower confidence
3. Consider adding more context to your transcripts (speaker names, roles)

### Conflicts seem wrong

**Problem:** CLU flagged something as a conflict that isn't one.

**Solution:**
1. Check the source quotes in `conflicts.md`
2. The same concept may have been discussed differently in different contexts
3. Edit `conflicts.md` to resolve false positives, then re-run `/clu-prd`

### CacheBash not sending updates

**Problem:** No mobile notifications during CLU runs.

**Solution:**
```bash
claude mcp list                  # Check CacheBash is configured
# If not configured:
claude mcp add --transport http cachebash \
  "https://cachebash-mcp-922749444863.us-central1.run.app/v1/mcp" \
  --header "Authorization: Bearer YOUR_API_KEY"
```

### Script errors

**Problem:** `clu.sh` fails with syntax or runtime errors.

**Solution:**
```bash
bash -n ~/.basher/clu.sh         # Check syntax
bash -n ~/.basher/lib/transcript-utils.sh
```

### CLU iterations complete instantly

**Problem:** `clu.sh` runs but iterations finish in under 1 second with no analysis output.

**Cause:** The script was using `--prompt-file` which is not a valid Claude CLI flag. The `|| true` in the script silently swallowed the error.

**Solution:** Update to the latest version. The fix pipes the prompt via stdin:
```bash
# Broken (old):
claude --prompt-file "$prompt_file" --dangerously-skip-permissions

# Fixed (current):
cat "$prompt_file" | claude -p --dangerously-skip-permissions
```

See [Anti-Patterns](TROUBLESHOOTING.md#anti-patterns--known-pitfalls) for the full list of known pitfalls.

---

## CLU API — Getting Started

The CLU API (`clu-api/`) is a FastAPI microservice that exposes CLU as a REST API. Use it for production deployments, CI pipelines, or team-wide access.

### Prerequisites

- Docker and docker-compose installed
- Anthropic API key

### Local Development Setup

```bash
cd clu-api

# Create .env file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Optional: seed sample data
docker-compose exec api python scripts/seed.py
```

The API is available at `http://localhost:8000`. Interactive Swagger docs at `http://localhost:8000/docs`.

### API Workflow

```bash
# 1. Create a project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "my-project"}'

# 2. Upload transcripts (supports .txt, .md, .pdf, .docx)
curl -X POST http://localhost:8000/api/v1/projects/1/transcripts \
  -F "file=@meeting-notes.txt"

# 3. Trigger analysis
curl -X POST http://localhost:8000/api/v1/projects/1/analyze

# 4. Poll status
curl http://localhost:8000/api/v1/projects/1/analysis/status

# 5. Get results
curl http://localhost:8000/api/v1/projects/1/analysis/results
```

### Production Features (v0.4)

| Feature | Description |
|---------|-------------|
| **API key auth** | Header: `X-API-Key`. Keys managed via database. |
| **Rate limiting** | Redis-backed sliding window. Configurable per-key limits. |
| **Tenant isolation** | All queries scoped by `tenant_id`. Data never leaks between tenants. |
| **Job recovery** | Failed analyses resume from last checkpoint instead of restarting. |
| **Structured logging** | JSON logs with request IDs for tracing. |
| **Health checks** | `GET /health` returns service status including DB, Redis, ChromaDB connectivity. |

### GCP Cloud Run Deployment

```bash
# Deploy via Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# Or build and push manually
docker build -t gcr.io/PROJECT/clu-api .
docker push gcr.io/PROJECT/clu-api
gcloud run deploy clu-api --image gcr.io/PROJECT/clu-api
```

Required environment variables for production: `DATABASE_URL`, `ANTHROPIC_API_KEY`, `REDIS_URL`, `CHROMADB_HOST`.

For full API endpoint reference, see [clu-api/README.md](../clu-api/README.md).

---

## Technology Learning Module

CLU is designed to evolve from a CLI skill (v0.1) to a full API microservice (v0.2+). This section covers the technologies used in the full roadmap, providing enough context to understand the architecture and discuss it credibly.

### FastAPI (v0.2+)

**What it is:** A modern Python web framework for building APIs, known for automatic OpenAPI docs, type validation, and async support.

**Why CLU uses it:** FastAPI's async capabilities handle concurrent LLM calls efficiently. Pydantic integration validates extraction schemas. Auto-generated docs make the API self-documenting.

**Core concepts:**
- **Path operations** — Route handlers decorated with `@app.get("/path")`
- **Dependency injection** — Database sessions, auth, injected via `Depends()`
- **Background tasks** — Long-running analysis jobs run asynchronously
- **Pydantic models** — Request/response validation with type hints

**How it works in CLU:**
```python
@app.post("/api/v1/projects/{project_id}/analyze")
async def trigger_analysis(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job = create_analysis_job(db, project_id)
    background_tasks.add_task(run_analysis_pipeline, job.id)
    return {"job_id": job.id, "status": "started"}
```

**Talking points:** "We chose FastAPI over Flask/Django because the async-first design handles concurrent Anthropic API calls without blocking, and Pydantic models enforce extraction schema contracts at the API boundary."

### SQLAlchemy + PostgreSQL (v0.2+)

**What it is:** SQLAlchemy is Python's most popular ORM. PostgreSQL is a production-grade relational database.

**Why CLU uses it:** Structured data (projects, transcripts, extractions, analyses) maps naturally to relational tables. PostgreSQL's JSONB columns store variable extraction data while keeping relational integrity.

**Core concepts:**
- **Declarative models** — Python classes map to database tables
- **Sessions** — Unit-of-work pattern for transactions
- **Alembic migrations** — Version-controlled schema changes
- **JSONB columns** — Store extraction data (variable shape) alongside fixed columns

**How it works in CLU:**
```python
class Extraction(Base):
    __tablename__ = "extractions"
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"))
    data_json = Column(JSONB)           # Variable extraction data
    confidence = Column(Float)           # 0.0-1.0
    tenant_id = Column(String)           # Multi-tenant from day one
```

**Talking points:** "tenant_id is on every model from day one — not as premature optimization, but because retrofitting multi-tenancy is one of the hardest migrations to do later."

### Redis (v0.3+)

**What it is:** An in-memory data store used for caching, job queues, and rate limiting.

**Why CLU uses it:** LLM calls are expensive. Caching extraction results by transcript content hash avoids redundant API calls. Redis also backs rate limiting for the production API.

**Core concepts:**
- **Key-value store** — Simple get/set with TTL (expiration)
- **Hashing** — Cache keyed on SHA-256 of transcript content
- **Sliding window** — Rate limiting with sorted sets
- **Pub/sub** — Job status notifications (optional)

**How it works in CLU:**
```python
cache_key = f"extraction:{hashlib.sha256(content.encode()).hexdigest()}"
cached = redis.get(cache_key)
if cached:
    return json.loads(cached)  # Skip LLM call
result = await extract_with_anthropic(content)
redis.setex(cache_key, 86400, json.dumps(result))  # Cache for 24h
```

**Talking points:** "We cache by content hash, not filename, so re-analyzing the same transcript — even under a different name — hits the cache. This saves significant API costs for iterative workflows."

### ChromaDB (v0.3+)

**What it is:** An open-source vector database for semantic search using embeddings.

**Why CLU uses it:** Keyword matching misses semantic relationships. "REST API" and "RESTful endpoints" are the same concept. ChromaDB embeds extracted entities as vectors and finds semantic similarities for better conflict detection and consensus ranking.

**Core concepts:**
- **Embeddings** — Convert text to high-dimensional vectors
- **Collections** — Groups of related embeddings (one per project)
- **Similarity search** — Find semantically similar entities across transcripts
- **Metadata filtering** — Filter by entity type, source, confidence

**How it works in CLU:**
```python
collection = chroma.get_or_create_collection(f"project-{project_id}")
collection.add(
    documents=[req["description"] for req in requirements],
    metadatas=[{"source": req["source"], "type": "requirement"} for req in requirements],
    ids=[f"req-{i}" for i in range(len(requirements))]
)
# Find semantically similar requirements across transcripts
similar = collection.query(query_texts=["user authentication"], n_results=5)
```

**Talking points:** "ChromaDB catches conflicts that keyword matching misses. Two stakeholders might say 'REST API' and 'GraphQL endpoint' — both are about API protocol, and semantic similarity flags the disagreement."

### Anthropic SDK (v0.2+)

**What it is:** The official Python SDK for calling Claude models directly.

**Why CLU uses it (instead of LangChain):** Direct API calls are simpler to debug, have fewer abstraction layers, and give full control over prompts and responses. LangChain adds complexity without proportional benefit for CLU's use case.

**Core concepts:**
- **Messages API** — Send messages with system prompts and get responses
- **Model selection** — Choose between Sonnet (fast/cheap) and Opus (capable)
- **Structured output** — Prompt engineering for JSON extraction
- **Token management** — Monitor usage for cost tracking

**How it works in CLU:**
```python
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",  # Or use alias "sonnet" in CLI
    max_tokens=8192,
    system=extraction_system_prompt,
    messages=[{"role": "user", "content": f"Extract entities from:\n\n{transcript}"}]
)
extraction = json.loads(response.content[0].text)
```

**Talking points:** "We use the Anthropic SDK directly rather than LangChain because our prompt logic is the core IP — we need full control over what goes to the model and how we parse responses. LangChain's abstractions would add indirection without value here."

### Docker (v0.2+)

**What it is:** Containerization platform that packages applications with their dependencies.

**Why CLU uses it:** Consistent development environment (PostgreSQL, Redis, ChromaDB all running locally). Single `docker-compose up` to start everything. Same containers deploy to production (Cloud Run).

**Core concepts:**
- **Dockerfile** — Build instructions for the application image
- **docker-compose** — Multi-container orchestration (API + DB + Redis + ChromaDB)
- **Volumes** — Persistent data storage for databases
- **Networks** — Container-to-container communication

**How it works in CLU:**
```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports: ["8000:8000"]
    depends_on: [db, redis]
  db:
    image: postgres:16
    volumes: [pgdata:/var/lib/postgresql/data]
  redis:
    image: redis:7-alpine
```

**Talking points:** "Docker-compose gives us a one-command development environment. The same Dockerfile deploys to Cloud Run in production, so there's no environment drift between dev and prod."
