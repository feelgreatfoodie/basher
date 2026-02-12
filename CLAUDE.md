# Basher for Claude Code

## Project Overview

Basher is an autonomous code generation system that uses Claude Code to implement entire projects from meeting notes or PRDs. It breaks work into small tasks, runs each in a fresh Claude session, and commits changes incrementally.

**New in v2:** CacheBash integration for mobile communication, parallel story execution, and smart error recovery.

**New in v3:** Hybrid model architecture (Opus orchestrator + Sonnet subagents), continuous interrupt polling, dynamic sprint insertion, and enhanced Opus code review.

**New: CLU** (Codified Likeness Utility) — Multi-transcript analysis and synthesis engine. Ingests 10+ mixed-format transcripts (.txt, .md, .pdf, .docx), extracts structured data, cross-references across sources, and produces actionable reports. Available as CLI skills (v0.1) and a FastAPI microservice (v0.2+) with PostgreSQL, ChromaDB semantic search, Redis caching, API key auth, rate limiting, tenant isolation, and GCP Cloud Run deployment.

## Repository Structure

```
basher/
├── scripts/                    # Core execution scripts
│   ├── basher.sh              # Main execution loop (sequential + parallel modes)
│   ├── basher-init.sh         # Project initialization
│   ├── package.sh             # Create shareable package
│   ├── clu.sh                 # CLU execution script
│   ├── clu-wizard.sh          # Interactive conflict resolution wizard
│   └── kickoff-clu.sh         # CLU continuous AFK build (v0.1→v1.0)
├── prompts/                    # Agent prompts for parallel mode
│   ├── orchestrator.md        # Main orchestrator prompt
│   └── subagent-story.md      # Subagent prompt for parallel work
│   ├── clu-orchestrator.md    # CLU orchestrator (extraction + synthesis)
│   └── clu-subagent-extract.md # CLU extraction subagent
├── skills/                     # Claude Code skills (prompt templates)
│   ├── prd/                   # /prd - Generate PRD from notes
│   ├── basher-convert/        # /basher-convert - PRD to JSON
│   ├── compose-prd/           # /compose-prd - Merge domain PRDs
│   ├── extract-domain/        # /extract-domain - Extract from codebase
│   ├── kickoff/               # /kickoff - Interactive project setup
│   ├── verify-blueprint/      # /verify-blueprint - Validate blueprint
│   ├── clu/                   # /clu - Full CLU pipeline (extract + synthesize + PRD)
│   ├── clu-analyze/           # /clu-analyze - Extract + synthesize only
│   └── clu-prd/               # /clu-prd - Generate PRD from CLU analysis
├── lib/                        # Shared bash libraries
│   ├── detect-stack.sh        # Tech stack auto-detection
│   └── transcript-utils.sh    # CLU transcript utilities
├── docs/                       # Documentation
│   ├── CLU-GUIDE.md           # CLU user guide + learning module
│   ├── QUICK-START.md         # Quick start (Basher + CLU paths)
│   └── TROUBLESHOOTING.md     # Troubleshooting + anti-patterns
├── templates/                  # Configuration templates
│   ├── basher.config.json     # Basher config template
│   ├── clu.config.json        # CLU config template
│   └── extraction-templates/  # CLU extraction templates (default, requirements-only, decisions-only)
├── clu-api/                    # CLU FastAPI microservice (v0.2+)
│   ├── app/                   # FastAPI application
│   │   ├── api/               # Route handlers (projects, transcripts, analysis)
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # Business logic (extraction, synthesis, parsers, cache, recovery)
│   │   ├── middleware/        # Auth, rate limiting, tenant isolation
│   │   └── prompts/           # Prompt templates for Anthropic SDK
│   ├── alembic/               # Database migrations
│   ├── tests/                 # pytest test suite (API + services)
│   ├── docker-compose.yml     # API + PostgreSQL + Redis + ChromaDB
│   ├── cloudbuild.yaml        # GCP Cloud Run deployment
│   └── README.md              # API documentation
├── saas-blueprint/             # Complete SaaS reference blueprint (separate git repo)
│   ├── domains/               # 8 domain extractions
│   ├── architecture/          # System design docs
│   ├── security/              # OWASP coverage, security patterns
│   ├── engineering/           # Best practices
│   └── questions/             # Planning frameworks
├── install.sh                  # One-line installer
├── prompt.md                   # Main iteration prompt (sequential mode)
└── README.md                   # User documentation
```

