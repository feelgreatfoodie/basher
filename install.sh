#!/usr/bin/env bash
#
# Basher for Claude Code - Installation Script
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/feelgreatfoodie/basher/main/install.sh | bash
#
#   Or clone the repo and run:
#   ./install.sh
#
# This script installs Basher to ~/.basher/
#

set -euo pipefail

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

BASHER_HOME="${BASHER_HOME:-$HOME/.basher}"

# Detect if we're running from a cloned repo or via curl
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [[ -f "$SCRIPT_DIR/scripts/basher.sh" ]]; then
    SOURCE_DIR="$SCRIPT_DIR"
    INSTALL_MODE="local"
else
    SOURCE_DIR=""
    INSTALL_MODE="remote"
fi

# ============================================================================
# Helper Functions
# ============================================================================

print_banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}║         ${BOLD}Basher for Claude Code${NC}${CYAN} - Installer                  ║${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}║         Autonomous AI Agent Loop for Building Apps           ║${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_step() {
    echo -e "${BLUE}[install]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[install]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[install]${NC} $1"
}

log_error() {
    echo -e "${RED}[install]${NC} $1"
}

# ============================================================================
# Prerequisite Checks
# ============================================================================

check_prerequisites() {
    log_step "Checking prerequisites..."

    local has_errors=false

    # Check for git
    if command -v git &>/dev/null; then
        log_success "Git found: $(git --version)"
    else
        log_error "Git is not installed"
        echo "       Please install git first:"
        echo "       - Mac: xcode-select --install"
        echo "       - Windows: https://git-scm.com/download/win"
        echo "       - Linux: sudo apt install git"
        has_errors=true
    fi

    # Check for Claude CLI
    if command -v claude &>/dev/null; then
        log_success "Claude Code CLI found"
    else
        log_warn "Claude Code CLI not found in PATH"
        echo ""
        echo -e "       ${YELLOW}Basher requires Claude Code CLI to run.${NC}"
        echo "       Install from: https://claude.ai/download"
        echo "       After installing, run: claude auth login"
        echo ""
    fi

    # Check for bash version (need 4+ for associative arrays, but we avoid them)
    local bash_version="${BASH_VERSION%%[^0-9]*}"
    if [[ "$bash_version" -ge 3 ]]; then
        log_success "Bash version: $BASH_VERSION"
    else
        log_warn "Bash version $BASH_VERSION may have compatibility issues"
    fi

    if [[ "$has_errors" == "true" ]]; then
        echo ""
        log_error "Please fix the above errors and run the installer again."
        exit 1
    fi

    echo ""
}

# ============================================================================
# Installation
# ============================================================================

backup_existing() {
    if [[ -d "$BASHER_HOME" ]]; then
        log_step "Found existing installation, creating backup..."
        local backup_dir="$BASHER_HOME.backup-$(date +%Y%m%d-%H%M%S)"
        mv "$BASHER_HOME" "$backup_dir"
        log_success "Backup created at: $backup_dir"
    fi
}

create_directories() {
    log_step "Creating directory structure..."
    mkdir -p "$BASHER_HOME"/{scripts,skills/prd,skills/basher-convert,templates,lib,archive,prompts}
}

install_from_local() {
    log_step "Installing from local repository..."

    # Copy scripts
    cp "$SOURCE_DIR/scripts/basher.sh" "$BASHER_HOME/"
    cp "$SOURCE_DIR/scripts/basher-init.sh" "$BASHER_HOME/"
    cp "$SOURCE_DIR/scripts/package.sh" "$BASHER_HOME/"

    # Copy prompt
    cp "$SOURCE_DIR/prompt.md" "$BASHER_HOME/"

    # Copy prompts (orchestrator and subagent)
    cp "$SOURCE_DIR/prompts/"*.md "$BASHER_HOME/prompts/"

    # Copy lib
    cp "$SOURCE_DIR/lib/detect-stack.sh" "$BASHER_HOME/lib/"

    # Copy skills
    cp "$SOURCE_DIR/skills/prd/prompt.md" "$BASHER_HOME/skills/prd/"
    cp "$SOURCE_DIR/skills/basher-convert/prompt.md" "$BASHER_HOME/skills/basher-convert/"

    # Copy templates
    cp "$SOURCE_DIR/templates/"* "$BASHER_HOME/templates/"

    # Initialize global learnings file if it doesn't exist
    if [[ ! -f "$BASHER_HOME/learnings.md" ]]; then
        cp "$BASHER_HOME/templates/learnings.md" "$BASHER_HOME/learnings.md"
        log_step "Initialized global learnings file"
    fi
}

install_from_remote() {
    log_step "Downloading Basher from GitHub..."

    local BASE_URL="https://raw.githubusercontent.com/feelgreatfoodie/basher/main"

    # Download scripts
    curl -fsSL "$BASE_URL/scripts/basher.sh" -o "$BASHER_HOME/basher.sh"
    curl -fsSL "$BASE_URL/scripts/basher-init.sh" -o "$BASHER_HOME/basher-init.sh"
    curl -fsSL "$BASE_URL/scripts/package.sh" -o "$BASHER_HOME/package.sh"

    # Download prompt
    curl -fsSL "$BASE_URL/prompt.md" -o "$BASHER_HOME/prompt.md"

    # Download prompts (orchestrator and subagent for parallel mode)
    curl -fsSL "$BASE_URL/prompts/orchestrator.md" -o "$BASHER_HOME/prompts/orchestrator.md"
    curl -fsSL "$BASE_URL/prompts/subagent-story.md" -o "$BASHER_HOME/prompts/subagent-story.md"

    # Download lib
    curl -fsSL "$BASE_URL/lib/detect-stack.sh" -o "$BASHER_HOME/lib/detect-stack.sh"

    # Download skills
    curl -fsSL "$BASE_URL/skills/prd/prompt.md" -o "$BASHER_HOME/skills/prd/prompt.md"
    curl -fsSL "$BASE_URL/skills/basher-convert/prompt.md" -o "$BASHER_HOME/skills/basher-convert/prompt.md"

    # Download templates
    curl -fsSL "$BASE_URL/templates/basher.config.json" -o "$BASHER_HOME/templates/basher.config.json"
    curl -fsSL "$BASE_URL/templates/prd.json.example" -o "$BASHER_HOME/templates/prd.json.example"
    curl -fsSL "$BASE_URL/templates/prd.md.example" -o "$BASHER_HOME/templates/prd.md.example"
    curl -fsSL "$BASE_URL/templates/transcript.example.txt" -o "$BASHER_HOME/templates/transcript.example.txt"
    curl -fsSL "$BASE_URL/templates/learnings.md" -o "$BASHER_HOME/templates/learnings.md"

    # Initialize global learnings file if it doesn't exist
    if [[ ! -f "$BASHER_HOME/learnings.md" ]]; then
        cp "$BASHER_HOME/templates/learnings.md" "$BASHER_HOME/learnings.md"
    fi
}

set_permissions() {
    log_step "Setting executable permissions..."
    chmod +x "$BASHER_HOME/basher.sh"
    chmod +x "$BASHER_HOME/basher-init.sh"
    chmod +x "$BASHER_HOME/package.sh"
    chmod +x "$BASHER_HOME/lib/detect-stack.sh"
}

detect_shell() {
    if [[ -n "${ZSH_VERSION:-}" ]] || [[ "$SHELL" == *"zsh"* ]]; then
        echo "zsh"
    elif [[ -n "${BASH_VERSION:-}" ]] || [[ "$SHELL" == *"bash"* ]]; then
        echo "bash"
    else
        echo "unknown"
    fi
}

print_success() {
    local shell_type=$(detect_shell)
    local rc_file=""

    case "$shell_type" in
        zsh)  rc_file="~/.zshrc" ;;
        bash) rc_file="~/.bashrc" ;;
        *)    rc_file="your shell's rc file" ;;
    esac

    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║              Installation Complete! ${NC}                          ${GREEN}║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}Basher is installed at:${NC} $BASHER_HOME"
    echo ""
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}NEXT STEPS${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}1. Add Basher to your PATH${NC} (recommended)"
    echo ""
    echo "   Run this command:"
    echo -e "   ${CYAN}echo 'export PATH=\"\$HOME/.basher:\$PATH\"' >> $rc_file${NC}"
    echo ""
    echo "   Then reload your shell:"
    echo -e "   ${CYAN}source $rc_file${NC}"
    echo ""
    echo -e "${BOLD}2. Verify Claude Code is installed${NC}"
    echo ""
    echo "   Run:"
    echo -e "   ${CYAN}claude --version${NC}"
    echo ""
    echo "   If not installed, get it from: https://claude.ai/download"
    echo ""
    echo -e "${BOLD}3. Initialize Basher in a project${NC}"
    echo ""
    echo "   Navigate to your project and run:"
    echo -e "   ${CYAN}~/.basher/basher-init.sh${NC}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}QUICK START${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "   mkdir my-project && cd my-project"
    echo "   git init"
    echo "   ~/.basher/basher-init.sh"
    echo "   # Edit ./basher/transcript.txt with your feature description"
    echo "   claude   # then type: /prd"
    echo "   # Review ./basher/prd.md"
    echo "   claude   # then type: /basher-convert"
    echo "   ~/.basher/basher.sh"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "For detailed documentation, see: $BASHER_HOME/README.md"
    echo "Or visit: https://github.com/feelgreatfoodie/basher"
    echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
    print_banner
    check_prerequisites
    backup_existing
    create_directories

    if [[ "$INSTALL_MODE" == "local" ]]; then
        install_from_local
    else
        install_from_remote
    fi

    set_permissions
    print_success
}

main "$@"
