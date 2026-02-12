#!/usr/bin/env bash
#
# CLU Build Kickoff — Continuous AFK build v0.1 → v1.0
#
# Usage: ./scripts/kickoff-clu.sh [OPTIONS]
#
#   --from VERSION    Start from a specific version (default: v0.1)
#   --to VERSION      Stop after a specific version (default: v1.0)
#   --resume          Auto-detect last completed version and continue from next
#   -y, --yes         Skip all interactive prompts (auto-accept)
#   -h, --help        Show usage
#
# Examples:
#   ./scripts/kickoff-clu.sh                    # Full build: v0.1 → v1.0
#   ./scripts/kickoff-clu.sh --from v0.2        # Start from v0.2 (assumes v0.1 done)
#   ./scripts/kickoff-clu.sh --to v0.1          # Only build v0.1
#   ./scripts/kickoff-clu.sh --resume           # Pick up where last run left off
#
# One branch (clu/full-build), one run, no intermediate reviews.
# Commit + push at every natural breakpoint. Review comprehensively after v1.0.
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

ALL_VERSIONS=("v0.1" "v0.2" "v0.3" "v0.4" "v1.0")
FROM_VERSION="v0.1"
TO_VERSION="v1.0"
RESUME=false
AUTO_YES=false

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
PLAN_FILE="$HOME/.claude/plans/kind-hugging-creek.md"
BRANCH_NAME="clu/full-build"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ============================================================================
# Argument Parsing
# ============================================================================

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --from VERSION    Start from version (default: v0.1)"
    echo "  --to VERSION      Stop after version (default: v1.0)"
    echo "  --resume          Auto-detect and resume from last completed version"
    echo "  -y, --yes         Skip all interactive prompts (auto-accept)"
    echo "  -h, --help        Show this help"
    echo ""
    echo "Versions: v0.1, v0.2, v0.3, v0.4, v1.0"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --from)   FROM_VERSION="$2"; shift 2 ;;
            --to)     TO_VERSION="$2"; shift 2 ;;
            --resume) RESUME=true; shift ;;
            -y|--yes) AUTO_YES=true; shift ;;
            -h|--help) usage; exit 0 ;;
            *) echo "Unknown option: $1"; usage; exit 1 ;;
        esac
    done
}

# ============================================================================
# Logging
# ============================================================================

log_info()    { echo -e "${BLUE}[kickoff]${NC} $1"; }
log_success() { echo -e "${GREEN}[kickoff]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[kickoff]${NC} $1"; }
log_error()   { echo -e "${RED}[kickoff]${NC} $1"; }
log_step()    { echo -e "${CYAN}[kickoff]${NC} -- $1"; }

# ============================================================================
# Version Helpers
# ============================================================================

# Get index of a version in ALL_VERSIONS (0-based)
version_index() {
    local v="$1"
    for i in "${!ALL_VERSIONS[@]}"; do
        if [[ "${ALL_VERSIONS[$i]}" == "$v" ]]; then
            echo "$i"
            return
        fi
    done
    echo "-1"
}

# Detect last completed version by checking for version artifacts
detect_last_completed() {
    cd "$REPO_DIR"
    if [[ -f "clu-api/app/middleware/auth.py" ]]; then
        # v0.4 artifacts exist — check for v1.0
        if [[ -f "scripts/clu-wizard.sh" ]]; then
            echo "v1.0"
        else
            echo "v0.4"
        fi
    elif grep -q "chromadb" "clu-api/pyproject.toml" 2>/dev/null; then
        echo "v0.3"
    elif [[ -d "clu-api" ]]; then
        echo "v0.2"
    elif [[ -f "scripts/clu.sh" ]]; then
        echo "v0.1"
    else
        echo "none"
    fi
}