## Key Features

### Execution Modes

| Mode | Command | Description |
|------|---------|-------------|
| Sequential | `basher.sh` | One story at a time, iteration loop |
| Parallel | `basher.sh --parallel` | Orchestrator spawns subagents for concurrent work |

### CacheBash Integration

Basher communicates with users via mobile when running autonomously:
- **Status updates** - Track progress from your phone
- **Question asking** - Answer blocking questions via mobile app
- **Error notifications** - Get notified of failures immediately

### Smart Error Recovery

Quality gates now have intelligent debugging:
- Auto-fix lint/type errors (max 3 attempts)
- Analyze test failures (implementation vs test bug)
- Escalate to user via CacheBash when stuck

## Key Scripts

### basher.sh

Main autonomous execution loop:
- **Sequential mode**: Reads `./basher/prd.json`, runs one story per iteration
- **Parallel mode**: Uses orchestrator to spawn subagents for concurrent work
- Executes quality gates (lint, typecheck, test, build)
- Commits changes to git
- Updates status via CacheBash

New flags:
- `--parallel` - Enable orchestrator mode with parallel subagents
- `--sequential` - Force sequential mode (default)
- `--no-mcp-check` - Skip CacheBash MCP configuration check

### basher-init.sh

Initializes a project for Basher:
- Creates `./basher/` directory with prompts subdirectory
- Auto-detects tech stack
- Creates configuration files with new options
- Optionally sets up CacheBash MCP server
- Sets up progress tracking

New flags:
- `--skip-cachebash` - Skip CacheBash setup prompt

## Prompts

### prompt.md (Sequential Mode)

Instructions for a single Basher iteration:
- Read state from files
- Select next incomplete story
- Implement with smart recovery
- Commit and signal completion
- Communicate via CacheBash when blocked

### prompts/orchestrator.md (Parallel Mode)

Instructions for the orchestrator agent:
- Analyze PRD dependencies
- Group stories into parallelizable waves
- Spawn up to 3 subagents concurrently
- Coordinate commits in dependency order
- Handle failures and blocked subagents

### prompts/subagent-story.md

Template for subagent workers:
- Focused on single story implementation
- Reports back to orchestrator
- Uses CacheBash directly for questions
- Stages changes but does NOT commit
- Aware that Opus will review code before commit

## Continuous Interrupt Polling (v3)

During parallel execution, the orchestrator polls for interrupts every 2 minutes (configurable via `interruptPollSeconds`). This allows:

- **Immediate action** on interrupt-level tasks
- **Dynamic sprint insertion** via `sprint` action level
- **Course corrections** without waiting for wave completion

### Task Action Levels

| Action | Timing | Behavior |
|--------|--------|----------|
| `interrupt` | Immediate | Pause work, handle task now |
| `sprint` | Current wave | Add to running sprint if no dependency conflicts |
| `parallel` | Next available | Spawn subagent at next opportunity |
| `queue` | After current | Handle when current work completes |
| `backlog` | Eventually | Low priority, handle when idle |

## Configuration

`basher.config.json` options:

```json
{
  "quality": {
    "smartRecovery": true,
    "maxFixAttempts": 3
  },
  "claude": {
    "orchestratorModel": "opus",
    "subagentModel": "sonnet",
    "complexStoryModel": "opus",
    "reviewWithOrchestrator": true
  },
  "parallel": {
    "enabled": false,
    "maxConcurrent": 3
  },
  "cachebash": {
    "enabled": true,
    "pollIntervalSeconds": 30,
    "interruptPollSeconds": 120
  }
}
```

### Hybrid Model Architecture (v3)

| Setting | Default | Purpose |
|---------|---------|---------|
| `orchestratorModel` | opus | Model for the orchestrator (planning, review, coordination) |
| `subagentModel` | sonnet | Model for standard story implementation |
| `complexStoryModel` | opus | Model for high-complexity stories |
| `reviewWithOrchestrator` | true | Opus reviews all subagent code before commit |

