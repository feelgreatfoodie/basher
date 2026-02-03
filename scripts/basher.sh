#!/usr/bin/env bash
#
# Basher for Claude Code - Autonomous AI Agent Loop
#
# Usage: basher.sh [OPTIONS] [max_iterations]
#
# This script orchestrates Claude Code CLI invocations to complete
# all user stories in a PRD. Supports both sequential (one story at a time)
# and parallel (orchestrator with subagents) modes.
#

set -euo pipefail

# ============================================================================
# Help
# ============================================================================

show_help() {
    cat << 'EOF'
Basher for Claude Code - Autonomous AI Agent Loop

Usage: basher.sh [OPTIONS] [max_iterations]

Arguments:
  max_iterations    Maximum number of iterations before stopping (default: 20)

Options:
  -h, --help        Show this help message and exit
  --parallel        Run in parallel mode (orchestrator + subagents)
  --sequential      Run in sequential mode (one story at a time, default)
  --no-mcp-check    Skip CacheBash MCP configuration check

Description:
  This script orchestrates Claude Code CLI invocations to complete
  all user stories in a PRD.

  Sequential mode: Each iteration implements one story, then exits.
  Parallel mode: Orchestrator analyzes dependencies and spawns subagents.

Prerequisites:
  - prd.json must exist in ./basher/ or ~/.basher/
  - Claude Code CLI must be installed and authenticated
  - Must be run from within a git repository
  - CacheBash MCP server should be configured (for status updates)

Examples:
  basher.sh              # Run sequentially with default 20 iterations
  basher.sh --parallel   # Run with orchestrator and parallel subagents
  basher.sh 50           # Run with up to 50 iterations
  basher.sh --help       # Show this help message

For more information, see: https://github.com/feelgreatfoodie/basher
EOF
    exit 0
}

# ============================================================================
# Configuration
# ============================================================================

BASHER_GLOBAL_DIR="${BASHER_HOME:-$HOME/.basher}"
BASHER_LOCAL_DIR="./basher"
MAX_ITERATIONS="${1:-20}"
DELAY_SECONDS=2
EXECUTION_MODE="sequential"  # or "parallel"
CHECK_MCP=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Argument Parsing
# ============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                ;;
            --parallel)
                EXECUTION_MODE="parallel"
                shift
                ;;
            --sequential)
                EXECUTION_MODE="sequential"
                shift
                ;;
            --no-mcp-check)
                CHECK_MCP=false
                shift
                ;;
            *)
                if [[ "$1" =~ ^[0-9]+$ ]]; then
                    MAX_ITERATIONS="$1"
                fi
                shift
                ;;
        esac
    done
}

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[basher]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[basher]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[basher]${NC} $1"
}

log_error() {
    echo -e "${RED}[basher]${NC} $1"
}

log_iteration() {
    echo -e "${CYAN}[basher]${NC} ══════════════════════════════════════════════════════════"
    echo -e "${CYAN}[basher]${NC} ITERATION $1 / $MAX_ITERATIONS"
    echo -e "${CYAN}[basher]${NC} ══════════════════════════════════════════════════════════"
}

# Find a file, preferring local over global
find_file() {
    local filename="$1"
    if [[ -f "$BASHER_LOCAL_DIR/$filename" ]]; then
        echo "$BASHER_LOCAL_DIR/$filename"
    elif [[ -f "$BASHER_GLOBAL_DIR/$filename" ]]; then
        echo "$BASHER_GLOBAL_DIR/$filename"
    else
        echo ""
    fi
}

# Extract JSON value using jq if available, otherwise fall back to grep/sed
json_get() {
    local file="$1"
    local jq_path="$2"
    local grep_pattern="$3"
    local default="$4"

    if command -v jq &>/dev/null; then
        local value
        value=$(jq -r "$jq_path // empty" "$file" 2>/dev/null)
        if [[ -n "$value" && "$value" != "null" ]]; then
            echo "$value"
            return
        fi
    else
        local value
        value=$(grep -o "$grep_pattern" "$file" 2>/dev/null | head -1 | sed 's/.*: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/' || true)
        if [[ -n "$value" ]]; then
            echo "$value"
            return
        fi
    fi
    echo "$default"
}