# Get the next version after the given one
next_version() {
    local current="$1"
    local idx
    idx=$(version_index "$current")
    local next_idx=$((idx + 1))
    if [[ $next_idx -lt ${#ALL_VERSIONS[@]} ]]; then
        echo "${ALL_VERSIONS[$next_idx]}"
    else
        echo "done"
    fi
}

# ============================================================================
# Pre-Flight Checks
# ============================================================================

check_prerequisites() {
    echo ""
    echo -e "${CYAN}+==============================================================+${NC}"
    echo -e "${CYAN}|       CLU Continuous Build -- Pre-Flight Checks              |${NC}"
    echo -e "${CYAN}+==============================================================+${NC}"
    echo ""

    local has_errors=false

    # Check git
    log_step "Checking git..."
    if command -v git &>/dev/null; then
        log_success "Git found"
    else
        log_error "Git not found"
        has_errors=true
    fi

    # Check Claude CLI
    log_step "Checking Claude Code CLI..."
    if command -v claude &>/dev/null; then
        log_success "Claude Code CLI found"
    else
        log_error "Claude Code CLI not found. Install from: https://claude.ai/download"
        has_errors=true
    fi

    # Check CacheBash MCP
    log_step "Checking CacheBash MCP..."
    if claude mcp list 2>/dev/null | grep -q "cachebash"; then
        log_success "CacheBash MCP configured"
    else
        log_warn "CacheBash MCP not configured"
        echo ""
        echo "  To configure CacheBash (recommended for AFK mode):"
        echo -e "  ${CYAN}claude mcp add --transport http cachebash \\${NC}"
        echo -e "  ${CYAN}  \"https://cachebash-mcp-922749444863.us-central1.run.app/v1/mcp\" \\${NC}"
        echo -e "  ${CYAN}  --header \"Authorization: Bearer YOUR_API_KEY\"${NC}"
        echo ""
        if [[ "$AUTO_YES" == "true" ]]; then
            log_info "Auto-accepting: continue without CacheBash (--yes)"
        else
            read -p "  Continue without CacheBash? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi

    # Check we're in basher-repo
    log_step "Checking repository..."
    if [[ -f "$REPO_DIR/scripts/basher.sh" ]]; then
        log_success "In basher-repo: $REPO_DIR"
    else
        log_error "Not in basher-repo. Run from basher-repo/scripts/"
        has_errors=true
    fi

    # Check clean git state
    log_step "Checking git state..."
    cd "$REPO_DIR"
    if [[ -z "$(git status --porcelain)" ]]; then
        log_success "Clean working tree"
    else
        log_warn "Uncommitted changes detected"
        git status --short
        echo ""
        if [[ "$AUTO_YES" == "true" ]]; then
            log_info "Auto-accepting: continue with uncommitted changes (--yes)"
        else
            read -p "  Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi

    # Check ALL prerequisites needed for the full build range
    local to_idx
    to_idx=$(version_index "$TO_VERSION")

    # v0.2+ needs Python, Docker
    if [[ $to_idx -ge 1 ]]; then
        log_step "Checking Python 3.11+ (needed for v0.2+)..."
        if command -v python3 &>/dev/null; then
            local py_version
            py_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
            if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
                log_success "Python $py_version found"
            else
                log_error "Python 3.11+ required, found $py_version"
                has_errors=true
            fi
        else
            log_error "Python 3 not found"
            has_errors=true
        fi

        log_step "Checking Docker..."
        if command -v docker &>/dev/null; then
            log_success "Docker found"
        else
            log_error "Docker not found. Install from: https://docker.com"
            has_errors=true
        fi

        log_step "Checking docker-compose..."
        if command -v docker-compose &>/dev/null || docker compose version &>/dev/null 2>&1; then
            log_success "docker-compose found"
        else
            log_error "docker-compose not found"
            has_errors=true
        fi
    fi

    if [[ "$has_errors" == "true" ]]; then
        echo ""
        log_error "Pre-flight checks failed. Fix errors above and retry."
        exit 1
    fi

    echo ""
    log_success "All pre-flight checks passed!"
}

# ============================================================================
# Branch Setup
# ============================================================================

setup_branch() {
    cd "$REPO_DIR"

    log_step "Setting up branch: $BRANCH_NAME"

    if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME" 2>/dev/null; then
        if [[ "$RESUME" == "true" ]]; then
            git checkout "$BRANCH_NAME"
            log_success "Resumed branch: $BRANCH_NAME"
        else
            log_warn "Branch $BRANCH_NAME already exists"
            if [[ "$AUTO_YES" == "true" ]]; then
                git checkout "$BRANCH_NAME"
                log_info "Auto-resuming branch: $BRANCH_NAME (--yes)"
            else
                echo ""
                echo "  [r] Resume previous build"
                echo "  [f] Start fresh (delete and recreate branch)"
                echo "  [q] Quit"
                echo ""
                read -p "  Choice: " -n 1 -r
                echo
                case "$REPLY" in
                    r|R)
                        git checkout "$BRANCH_NAME"
                        log_success "Resumed branch: $BRANCH_NAME"
                        ;;
                    f|F)
                        git branch -D "$BRANCH_NAME"
                        git checkout -b "$BRANCH_NAME"
                        log_success "Fresh branch created: $BRANCH_NAME"
                        ;;
                    *)
                        exit 0
                        ;;
                esac
            fi
        fi
    else
        git checkout -b "$BRANCH_NAME"
        log_success "Branch created: $BRANCH_NAME"
    fi

    # Set upstream on first push
    if ! git config "branch.$BRANCH_NAME.remote" &>/dev/null; then
        log_step "Will set upstream on first push"
    fi
}

