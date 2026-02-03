#!/usr/bin/env bash
#
# Basher Package - Create a portable Basher installation
#
# Usage: package.sh [output-file]
#
# Creates a tarball that can be shared with colleagues.
# Does NOT include any credentials or API keys.
#

set -euo pipefail

BASHER_HOME="${BASHER_HOME:-$HOME/.basher}"
OUTPUT_FILE="${1:-basher-portable.tar.gz}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          Basher Portable Package Creator                     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Copy Basher files (excluding archives and any sensitive data)
echo -e "${BLUE}[package]${NC} Collecting Basher files..."
mkdir -p "$TEMP_DIR/.basher"

# Copy core files
cp "$BASHER_HOME/basher.sh" "$TEMP_DIR/.basher/"
cp "$BASHER_HOME/basher-init.sh" "$TEMP_DIR/.basher/"
cp "$BASHER_HOME/prompt.md" "$TEMP_DIR/.basher/"
cp "$BASHER_HOME/install.sh" "$TEMP_DIR/.basher/"
cp "$BASHER_HOME/README.md" "$TEMP_DIR/.basher/"
cp "$BASHER_HOME/package.sh" "$TEMP_DIR/.basher/"

# Copy lib
cp -r "$BASHER_HOME/lib" "$TEMP_DIR/.basher/"

# Copy skills
cp -r "$BASHER_HOME/skills" "$TEMP_DIR/.basher/"

# Copy templates
cp -r "$BASHER_HOME/templates" "$TEMP_DIR/.basher/"

# Create empty archive directory
mkdir -p "$TEMP_DIR/.basher/archive"

# Create installation instructions
cat > "$TEMP_DIR/INSTALL.txt" << 'EOF'
Basher for Claude Code - Installation Instructions
================================================

1. Extract to home directory:
   tar -xzf basher-portable.tar.gz -C ~/

2. Make scripts executable (should already be set):
   chmod +x ~/.basher/*.sh ~/.basher/lib/*.sh

3. (Optional) Add to PATH:
   echo 'export PATH="$HOME/.basher:$PATH"' >> ~/.zshrc
   echo 'alias basher="~/.basher/basher.sh"' >> ~/.zshrc
   source ~/.zshrc

4. Install Claude Code CLI (if not already installed):
   Visit: https://docs.anthropic.com/claude-code

5. Authenticate Claude Code:
   claude auth login

6. Initialize Basher in your project:
   cd your-project
   ~/.basher/basher-init.sh

You're ready to go! See ~/.basher/README.md for full documentation.
EOF

# Create tarball
echo -e "${BLUE}[package]${NC} Creating tarball..."
cd "$TEMP_DIR"
tar -czf "$OUTPUT_FILE" .basher INSTALL.txt

# Move to original directory
mv "$OUTPUT_FILE" "$OLDPWD/"
cd "$OLDPWD"

# Get file size
SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Package created: $OUTPUT_FILE ($SIZE)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Share this file with colleagues. They need to:"
echo "  1. Extract: tar -xzf $OUTPUT_FILE -C ~/"
echo "  2. Install Claude Code CLI"
echo "  3. Authenticate with their own credentials"
echo ""
echo "See INSTALL.txt in the package for detailed instructions."
echo ""
