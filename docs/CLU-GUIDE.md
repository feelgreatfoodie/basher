# CLU User Guide

> **Codified Likeness Utility** — Turn 10 messy transcripts into one clear build plan.

CLU ingests multiple text transcripts (meeting notes, interviews, Slack threads, spec documents), extracts structured data from each, cross-references across all sources, and produces actionable reports. Optionally generates a Basher-compatible PRD for autonomous code generation.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [The Pipeline](#the-pipeline)
3. [Input: Transcripts](#input-transcripts)
4. [Skills Reference](#skills-reference)
5. [Output Files](#output-files)
6. [Configuration](#configuration)
7. [Running CLU](#running-clu)
8. [Review Checkpoints](#review-checkpoints)
9. [End-to-End Example](#end-to-end-example)
10. [Troubleshooting](#troubleshooting)
11. [Technology Learning Module](#technology-learning-module)

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

CLU scans `./clu/transcripts/` for `.txt` and `.md` files. For each file, it:
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
| `--dir PATH` | Path to transcripts directory (default: `./clu/transcripts`) |
| `--no-mcp-check` | Skip CacheBash MCP configuration check |
| `-h, --help` | Show usage information |

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
1. Edit `conflicts.md` directly with your resolution
2. Re-run `/clu-prd` to generate an updated PRD
3. Or use the `ask-user` conflict handling mode for interactive resolution

---

## End-to-End Example

### Scenario: Planning a User Authentication System

You have 3 transcripts from different meetings about adding auth to your app.

#### 1. Set Up

```bash
cd my-project
~/.basher/basher-init.sh       # Creates ./clu/transcripts/
```

#### 2. Add Transcripts

```bash
# Copy your meeting notes
cp ~/notes/kickoff-auth.txt ./clu/transcripts/
cp ~/notes/security-review.txt ./clu/transcripts/
cp ~/notes/ux-feedback.txt ./clu/transcripts/
```

#### 3. Run CLU with PRD

```bash
claude /clu --prd
```

CLU will:
- Discover 3 transcripts, generate manifest
- Extract entities from each (participants, decisions, requirements, etc.)
- Cross-reference: find that all 3 mention "email/password login" (high consensus), but kickoff says "OAuth later" while security-review says "OAuth required for launch" (conflict!)
- Generate reports highlighting the OAuth conflict
- Generate a Basher-compatible PRD with the conflict as an open question

#### 4. Review

```bash
# Check the executive summary
cat ./clu/SUMMARY.md

# Resolve the OAuth conflict
vim ./clu/conflicts.md          # Add your resolution

# Review the PRD
vim ./basher/prd.md              # Edit if needed
```

#### 5. Continue to Basher

```bash
claude /basher-convert           # Convert PRD to JSON tasks
~/.basher/basher.sh              # Run autonomous implementation
```

The full pipeline: transcripts → CLU → PRD → Basher → working auth system.

---

## Troubleshooting

### "No .txt or .md files found"

**Problem:** CLU can't find transcripts.

**Solution:**
```bash
ls ./clu/transcripts/           # Check files exist
# Files must have .txt or .md extension
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
    model="claude-sonnet-4-5-20250929",
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