# ============================================================================
# Resume Detection
# ============================================================================

handle_resume() {
    if [[ "$RESUME" != "true" ]]; then
        return
    fi

    local last_completed
    last_completed=$(detect_last_completed)

    if [[ "$last_completed" == "none" ]]; then
        log_info "No previous build detected. Starting from v0.1."
        FROM_VERSION="v0.1"
    elif [[ "$last_completed" == "v1.0" ]]; then
        log_success "All versions already complete!"
        exit 0
    else
        local next
        next=$(next_version "$last_completed")
        log_info "Last completed: $last_completed. Resuming from: $next"
        FROM_VERSION="$next"
    fi
}

# ============================================================================
# Prompt Generation
# ============================================================================

generate_prompt() {
    local version="$1"
    local prompt_file="/tmp/clu-build-${version}.md"

    cat > "$prompt_file" << 'PROMPT_HEADER'
You are building CLU (Codified Likeness Utility) -- a multi-transcript analysis and synthesis engine. You are running in AFK mode: the user is away. Use CacheBash MCP tools to communicate.

## Critical Rules

1. **Commit authorship**: ALL commits use `--author="feelgreatfoodie <feelgreatfoodie@users.noreply.github.com>"`. NEVER add `Co-Authored-By:` lines.
2. **CacheBash communication**: Use `update_status()` for progress. Use `ask_question()` when blocked. NEVER guess -- ask.
3. **Read before writing**: Always read existing files before modifying them. Follow existing patterns.
4. **One commit per logical unit**: Commit after each file group.
5. **Syntax validation**: Run `bash -n` on all `.sh` files before committing.
6. **No over-engineering**: Build exactly what's specified. No extras.
7. **Push after commits**: Run `git push origin clu/full-build` after completing all commits for this version.

PROMPT_HEADER

    # Append version-specific instructions
    case "$version" in
        v0.1)
            cat >> "$prompt_file" << 'V01_PROMPT'
## Version: v0.1 -- "Prove the synthesis"

You are building the CLI skill inside basher-repo. No API, no database. Prompt files + bash scripts only.

## Full Plan Reference

Read the detailed plan file for complete specifications:
```
cat ~/.claude/plans/kind-hugging-creek.md
```

Focus on the "v0.1 Implementation Steps (14 total)" section. That is your build spec.

## Status Updates

```
update_status({ status: "CLU v0.1: Starting build", state: "working", progress: 0 })
```
Update progress after each step (1/14 = 7%, 2/14 = 14%, etc.)

## Summary of What to Build

14 files total: 9 new + 5 updates. Build in this order:

1. `prompts/clu-subagent-extract.md` -- Extraction prompt (read `prompts/subagent-story.md` + `skills/prd/prompt.md` first)
2. `prompts/clu-orchestrator.md` -- Orchestrator prompt (read `prompts/orchestrator.md` first)
3. `skills/clu/prompt.md` -- Main `/clu` skill (read `skills/prd/prompt.md` first)
4. `skills/clu-analyze/prompt.md` -- Analysis-only skill
5. `skills/clu-prd/prompt.md` -- PRD generation skill (read `skills/compose-prd/prompt.md` first)
6. `lib/transcript-utils.sh` -- Bash utilities (read `lib/detect-stack.sh` first)
7. `scripts/clu.sh` -- Execution script (read `scripts/basher.sh` first)
8. `templates/clu.config.json` -- Config template
9. Update `scripts/basher-init.sh` -- Add CLU directories
10. Update `install.sh` -- Copy CLU files
11. Update `scripts/package.sh` -- Include CLU files
12. Update `CLAUDE.md` -- Document CLU
13. Update `README.md` -- Add CLU section
14. `docs/CLU-GUIDE.md` -- User guide + learning module

## Commit Strategy (4 commits)

After ALL 4 commits, push: `git push origin clu/full-build`

1. `feat(clu): add extraction and orchestrator prompts` -- Steps 1-2
2. `feat(clu): add /clu, /clu-analyze, /clu-prd skills` -- Steps 3-5
3. `feat(clu): add execution script and utilities` -- Steps 6-8
4. `feat(clu): integrate CLU into basher ecosystem` -- Steps 9-14

## On Completion

1. Run `bash -n scripts/clu.sh` and `bash -n lib/transcript-utils.sh`
2. Verify `git log --oneline -5` shows 4 clean commits
3. Push: `git push origin clu/full-build`
4. Send: `update_status({ status: "CLU v0.1: Complete! 4 commits, 14 files. Pushed.", state: "complete", progress: 100 })`
V01_PROMPT
            ;;
        v0.2)
            cat >> "$prompt_file" << 'V02_PROMPT'
## Version: v0.2 -- "Open the API"

You are building a FastAPI microservice in `clu-api/` directory within basher-repo.

## Full Plan Reference

Read the detailed plan file for complete specifications:
```
cat ~/.claude/plans/kind-hugging-creek.md
```

Focus on the "v0.2 AFK Build Spec -- FastAPI Microservice" section.

## Status Updates

```
update_status({ status: "CLU v0.2: Starting API build", state: "working", progress: 0 })
```

## Summary of What to Build

Create the `clu-api/` directory with a complete FastAPI microservice:
- FastAPI + SQLAlchemy + PostgreSQL + Anthropic SDK
- Docker + docker-compose for local development
- Alembic for database migrations
- Full REST API for transcript upload, analysis, and results
- pytest test suite
- Reuses same extraction/synthesis prompt logic from v0.1

## Key Technical Decisions

- Use Anthropic SDK directly (NO LangChain)
- PostgreSQL for persistence, background tasks for async processing
- tenant_id on all models from day one (nullable for now)
- Prompts in Python mirror the CLI prompt templates exactly

## Commit Strategy (6 commits)

After ALL 6 commits, push: `git push origin clu/full-build`

1. `feat(clu-api): project scaffolding and Docker setup`
2. `feat(clu-api): database models and migrations`
3. `feat(clu-api): API routes and schemas`
4. `feat(clu-api): extraction and synthesis services`
5. `feat(clu-api): background job processing`
6. `feat(clu-api): tests and documentation`

## On Completion

1. Push: `git push origin clu/full-build`
2. Send: `update_status({ status: "CLU v0.2: Complete! API built. Pushed.", state: "complete", progress: 100 })`
V02_PROMPT
            ;;
        v0.3)
            cat >> "$prompt_file" << 'V03_PROMPT'
## Version: v0.3 -- "Semantic intelligence"

You are adding ChromaDB, Redis, and confidence scoring to the existing clu-api/.

## Full Plan Reference

```
cat ~/.claude/plans/kind-hugging-creek.md
```

