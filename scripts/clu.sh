#!/usr/bin/env bash
#
# CLU for Claude Code - Multi-Transcript Analysis & Synthesis
#
# Usage: clu.sh [OPTIONS]
#
# Orchestrates Claude Code to extract structured data from transcripts,
# cross-reference across sources, and generate actionable reports.
# Optionally generates a Basher-compatible PRD.
#

set -euo pipefail

# ============================================================================
# Help
# ============================================================================

show_help() {
    cat << 'EOF'
CLU for Claude Code - Multi-Transcript Analysis & Synthesis

Usage: clu.sh [OPTIONS]

Options:
  -h, --help        Show this help message and exit
  --prd             Generate Basher-compatible PRD after analysis
  --dir PATH        Path to transcripts directory (default: ./clu/transcripts)
  --no-mcp-check    Skip CacheBash MCP configuration check

Description:
  CLU (Codified Likeness Utility) ingests multiple text transcripts,
  extracts structured data from each, cross-references across all sources,
  and produces actionable reports.

  Pipeline: Transcripts -> Extract -> Synthesize -> Reports [-> PRD]

Prerequisites:
  - Text files (.txt, .md) in ./clu/transcripts/
  - Claude Code CLI must be installed and authenticated
  - CacheBash MCP server should be configured (for mobile updates)

Output:
  ./clu/SUMMARY.md         Executive summary
  ./clu/conflicts.md       Contradictions needing resolution
  ./clu/gaps.md            Referenced but undefined concepts
  ./clu/decisions.md       Chronological decision log
  ./clu/requirements.md    Consolidated requirements
  ./clu/stakeholders.md    Stakeholder map
  ./clu/action-items.md    Action items with owners
  ./clu/analysis.json      Full structured synthesis
  ./clu/extractions/       Per-document extraction JSONs

Examples:
  clu.sh                   # Analyze transcripts in ./clu/transcripts/
  clu.sh --prd             # Analyze + generate Basher PRD
  clu.sh --dir ~/notes     # Use custom transcript directory
  clu.sh --help            # Show this help message

For more information, see: docs/CLU-GUIDE.md
EOF
    exit 0
}

# ============================================================================
# Configuration
# ============================================================================

BASHER_GLOBAL_DIR="${BASHER_HOME:-$HOME/.basher}"
TRANSCRIPT_DIR="./clu/transcripts"
GENERATE_PRD=false
CHECK_MCP=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================================
# Argument Parsing
# ============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                ;;
            --prd)
                GENERATE_PRD=true
                shift
                ;;
            --dir)
                TRANSCRIPT_DIR="$2"
                shift 2
                ;;
            --no-mcp-check)
                CHECK_MCP=false
                shift
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                ;;
        esac
    done
}

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[clu]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[clu]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[clu]${NC} $1"
}

log_error() {
    echo -e "${RED}[clu]${NC} $1"
}

# Load CLU configuration
load_config() {
    local config_file="./clu/clu.config.json"

    if [[ -f "$config_file" ]]; then
        log_info "Loading config from: $config_file"

        if command -v jq &>/dev/null; then
            local max_concurrent
            max_concurrent=$(jq -r '.clu.maxConcurrent // 3' "$config_file" 2>/dev/null)
            local prd_generation
            prd_generation=$(jq -r '.clu.prdGeneration // false' "$config_file" 2>/dev/null)

            # Config PRD generation can be overridden by --prd flag
            if [[ "$prd_generation" == "true" && "$GENERATE_PRD" == "false" ]]; then
                GENERATE_PRD=true
            fi
        fi
    else
        log_info "No CLU config found, using defaults"
    fi
}

# ============================================================================
# MCP Configuration Check
# ============================================================================