**Cost optimization:** Sonnet handles ~80% of implementation work. Opus provides quality assurance through orchestration and code review.

## Skills (Slash Commands)

| Skill | Purpose |
|-------|---------|
| `/prd` | Generate structured PRD from meeting notes |
| `/basher-convert` | Convert PRD markdown to JSON task list |
| `/compose-prd` | Merge multiple domain PRD fragments |
| `/extract-domain` | Extract patterns from existing codebase |
| `/kickoff` | Interactive Q&A for new project setup |
| `/verify-blueprint` | Validate blueprint completeness |
| `/clu` | Full CLU pipeline: extract + synthesize + optional PRD |
| `/clu-analyze` | Extract + synthesize only (no PRD generation) |
| `/clu-prd` | Generate Basher PRD from existing CLU analysis |

## CLU — Multi-Transcript Analysis & Synthesis

CLU (Codified Likeness Utility) ingests multiple text transcripts, extracts structured data from each, cross-references across all sources, and produces actionable reports.

### Pipeline

```
./clu/transcripts/          Phase 1: Extract        Phase 2: Synthesize       Phase 3: PRD (optional)
 ├── meeting-1.txt    ──►  Per-transcript     ──►  Cross-reference      ──►  Basher-compatible
 ├── interview-2.txt       extraction JSONs         analysis + reports        prd.md / prd.json
 ├── spec-doc.pdf          (Sonnet, parallel)       (Opus, single pass)
 └── requirements.docx
```

### CLU Versions

| Version | Codename | What It Adds |
|---------|----------|-------------|
| v0.1 | "Prove the synthesis" | CLI skills, bash scripts, prompt templates |
| v0.2 | "Open the API" | FastAPI + PostgreSQL + Docker + Anthropic SDK |
| v0.3 | "Semantic intelligence" | ChromaDB embeddings, Redis caching, confidence scoring |
| v0.4 | "Production hardening" | API key auth, rate limiting, tenant isolation, GCP Cloud Run |
| v1.0 | "Make it useful daily" | PDF/DOCX ingestion, incremental analysis, conflict wizard, extraction templates |

### CLU Output Files

| File | Contents | Priority |
|------|----------|----------|
| `SUMMARY.md` | Executive summary — conflicts count, consensus highlights | Level 1: Act on this |
| `conflicts.md` | Contradictions with both positions + source citations | Level 1: Act on this |
| `gaps.md` | Referenced but undefined concepts | Level 1: Act on this |
| `decisions.md` | Chronological decision log with confirmation status | Level 2: Verified consensus |
| `requirements.md` | Consolidated requirements ranked by consensus | Level 2: Verified consensus |
| `stakeholders.md` | Who cares about what, decision authority | Level 2: Verified consensus |
| `action-items.md` | Action items with owners, sources, status | Level 2: Verified consensus |
| `analysis.json` | Full structured synthesis (machine-readable) | Level 3: Reference |

### CLU Configuration

`clu.config.json` options:

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

| Setting | Default | Purpose |
|---------|---------|---------|
| `maxConcurrent` | 3 | Max parallel extraction subagents |
| `extractorModel` | sonnet | Model for per-transcript extraction |
| `synthesizerModel` | opus | Model for cross-reference synthesis |
| `autoManifest` | true | Auto-generate transcript manifest |
| `prdGeneration` | false | Generate Basher PRD after analysis |
| `conflictHandling` | open-questions | How to handle conflicts: `open-questions`, `strongest-consensus`, `ask-user` |

### CLU Project Directory Structure

```
./clu/
├── transcripts/              # User drops text files here
│   ├── meeting-kickoff.txt
│   └── manifest.json         # Auto-generated metadata
├── extractions/              # Per-transcript extraction JSONs
├── SUMMARY.md                # Executive summary
├── conflicts.md              # Contradictions needing resolution
├── gaps.md                   # Referenced but undefined concepts
├── decisions.md              # Chronological decision log
├── requirements.md           # Ranked requirements
├── stakeholders.md           # Stakeholder map
├── action-items.md           # Action items with owners
├── analysis.json             # Full structured synthesis
└── clu.config.json           # CLU-specific config
```