Focus on the "v0.3 AFK Build Spec -- Semantic Intelligence" section.

## Summary

- Add ChromaDB for semantic cross-referencing (embed entities, similarity search)
- Add Redis for LLM response caching and job queues
- Add confidence scoring (0.0-1.0) on all extractions
- Update docker-compose.yml with Redis and ChromaDB services
- Update tests

## Commit Strategy (4 commits)

After ALL 4 commits, push: `git push origin clu/full-build`

1. `feat(clu-api): add ChromaDB for semantic cross-referencing`
2. `feat(clu-api): add Redis caching layer`
3. `feat(clu-api): add confidence scoring to extractions`
4. `feat(clu-api): update tests and docs for v0.3`

## On Completion

1. Push: `git push origin clu/full-build`
2. Send: `update_status({ status: "CLU v0.3: Complete! Semantic layer added. Pushed.", state: "complete", progress: 100 })`
V03_PROMPT
            ;;
        v0.4)
            cat >> "$prompt_file" << 'V04_PROMPT'
## Version: v0.4 -- "Production hardening"

You are adding auth, rate limiting, tenant isolation, and GCP deployment to clu-api/.

## Full Plan Reference

```
cat ~/.claude/plans/kind-hugging-creek.md
```

Focus on the "v0.4 AFK Build Spec -- Production Hardening" section.

## Summary

- API key authentication middleware
- Rate limiting (Redis-backed sliding window)
- Tenant isolation (all queries scoped to tenant_id)
- GCP Cloud Run deployment (cloudbuild.yaml)
- Job recovery (resume failed analyses from last checkpoint)
- Structured logging, health checks

## Commit Strategy (5 commits)

After ALL 5 commits, push: `git push origin clu/full-build`

1. `feat(clu-api): add API key authentication`
2. `feat(clu-api): add rate limiting and tenant isolation`
3. `feat(clu-api): add structured logging and health checks`
4. `feat(clu-api): add job recovery for failed analyses`
5. `feat(clu-api): add GCP Cloud Run deployment config`

## On Completion

1. Push: `git push origin clu/full-build`
2. Send: `update_status({ status: "CLU v0.4: Complete! Production-ready. Pushed.", state: "complete", progress: 100 })`
V04_PROMPT
            ;;
        v1.0)
            cat >> "$prompt_file" << 'V10_PROMPT'
## Version: v1.0 -- "Make it useful daily"

You are adding PDF/DOCX support, incremental analysis, CLI wizard, extraction templates, and CacheBash integration.

## Full Plan Reference

```
cat ~/.claude/plans/kind-hugging-creek.md
```

Focus on the "v1.0 AFK Build Spec -- Daily Usability" section.

## Summary

- PDF and DOCX ingestion (PyMuPDF, python-docx)
- Incremental analysis (add new transcripts without re-running everything)
- Interactive CLI conflict resolution wizard (scripts/clu-wizard.sh)
- Configurable extraction templates (default, requirements-only, decisions-only)
- CacheBash mobile integration (push results, resolve conflicts via mobile)
- Full JSON export

## Commit Strategy (5 commits)

After ALL 5 commits, push: `git push origin clu/full-build`

1. `feat(clu): add PDF and DOCX ingestion`
2. `feat(clu): add incremental analysis`
3. `feat(clu): add interactive conflict resolution wizard`
4. `feat(clu): add configurable extraction templates`
5. `feat(clu): v1.0 documentation and CacheBash integration`

## On Completion

1. Push: `git push origin clu/full-build`
2. Send: `update_status({ status: "CLU v1.0: COMPLETE! Full build done. Review clu/full-build branch.", state: "complete", progress: 100 })`
V10_PROMPT
            ;;
        *)
            log_error "Unknown version: $version"
            exit 1
            ;;
    esac

    echo "$prompt_file"
}

# ============================================================================
# Build Loop
# ============================================================================