check_mcp_config() {
    if [[ "$CHECK_MCP" != "true" ]]; then
        return 0
    fi

    log_info "Checking CacheBash MCP configuration..."

    if ! command -v claude &>/dev/null; then
        log_error "Claude Code CLI not found. Install it first."
        exit 1
    fi

    if claude mcp list 2>/dev/null | grep -q "cachebash"; then
        log_success "CacheBash MCP server configured"
    else
        log_warn "CacheBash MCP server not configured"
        log_warn "CLU will run without mobile notifications."
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
# Transcript Validation
# ============================================================================

validate_transcripts() {
    log_info "Checking transcripts directory: $TRANSCRIPT_DIR"

    if [[ ! -d "$TRANSCRIPT_DIR" ]]; then
        log_error "Transcripts directory not found: $TRANSCRIPT_DIR"
        log_error "Create it and add your .txt/.md files:"
        log_error "  mkdir -p $TRANSCRIPT_DIR"
        log_error "  cp your-notes.txt $TRANSCRIPT_DIR/"
        exit 1
    fi

    local file_count
    file_count=$(find "$TRANSCRIPT_DIR" -maxdepth 1 \( -name "*.txt" -o -name "*.md" \) -not -name "manifest.json" 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$file_count" -eq 0 ]]; then
        log_error "No .txt or .md files found in $TRANSCRIPT_DIR"
        log_error "Add your transcripts and try again."
        exit 1
    fi

    log_success "Found $file_count transcript(s)"

    # Ensure extractions directory exists
    mkdir -p ./clu/extractions
}

# ============================================================================
# Generate Manifest
# ============================================================================

generate_manifest() {
    local utils_file="$BASHER_GLOBAL_DIR/lib/transcript-utils.sh"

    if [[ -f "$utils_file" ]]; then
        source "$utils_file"
        local manifest
        manifest=$(generate_manifest "$TRANSCRIPT_DIR")
        log_success "Manifest generated: $manifest"
        print_manifest_summary "$manifest"
    elif [[ -f "./lib/transcript-utils.sh" ]]; then
        source "./lib/transcript-utils.sh"
        local manifest
        manifest=$(generate_manifest "$TRANSCRIPT_DIR")
        log_success "Manifest generated: $manifest"
        print_manifest_summary "$manifest"
    else
        log_warn "transcript-utils.sh not found, skipping manifest pre-generation"
        log_info "The orchestrator will generate the manifest during Phase 1"
    fi
}

# ============================================================================
# Claude Execution
# ============================================================================

run_clu() {
    local prompt_file

    # Find orchestrator prompt
    if [[ -f "./prompts/clu-orchestrator.md" ]]; then
        prompt_file="./prompts/clu-orchestrator.md"
    elif [[ -f "$BASHER_GLOBAL_DIR/prompts/clu-orchestrator.md" ]]; then
        prompt_file="$BASHER_GLOBAL_DIR/prompts/clu-orchestrator.md"
    else
        log_error "No clu-orchestrator.md found"
        log_error "Expected at: ./prompts/clu-orchestrator.md or $BASHER_GLOBAL_DIR/prompts/clu-orchestrator.md"
        exit 1
    fi

    log_info "Running CLU orchestrator with:"
    log_info "  Prompt: $prompt_file"
    log_info "  Transcripts: $TRANSCRIPT_DIR"
    log_info "  PRD generation: $GENERATE_PRD"

    # Build Claude command
    local claude_cmd="claude"

    # Orchestrator uses Opus
    claude_cmd="$claude_cmd --model opus"

    # Run Claude with orchestrator prompt piped via stdin
    local output
    output=$(cat "$prompt_file" | $claude_cmd -p --dangerously-skip-permissions 2>&1) || true

    # Check for completion signal
    if echo "$output" | grep -q '<clu>COMPLETE</clu>'; then
        log_success "CLU analysis complete!"
        return 0
    fi

    if echo "$output" | grep -q '<clu>ERROR</clu>'; then
        log_error "CLU encountered an error"
        echo "$output" | grep -A10 '<clu>ERROR</clu>' || true
        return 1
    fi

    return 0
}

# ============================================================================
# Results Summary
# ============================================================================

print_results() {
    echo ""
    echo -e "${GREEN}==============================================================${NC}"
    echo -e "${GREEN}CLU Analysis Complete${NC}"
    echo -e "${GREEN}==============================================================${NC}"
    echo ""

    # Check which files were generated
    local generated=()
    local missing=()

    for file in SUMMARY.md conflicts.md gaps.md decisions.md requirements.md stakeholders.md action-items.md analysis.json; do
        if [[ -f "./clu/$file" ]]; then
            generated+=("$file")
        else
            missing+=("$file")
        fi
    done

    echo "Generated files (${#generated[@]}):"
    for file in "${generated[@]}"; do
        echo "  ./clu/$file"
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo ""
        echo "Missing files (${#missing[@]}):"
        for file in "${missing[@]}"; do
            echo "  ./clu/$file (not generated)"
        done
    fi

    if [[ -d "./clu/extractions" ]]; then
        local extraction_count
        extraction_count=$(find ./clu/extractions -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
        echo ""
        echo "Extractions: $extraction_count files in ./clu/extractions/"
    fi

    if [[ "$GENERATE_PRD" == "true" && -f "./basher/prd.md" ]]; then
        echo ""
        echo "PRD: ./basher/prd.md"
    fi

    echo ""
    echo "Next steps:"
    echo "  1. Review ./clu/SUMMARY.md for key findings"
    echo "  2. Resolve conflicts in ./clu/conflicts.md"
    echo "  3. Define gaps in ./clu/gaps.md"

    if [[ "$GENERATE_PRD" == "true" ]]; then
        echo "  4. Review ./basher/prd.md"
        echo "  5. Run: claude /basher-convert"
        echo "  6. Run: ~/.basher/basher.sh"
    else
        echo "  4. Run: claude /clu-prd  (to generate a Basher PRD)"
    fi

    echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
    parse_args "$@"

    echo ""
    echo -e "${CYAN}+==============================================================+${NC}"
    echo -e "${CYAN}|     CLU - Multi-Transcript Analysis & Synthesis               |${NC}"
    echo -e "${CYAN}+==============================================================+${NC}"
    echo ""

    load_config
    check_mcp_config
    validate_transcripts
    generate_manifest

    echo ""
    log_info "Starting CLU pipeline..."
    echo ""

    run_clu
    local result=$?

    if [[ $result -eq 0 ]]; then
        print_results
    else
        log_error "CLU pipeline failed"
        exit 1
    fi
}

main "$@"