# Load configuration with local override
load_config() {
    local config_file
    config_file=$(find_file "basher.config.json")

    if [[ -n "$config_file" ]]; then
        log_info "Loading config from: $config_file"

        GIT_STRATEGY=$(json_get "$config_file" '.git.strategy' '"strategy"[[:space:]]*:[[:space:]]*"[^"]*"' "single-branch")
        GIT_BASE_BRANCH=$(json_get "$config_file" '.git.baseBranch' '"baseBranch"[[:space:]]*:[[:space:]]*"[^"]*"' "main")
        GIT_BRANCH_PREFIX=$(json_get "$config_file" '.git.branchPrefix' '"branchPrefix"[[:space:]]*:[[:space:]]*"[^"]*"' "basher/")
        MAX_ITERATIONS_CONFIG=$(json_get "$config_file" '.iterations.max' '"max"[[:space:]]*:[[:space:]]*[0-9]*' "")
        DELAY_CONFIG=$(json_get "$config_file" '.iterations.delaySeconds' '"delaySeconds"[[:space:]]*:[[:space:]]*[0-9]*' "")
        # Hybrid model config: separate models for orchestrator and subagents
        ORCHESTRATOR_MODEL=$(json_get "$config_file" '.claude.orchestratorModel' '"orchestratorModel"[[:space:]]*:[[:space:]]*"[^"]*"' "opus")
        SUBAGENT_MODEL=$(json_get "$config_file" '.claude.subagentModel' '"subagentModel"[[:space:]]*:[[:space:]]*"[^"]*"' "sonnet")
        COMPLEX_STORY_MODEL=$(json_get "$config_file" '.claude.complexStoryModel' '"complexStoryModel"[[:space:]]*:[[:space:]]*"[^"]*"' "opus")
        REVIEW_WITH_ORCHESTRATOR=$(json_get "$config_file" '.claude.reviewWithOrchestrator' '"reviewWithOrchestrator"[[:space:]]*:[[:space:]]*true' "true")
        # Legacy fallback for single model config
        CLAUDE_MODEL=$(json_get "$config_file" '.claude.model' '"model"[[:space:]]*:[[:space:]]*"[^"]*"' "")

        # New config options
        PARALLEL_ENABLED=$(json_get "$config_file" '.parallel.enabled' '"enabled"[[:space:]]*:[[:space:]]*true' "false")
        MAX_CONCURRENT=$(json_get "$config_file" '.parallel.maxConcurrent' '"maxConcurrent"[[:space:]]*:[[:space:]]*[0-9]*' "3")
        CACHEBASH_ENABLED=$(json_get "$config_file" '.cachebash.enabled' '"enabled"[[:space:]]*:[[:space:]]*true' "true")
        INTERRUPT_POLL_SECONDS=$(json_get "$config_file" '.cachebash.interruptPollSeconds' '"interruptPollSeconds"[[:space:]]*:[[:space:]]*[0-9]*' "120")

        # Apply config values
        [[ -n "$MAX_ITERATIONS_CONFIG" ]] && MAX_ITERATIONS="$MAX_ITERATIONS_CONFIG"
        [[ -n "$DELAY_CONFIG" ]] && DELAY_SECONDS="$DELAY_CONFIG"

        # Use parallel mode if enabled in config and not overridden by CLI
        if [[ "$PARALLEL_ENABLED" == "true" && "$EXECUTION_MODE" == "sequential" ]]; then
            EXECUTION_MODE="parallel"
        fi
    else
        log_warn "No config file found, using defaults"
        GIT_STRATEGY="single-branch"
        GIT_BASE_BRANCH="main"
        GIT_BRANCH_PREFIX="basher/"
        ORCHESTRATOR_MODEL="opus"
        SUBAGENT_MODEL="sonnet"
        COMPLEX_STORY_MODEL="opus"
        REVIEW_WITH_ORCHESTRATOR="true"
        CLAUDE_MODEL=""
        CACHEBASH_ENABLED="true"
        INTERRUPT_POLL_SECONDS="120"
    fi
}