run_version() {
    local version="$1"
    local version_num
    version_num=$(version_index "$version")
    local from_idx to_idx
    from_idx=$(version_index "$FROM_VERSION")
    to_idx=$(version_index "$TO_VERSION")
    local total_versions=$((to_idx - from_idx + 1))
    local current_num=$((version_num - from_idx + 1))

    echo ""
    echo -e "${CYAN}==============================================================${NC}"
    echo -e "${BOLD}  Building CLU $version ($current_num of $total_versions)${NC}"
    echo -e "${CYAN}==============================================================${NC}"
    echo ""

    # Generate version-specific prompt
    local prompt_file
    prompt_file=$(generate_prompt "$version")
    log_success "Prompt: $prompt_file"

    # Launch Claude session
    log_info "Launching Claude session for $version..."
    cd "$REPO_DIR"
    cat "$prompt_file" | claude -p --dangerously-skip-permissions

    # After session ends, verify commits were made
    local commit_count
    commit_count=$(git log --oneline main..HEAD 2>/dev/null | wc -l | tr -d ' ')
    log_success "$version session ended. Total commits on branch: $commit_count"

    # Push to remote
    log_step "Pushing to remote..."
    if git config "branch.$BRANCH_NAME.remote" &>/dev/null; then
        git push origin "$BRANCH_NAME"
    else
        git push -u origin "$BRANCH_NAME"
    fi
    log_success "Pushed $BRANCH_NAME to remote."
}

run_build_chain() {
    local from_idx to_idx
    from_idx=$(version_index "$FROM_VERSION")
    to_idx=$(version_index "$TO_VERSION")

    echo ""
    echo -e "${CYAN}+==============================================================+${NC}"
    echo -e "${CYAN}|          CLU Continuous Build -- $FROM_VERSION -> $TO_VERSION                    |${NC}"
    echo -e "${CYAN}+==============================================================+${NC}"
    echo ""
    echo -e "  Branch:   ${BOLD}$BRANCH_NAME${NC}"
    echo -e "  Range:    ${BOLD}$FROM_VERSION -> $TO_VERSION${NC}"
    echo -e "  Plan:     ${BOLD}$PLAN_FILE${NC}"
    echo -e "  Repo:     ${BOLD}$REPO_DIR${NC}"
    echo ""

    local version_list=""
    for i in $(seq "$from_idx" "$to_idx"); do
        version_list+="  ${ALL_VERSIONS[$i]}"
    done
    echo -e "  Versions:${BOLD}$version_list${NC}"
    echo ""
    echo "  Each version runs as a fresh Claude session."
    echo "  Commits pushed after each version. No intermediate reviews."
    echo ""
    echo -e "${CYAN}==============================================================${NC}"
    echo ""

    if [[ "$AUTO_YES" == "true" ]]; then
        log_info "Auto-launching build (--yes)"
    else
        read -p "Launch continuous AFK build? (Y/n) " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo ""
            log_info "Build not launched."
            exit 0
        fi
    fi

    echo ""
    log_info "Starting continuous build. Go AFK -- CacheBash will keep you posted."
    echo ""

    # Chain through each version
    for i in $(seq "$from_idx" "$to_idx"); do
        local version="${ALL_VERSIONS[$i]}"
        run_version "$version"

        # Brief pause between versions for git to settle
        if [[ $i -lt $to_idx ]]; then
            log_info "Pausing 5 seconds before next version..."
            sleep 5
        fi
    done

    # Final summary
    echo ""
    echo -e "${GREEN}+==============================================================+${NC}"
    echo -e "${GREEN}|          CLU Build Complete!                                  |${NC}"
    echo -e "${GREEN}+==============================================================+${NC}"
    echo ""
    echo "  Branch: $BRANCH_NAME"
    echo ""
    echo "  Review everything:"
    echo "    git log --oneline main..$BRANCH_NAME"
    echo "    git diff main..$BRANCH_NAME --stat"
    echo ""
    echo "  Create PR:"
    echo "    gh pr create --base main --head $BRANCH_NAME --title \"feat: add CLU transcript analysis engine\""
    echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
    parse_args "$@"
    check_prerequisites
    setup_branch
    handle_resume
    run_build_chain
}

main "$@"