### CLU API (v0.2+)

The `clu-api/` directory contains a FastAPI microservice that exposes CLU as a REST API. See [clu-api/README.md](clu-api/README.md) for full API docs.

**Key endpoints:**
- `POST /api/v1/projects` — Create a project
- `POST /api/v1/projects/{id}/transcripts` — Upload transcript (supports PDF/DOCX)
- `POST /api/v1/projects/{id}/analyze` — Trigger analysis (background job)
- `POST /api/v1/projects/{id}/analyze/incremental` — Incremental analysis (new transcripts only)
- `GET /api/v1/projects/{id}/analysis/results` — Get full results
- `GET /api/v1/templates/extraction` — List extraction templates

**Running locally:**
```bash
cd clu-api
docker-compose up -d                          # Start API + PostgreSQL + Redis + ChromaDB
docker-compose exec api alembic upgrade head   # Run migrations
# API at http://localhost:8000, docs at http://localhost:8000/docs
```

**Production features (v0.4):**
- API key authentication (header: `X-API-Key`)
- Redis-backed sliding window rate limiting
- Tenant isolation (all queries scoped by `tenant_id`)
- GCP Cloud Run deployment via `cloudbuild.yaml`
- Job recovery with checkpointing for failed analyses

### Running CLU

```bash
# Via Claude Code skills (interactive — recommended for first time)
claude /clu-analyze            # Step 1: Extract + synthesize (no PRD)
claude /clu-prd                # Step 2: Generate PRD from analysis
claude /basher-convert         # Step 3: Convert PRD to JSON tasks

# Via bash script (autonomous / AFK)
~/.basher/clu.sh               # Analysis only
~/.basher/clu.sh --prd         # Analysis + PRD generation
~/.basher/clu.sh --wizard      # Interactive conflict resolution
~/.basher/clu.sh --dir ~/notes # Custom transcript directory

# Via kickoff-clu.sh (builds CLU itself, not user-facing)
./scripts/kickoff-clu.sh --from v0.2 --yes   # Build from version, skip prompts
./scripts/kickoff-clu.sh --resume --yes       # Auto-detect and continue
```

### Full Pipeline (Recommended Workflow)

```bash
# 1. Set up project and add transcripts
mkdir my-project && cd my-project && git init
~/.basher/basher-init.sh
cp meeting-notes.txt design-review.txt ./clu/transcripts/

# 2. Analyze transcripts (inside Claude Code)
claude /clu-analyze

# 3. Review results
cat ./clu/SUMMARY.md           # Executive summary
cat ./clu/conflicts.md         # Contradictions to resolve

# 4. Generate PRD from analysis
claude /clu-prd

# 5. Convert to tasks and run autonomously
claude /basher-convert
~/.basher/basher.sh
```

### Testing CLU

```bash
# Syntax validation
bash -n scripts/clu.sh
bash -n lib/transcript-utils.sh

# Initialize CLU directories
~/.basher/basher-init.sh       # Creates ./clu/transcripts/ and ./clu/extractions/

# Run analysis
cp your-notes.txt ./clu/transcripts/
claude /clu-analyze
```

## Key Scripts (CLU-Specific)

### clu-wizard.sh

Interactive conflict resolution wizard:
- Reads `analysis.json` for unresolved conflicts
- Presents each conflict with positions, sources, and suggested resolution
- Options: accept position A/B, custom resolution, defer, skip
- Saves resolutions back to `analysis.json`
- Regenerates `conflicts.md` with resolved items

### kickoff-clu.sh

Meta-build script for building CLU itself (v0.1→v1.0):
- Chains through version builds, each as a fresh Claude session
- `--from VERSION` / `--to VERSION` to target specific range
- `--resume` auto-detects last completed version
- `-y / --yes` bypasses all interactive prompts (required for background execution)
- Each version generates a prompt, pipes it to Claude, and pushes commits

## The saas-blueprint

A complete reference implementation extracted from a real SaaS project:

### Domains (8 total)
- **auth** - Firebase Auth, RBAC, multi-tenant
- **database** - Firestore patterns, security rules
- **api** - Next.js route handlers, middleware
- **ui** - React components, forms, state
- **realtime** - Firestore subscriptions
- **notifications** - Email, in-app alerts
- **compliance** - GDPR, audit logging
- **testing** - Jest, Playwright, Storybook

### Domain Structure
Each domain has 6 standard files:
```
domains/[name]/
├── README.md           # Overview and quick links
├── patterns.md         # Implementation patterns with code
├── deep-dive.md        # Educational: WHY these patterns work
├── questions.md        # Planning questions (15-25)
├── prd-fragment.md     # User stories for Basher
└── templates/          # Reusable code snippets
```

## Development Conventions

### Commits
- Use conventional commits format
- All commits authored by `feelgreatfoodie` (NEVER add co-author)
- Use `--author="feelgreatfoodie <feelgreatfoodie@users.noreply.github.com>"` flag
- NEVER use `Co-Authored-By:` in commit messages

### File Naming
- Scripts: `kebab-case.sh`
- Skills: `skill-name/prompt.md`
- Prompts: `agent-name.md`
- Domains: lowercase single word (auth, api, ui)

### Quality Gates
When modifying scripts:
- Test with `bash -n script.sh` for syntax
- Test initialization on empty directory
- Verify quality gate detection works

### Blueprint Verification
After modifying saas-blueprint:
```bash
./saas-blueprint/scripts/verify-blueprint.sh ./saas-blueprint
```

## Critical Rules

1. **Fresh Context Per Task** - Basher's key innovation. Each task runs in a new Claude session to prevent confusion.

2. **External State** - All important information must be in files (progress.txt, prd.json), not Claude's memory.

3. **Quality Gates** - Every task must pass lint, typecheck, test, and build before committing.

4. **Incremental Commits** - One commit per task with descriptive message.

5. **CacheBash Communication** - Ask questions via mobile rather than guessing on ambiguous requirements.

6. **Smart Recovery** - Try to fix errors automatically before escalating to user.

7. **Knowledge Capture** - Learnings must be captured and promoted to appropriate levels.

8. **Commit Authorship** - ALL commits authored by `feelgreatfoodie`. NEVER add co-author lines under any circumstances.

9. **Use Model Aliases** - Always use `opus`, `sonnet`, `haiku` instead of hardcoded model IDs like `claude-opus-4-5-20251101`. Aliases are forward-compatible.

10. **Pipe Prompts via stdin** - Claude CLI does NOT support `--prompt-file`. Always use `cat file | claude -p`.

## Anti-Patterns (Do NOT Do These)

These were discovered during live testing and caused real failures:

| Anti-Pattern | Why It's Bad | Correct Approach |
|-------------|-------------|-----------------|
| `claude --prompt-file file.md` | Not a valid CLI flag; fails silently with `\|\| true` | `cat file.md \| claude -p` |
| `|| true` without output validation | Swallows ALL errors including catastrophic ones | Check output length/content after `\|\| true` |
| Hardcoded model IDs (`claude-opus-4-5-20251101`) | Breaks when Anthropic releases new versions | Use aliases: `opus`, `sonnet`, `haiku` |
| Assuming `main` branch exists | Some repos use `master`; branch creation fails | Check `git.baseBranch` config or detect dynamically |
| Skills only in `skills/*/prompt.md` | Claude Code can't discover them as slash commands | Must also register in `.claude/commands/` |
| Running `basher.sh` without initial commit | Can't create branch from non-existent `main` | Always ensure at least one commit exists |

## Learnings from Live Testing (2026-02-11)

### CLU Pipeline
- Sonnet handles transcript extraction well in parallel (3 concurrent subagents)
- Opus cross-reference synthesis catches subtle conflicts that would be missed with keyword matching alone
- Conflict detection works best when transcripts include speaker names and explicit positions
- The `open-questions` conflict mode is the safest default — lets humans resolve ambiguity

### Basher Sequential Mode
- Fresh context per iteration is the key innovation — iteration #6 is as accurate as iteration #1
- `progress.txt` as a knowledge accumulation mechanism works well — later iterations build on earlier learnings
- Express 5, ESLint 10 flat config, Jest 30, Node 24 — modern tooling works cleanly with Basher
- Story granularity matters: 6 stories for a REST API with auth is about right (not too few, not too many)
- Quality gates (lint + test) catch real issues and force the agent to fix them before proceeding