# ============================================================================
# MCP Configuration Check
# ============================================================================

check_mcp_config() {
    if [[ "$CHECK_MCP" != "true" ]]; then
        return 0
    fi

    if [[ "$CACHEBASH_ENABLED" != "true" ]]; then
        log_info "CacheBash disabled in config, skipping MCP check"
        return 0
    fi

    log_info "Checking CacheBash MCP configuration..."

    if ! command -v claude &>/dev/null; then
        log_error "Claude Code CLI not found. Install it first."
        exit 1
    fi

    # Check if cachebash MCP server is configured
    if claude mcp list 2>/dev/null | grep -q "cachebash"; then
        log_success "CacheBash MCP server configured"
    else
        log_warn "CacheBash MCP server not configured"
        log_warn "Basher will run without mobile notifications."
        log_warn ""
        log_warn "To enable CacheBash:"
        log_warn "  1. Get API key from CacheBash app -> Settings"
        log_warn "  2. Run: claude mcp add --transport http cachebash \\"
        log_warn "       \"https://cachebash-mcp-922749444863.us-central1.run.app/v1/mcp\" \\"
        log_warn "       --header \"Authorization: Bearer YOUR_API_KEY\""
        log_warn ""
        log_warn "Use --no-mcp-check to suppress this warning."
        echo ""
        read -p "Continue without CacheBash? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# ============================================================================
# PRD Management
# ============================================================================

get_prd_file() {
    local prd_file
    prd_file=$(find_file "prd.json")

    if [[ -z "$prd_file" ]]; then
        log_error "No prd.json found in $BASHER_LOCAL_DIR or $BASHER_GLOBAL_DIR"
        log_error "Run 'claude /prd' to generate a PRD first"
        exit 1
    fi

    echo "$prd_file"
}

get_branch_name() {
    local prd_file="$1"
    grep -o '"branchName"[[:space:]]*:[[:space:]]*"[^"]*"' "$prd_file" | sed 's/.*: *"\([^"]*\)"/\1/' || echo "basher/feature"
}

get_incomplete_count() {
    local prd_file="$1"
    if command -v jq &>/dev/null; then
        jq '[.userStories[] | select(.passes != true)] | length' "$prd_file" 2>/dev/null || echo "0"
    else
        grep -c '"passes"[[:space:]]*:[[:space:]]*false' "$prd_file" 2>/dev/null || echo "0"
    fi
}

check_all_complete() {
    local prd_file="$1"
    local incomplete
    incomplete=$(get_incomplete_count "$prd_file")
    [[ "$incomplete" -eq 0 ]]
}

# ============================================================================
# Git Management
# ============================================================================

setup_git_branch() {
    local branch_name="$1"

    if ! git rev-parse --is-inside-work-tree &>/dev/null; then
        log_error "Not in a git repository"
        exit 1
    fi

    local current_branch
    current_branch=$(git branch --show-current)

    if [[ "$current_branch" != "$branch_name" ]]; then
        if git show-ref --verify --quiet "refs/heads/$branch_name"; then
            log_info "Switching to existing branch: $branch_name"
            git checkout "$branch_name"
        else
            log_info "Creating new branch: $branch_name from $GIT_BASE_BRANCH"
            git checkout -b "$branch_name" "$GIT_BASE_BRANCH"
        fi
    else
        log_info "Already on branch: $branch_name"
    fi
}

# ============================================================================
# Archive Management
# ============================================================================

archive_previous_run() {
    local prd_file="$1"
    local last_branch_file="$BASHER_LOCAL_DIR/.last-branch"
    local current_branch
    current_branch=$(get_branch_name "$prd_file")

    mkdir -p "$BASHER_LOCAL_DIR"

    if [[ -f "$last_branch_file" ]]; then
        local last_branch
        last_branch=$(cat "$last_branch_file")

        if [[ "$last_branch" != "$current_branch" ]]; then
            local archive_name
            archive_name=$(echo "$last_branch" | sed 's|^basher/||')
            archive_name="${archive_name}-$(date +%Y%m%d-%H%M%S)"

            log_info "Archiving previous run: $archive_name"
            mkdir -p "$BASHER_LOCAL_DIR/archive/$archive_name"

            [[ -f "$BASHER_LOCAL_DIR/progress.txt" ]] && mv "$BASHER_LOCAL_DIR/progress.txt" "$BASHER_LOCAL_DIR/archive/$archive_name/"
            [[ -f "$BASHER_LOCAL_DIR/prd.json" ]] && cp "$BASHER_LOCAL_DIR/prd.json" "$BASHER_LOCAL_DIR/archive/$archive_name/"

            echo "# Progress Log - $current_branch" > "$BASHER_LOCAL_DIR/progress.txt"
            echo "Started: $(date)" >> "$BASHER_LOCAL_DIR/progress.txt"
            echo "" >> "$BASHER_LOCAL_DIR/progress.txt"
        fi
    fi

    echo "$current_branch" > "$last_branch_file"
}

# ============================================================================
# Progress Management
# ============================================================================

init_progress_file() {
    local progress_file="$BASHER_LOCAL_DIR/progress.txt"

    if [[ ! -f "$progress_file" ]]; then
        mkdir -p "$BASHER_LOCAL_DIR"
        cat > "$progress_file" << 'EOF'
# Progress Log

This file accumulates learnings across Basher iterations.
Each iteration should append discoveries, patterns, and gotchas here.

## Codebase Patterns
<!-- Reusable patterns discovered during implementation -->

## Iteration Log
EOF
        log_info "Initialized progress.txt"
    fi
}

# ============================================================================
# Signal Handling
# ============================================================================

cleanup() {
    log_warn "Received interrupt signal, cleaning up..."
    # Kill any background Claude processes
    pkill -P $$ 2>/dev/null || true
    exit 130
}

trap cleanup SIGINT SIGTERM

# ============================================================================
# Claude Execution - Sequential Mode
# ============================================================================

run_claude_sequential() {
    local iteration="$1"
    local prompt_file
    local prd_file

    prompt_file=$(find_file "prompt.md")
    prd_file=$(get_prd_file)

    if [[ -z "$prompt_file" ]]; then
        log_error "No prompt.md found"
        exit 1
    fi

    # Use legacy model if set, otherwise orchestrator model (sequential uses same model throughout)
    local model_to_use="${CLAUDE_MODEL:-$ORCHESTRATOR_MODEL}"

    log_info "Running Claude (sequential mode) with:"
    log_info "  Prompt: $prompt_file"
    log_info "  PRD: $prd_file"
    log_info "  Model: $model_to_use"

    local claude_cmd="claude"

    if [[ "$model_to_use" == "opus" ]]; then
        claude_cmd="$claude_cmd --model claude-opus-4-5-20251101"
    fi

    # Run Claude with prompt file (no --print to allow MCP tools)
    local output
    output=$($claude_cmd --prompt-file "$prompt_file" --dangerously-skip-permissions 2>&1) || true

    # Check for completion signals
    if echo "$output" | grep -q '<basher>COMPLETE</basher>'; then
        log_success "All stories completed!"
        return 0
    fi

    if echo "$output" | grep -q '<basher>ITERATION_COMPLETE</basher>'; then
        log_success "Iteration $iteration completed successfully"
        return 1
    fi

    if echo "$output" | grep -q '<basher>ERROR</basher>'; then
        log_error "Iteration encountered an error"
        echo "$output" | grep -A10 '<basher>ERROR</basher>' || true
        return 2
    fi

    return 1
}

# ============================================================================
# Claude Execution - Parallel Mode (Orchestrator)
# ============================================================================

run_claude_parallel() {
    local prompt_file
    local prd_file

    # Use orchestrator prompt for parallel mode
    prompt_file=$(find_file "prompts/orchestrator.md")
    if [[ -z "$prompt_file" ]]; then
        prompt_file="$BASHER_GLOBAL_DIR/prompts/orchestrator.md"
    fi

    prd_file=$(get_prd_file)

    if [[ -z "$prompt_file" || ! -f "$prompt_file" ]]; then
        log_error "No orchestrator.md found for parallel mode"
        log_error "Expected at: ./basher/prompts/orchestrator.md or $BASHER_GLOBAL_DIR/prompts/orchestrator.md"
        exit 1
    fi

    # Orchestrator always uses orchestrator model (defaults to opus)
    local orchestrator_model="${CLAUDE_MODEL:-$ORCHESTRATOR_MODEL}"

    log_info "Running Claude (parallel/orchestrator mode) with:"
    log_info "  Prompt: $prompt_file"
    log_info "  PRD: $prd_file"
    log_info "  Orchestrator model: $orchestrator_model"
    log_info "  Subagent model: $SUBAGENT_MODEL"
    log_info "  Complex story model: $COMPLEX_STORY_MODEL"
    log_info "  Max concurrent: $MAX_CONCURRENT"

    local claude_cmd="claude"

    if [[ "$orchestrator_model" == "opus" ]]; then
        claude_cmd="$claude_cmd --model claude-opus-4-5-20251101"
    fi

    # Run Claude orchestrator (single run, it manages iterations internally)
    local output
    output=$($claude_cmd --prompt-file "$prompt_file" --dangerously-skip-permissions 2>&1) || true

    if echo "$output" | grep -q '<basher>COMPLETE</basher>'; then
        log_success "All stories completed!"
        return 0
    fi

    if echo "$output" | grep -q '<basher>ERROR</basher>'; then
        log_error "Orchestrator encountered an error"
        echo "$output" | grep -A10 '<basher>ERROR</basher>' || true
        return 2
    fi

    return 0
}

# ============================================================================
# Main Loop
# ============================================================================

main() {
    parse_args "$@"

    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          Basher for Claude Code - Autonomous Agent Loop      ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    load_config

    log_info "Execution mode: $EXECUTION_MODE"

    # Check MCP configuration
    check_mcp_config

    local prd_file
    prd_file=$(get_prd_file)
    log_info "Using PRD: $prd_file"

    archive_previous_run "$prd_file"
    init_progress_file

    local branch_name
    branch_name=$(get_branch_name "$prd_file")
    setup_git_branch "$branch_name"

    if check_all_complete "$prd_file"; then
        log_success "All stories are already complete!"
        exit 0
    fi

    local incomplete
    incomplete=$(get_incomplete_count "$prd_file")
    log_info "Stories remaining: $incomplete"

    # Run in appropriate mode
    if [[ "$EXECUTION_MODE" == "parallel" ]]; then
        # Parallel mode: orchestrator manages everything in one run
        run_claude_parallel
        local result=$?

        if [[ $result -eq 0 ]]; then
            log_success "══════════════════════════════════════════════════════════"
            log_success "BASHER COMPLETE - All stories implemented!"
            log_success "══════════════════════════════════════════════════════════"
            exit 0
        else
            log_error "Orchestrator stopped with errors"
            exit 1
        fi
    else
        # Sequential mode: iteration loop
        local iteration=1
        while [[ $iteration -le $MAX_ITERATIONS ]]; do
            log_iteration "$iteration"

            local result
            run_claude_sequential "$iteration" && result=$? || result=$?

            case $result in
                0)
                    log_success "══════════════════════════════════════════════════════════"
                    log_success "BASHER COMPLETE - All stories implemented!"
                    log_success "══════════════════════════════════════════════════════════"
                    exit 0
                    ;;
                1)
                    ;;
                2)
                    log_error "Stopping due to error in iteration $iteration"
                    exit 1
                    ;;
            esac

            if check_all_complete "$prd_file"; then
                log_success "══════════════════════════════════════════════════════════"
                log_success "BASHER COMPLETE - All stories implemented!"
                log_success "══════════════════════════════════════════════════════════"
                exit 0
            fi

            log_info "Waiting ${DELAY_SECONDS}s before next iteration..."
            sleep "$DELAY_SECONDS"

            ((iteration++))
        done

        log_warn "══════════════════════════════════════════════════════════"
        log_warn "MAX ITERATIONS REACHED ($MAX_ITERATIONS)"
        incomplete=$(get_incomplete_count "$prd_file")
        log_warn "Stories remaining: $incomplete"
        log_warn "══════════════════════════════════════════════════════════"
        exit 1
    fi
}

main "$@"