### Claude CLI
- `-p` / `--print` is the correct flag for non-interactive (piped) mode
- `--dangerously-skip-permissions` is required for fully autonomous execution
- Model aliases (`opus`, `sonnet`) work and are preferred over full model IDs
- The CLI accepts prompts via stdin: `echo "prompt" | claude -p`

## Knowledge Accumulation System

Learnings flow upward through three tiers:

```
┌─────────────────────────────────────────────────────────────┐
│  ~/.basher/learnings.md (Global)                            │
│  Cross-project patterns, framework gotchas, tool configs    │
├─────────────────────────────────────────────────────────────┤
│  ./CLAUDE.md (Project)                                      │
│  Reusable patterns, critical rules, architecture notes      │
├─────────────────────────────────────────────────────────────┤
│  ./basher/progress.txt (Run)                                │
│  Story-specific learnings, iteration logs                   │
└─────────────────────────────────────────────────────────────┘
```

### What Goes Where

| Learning Type | progress.txt | CLAUDE.md | learnings.md |
|--------------|--------------|-----------|--------------|
| Story-specific implementation details | ✅ | ❌ | ❌ |
| Reusable code patterns | ✅ | ✅ | ❌ |
| Critical rules (must follow) | ✅ | ✅ | ❌ |
| Architecture insights | ✅ | ✅ | ❌ |
| Framework-specific gotchas | ✅ | ✅ | ✅ |
| Cross-project patterns | ✅ | ❌ | ✅ |

### Promotion Flow

1. **Subagent** discovers pattern → Reports in LEARNINGS field
2. **Orchestrator** consolidates → Writes to progress.txt, promotes to CLAUDE.md
3. **End of project** → Framework patterns promoted to ~/.basher/learnings.md
4. **Next project** → Agents read learnings.md for cross-project knowledge

## Testing Changes

### Test basher-init.sh
```bash
mkdir /tmp/test-project && cd /tmp/test-project
git init
/path/to/basher-init.sh
```

### Test basher.sh (Sequential)
```bash
cd test-project
# Add a simple prd.json
~/.basher/basher.sh
```

### Test basher.sh (Parallel)
```bash
cd test-project
# Add prd.json with multiple independent stories
~/.basher/basher.sh --parallel
```

### Test Blueprint Verification
```bash
./saas-blueprint/scripts/verify-blueprint.sh ./saas-blueprint
```

## Related Repositories

- `saas-blueprint/` - Separate git repo inside this project
- User projects use `./basher/` directory (created by basher-init.sh)

## Common Tasks

### Add a New Skill
1. Create `skills/[name]/prompt.md`
2. Document in README.md
3. Add to INDEX.md in saas-blueprint if relevant

### Add a New Domain to Blueprint
1. Use `/extract-domain` skill on source codebase
2. Verify with `/verify-blueprint`
3. Update manifest.json and INDEX.md

### Fix Blueprint Issues
1. Run verify-blueprint.sh to identify gaps
2. Fix missing files or content
3. Re-run verification
4. Commit to saas-blueprint repo

### Set Up CacheBash
1. Download CacheBash mobile app
2. Get API key from Settings
3. Run: `claude mcp add --transport http cachebash "https://cachebash-mcp-922749444863.us-central1.run.app/v1/mcp" --header "Authorization: Bearer YOUR_KEY"`

---

## Opus Code Review (v3)

Before committing any subagent work, the Opus orchestrator performs a mandatory code review:

1. **Read staged diff** - Examine actual code changes
2. **Quality assessment** - Clean, idiomatic, minimal complexity
3. **Acceptance criteria check** - All criteria satisfied
4. **Integration check** - No conflicts with parallel work
5. **Debug artifact check** - No console.log, TODO, etc.
6. **Quality gates** - lint, typecheck, test pass

Issues are handled by severity:
- **Minor** - Orchestrator fixes directly
- **Medium** - Spawn cleanup subagent
- **Major** - Ask user via CacheBash

*Last updated: 2026-02-11*
