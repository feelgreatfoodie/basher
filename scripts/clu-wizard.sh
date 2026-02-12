#!/usr/bin/env bash
#
# CLU Conflict Resolution Wizard
#
# Interactive CLI for resolving conflicts found by CLU analysis.
# Reads analysis.json, presents each conflict, saves resolutions,
# and regenerates the conflicts.md report.
#
# Usage: clu-wizard.sh [OPTIONS]
#
#   --dir PATH    Path to CLU output directory (default: ./clu)
#   -h, --help    Show this help
#

set -euo pipefail

# ============================================================================
# Help
# ============================================================================

show_help() {
    cat << 'EOF'
CLU Conflict Resolution Wizard

Interactive CLI for resolving conflicts found by CLU analysis.

Usage: clu-wizard.sh [OPTIONS]

Options:
  --dir PATH    Path to CLU output directory (default: ./clu)
  -h, --help    Show this help

Description:
  Reads analysis.json, presents each conflict interactively, and lets you:
  - Accept Position A or Position B
  - Enter a custom resolution
  - Defer to Open Questions

  Resolutions are saved back to analysis.json and conflicts.md is regenerated.

Examples:
  clu-wizard.sh                  # Resolve conflicts in ./clu/
  clu-wizard.sh --dir ~/project/clu  # Custom CLU directory

EOF
    exit 0
}

# ============================================================================
# Configuration
# ============================================================================

CLU_DIR="./clu"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ============================================================================
# Argument Parsing
# ============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dir)
                CLU_DIR="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                ;;
        esac
    done
}

# ============================================================================
# JSON Helpers (using python3 for reliable JSON manipulation)
# ============================================================================

# Get the number of conflicts in analysis.json
get_conflict_count() {
    python3 -c "
import json, sys
with open('${CLU_DIR}/analysis.json') as f:
    data = json.load(f)
conflicts = data.get('conflicts', [])
print(len(conflicts))
"
}

# Get a specific conflict field as JSON
get_conflict() {
    local index="$1"
    python3 -c "
import json, sys
with open('${CLU_DIR}/analysis.json') as f:
    data = json.load(f)
conflicts = data.get('conflicts', [])
if $index < len(conflicts):
    print(json.dumps(conflicts[$index], indent=2))
else:
    print('{}')
"
}

# Get a specific field from a conflict
get_conflict_field() {
    local index="$1"
    local field="$2"
    python3 -c "
import json
with open('${CLU_DIR}/analysis.json') as f:
    data = json.load(f)
conflicts = data.get('conflicts', [])
if $index < len(conflicts):
    val = conflicts[$index].get('$field', '')
    if isinstance(val, list):
        print(json.dumps(val))
    else:
        print(val)
"
}

# Save a resolution to analysis.json
save_resolution() {
    local index="$1"
    local resolution="$2"
    local chosen="$3"
    python3 -c "
import json
with open('${CLU_DIR}/analysis.json') as f:
    data = json.load(f)
conflicts = data.get('conflicts', [])
if $index < len(conflicts):
    conflicts[$index]['resolution'] = '''$resolution'''
    conflicts[$index]['resolvedAs'] = '''$chosen'''
    conflicts[$index]['status'] = 'resolved'
data['conflicts'] = conflicts
with open('${CLU_DIR}/analysis.json', 'w') as f:
    json.dump(data, f, indent=2)
"
}

# Regenerate conflicts.md from analysis.json
regenerate_conflicts_md() {
    python3 << 'PYEOF'
import json

CLU_DIR = "${CLU_DIR}"

with open(f"{CLU_DIR}/analysis.json") as f:
    data = json.load(f)

conflicts = data.get("conflicts", [])

with open(f"{CLU_DIR}/conflicts.md", "w") as f:
    f.write("# Conflicts Requiring Resolution\n\n")

    resolved = [c for c in conflicts if c.get("status") == "resolved"]
    unresolved = [c for c in conflicts if c.get("status") != "resolved"]

    if not conflicts:
        f.write("No conflicts found.\n")
        return

    f.write(f"**Total:** {len(conflicts)} conflicts ")
    f.write(f"({len(resolved)} resolved, {len(unresolved)} unresolved)\n\n")
    f.write("---\n\n")

    for i, conflict in enumerate(conflicts, 1):
        topic = conflict.get("topic", f"Conflict {i}")
        status = conflict.get("status", "unresolved")

        if status == "resolved":
            f.write(f"## ~~CONFLICT {i}: {topic}~~ (RESOLVED)\n\n")
            f.write(f"**Resolution:** {conflict.get('resolution', 'N/A')}\n\n")
        else:
            f.write(f"## CONFLICT {i}: {topic}\n\n")

        positions = conflict.get("positions", [])
        for pos in positions:
            label = pos.get("label", "Position")
            sources = pos.get("sources", [])
            f.write(f"**{label}** ({len(sources)} source(s)):\n")
            for src in sources:
                quote = src.get("quote", "")
                speaker = src.get("speaker", "Unknown")
                source_file = src.get("source", "Unknown")
                f.write(f'> "{quote}" -- {speaker} ({source_file})\n\n')

        if conflict.get("suggestedResolution"):
            f.write(f"**Suggested Resolution:** {conflict['suggestedResolution']}\n")

        if conflict.get("impact"):
            f.write(f"**Impact:** {conflict['impact']}\n")

        f.write("\n---\n\n")

print(f"Regenerated {CLU_DIR}/conflicts.md ({len(resolved)} resolved, {len(unresolved)} unresolved)")
PYEOF
}

# ============================================================================
# Display Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}+==============================================================+${NC}"
    echo -e "${CYAN}|        CLU Conflict Resolution Wizard                         |${NC}"
    echo -e "${CYAN}+==============================================================+${NC}"
    echo ""
}

print_conflict() {
    local index="$1"
    local total="$2"
    local conflict_json
    conflict_json=$(get_conflict "$index")

    local topic
    topic=$(echo "$conflict_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('topic','Unknown'))")

    local status
    status=$(echo "$conflict_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','unresolved'))")

    echo ""
    echo -e "${BOLD}CONFLICT $((index + 1)) of $total: ${topic}${NC}"

    if [[ "$status" == "resolved" ]]; then
        local resolution
        resolution=$(echo "$conflict_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('resolution','N/A'))")
        echo -e "${GREEN}  [RESOLVED] $resolution${NC}"
        return 1  # Signal: already resolved
    fi

    echo ""

    # Print positions
    echo "$conflict_json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
positions = data.get('positions', [])
for i, pos in enumerate(positions):
    label = pos.get('label', f'Position {chr(65+i)}')
    sources = pos.get('sources', [])
    print(f'  {label} ({len(sources)} source(s)):')
    for src in sources:
        quote = src.get('quote', '')
        speaker = src.get('speaker', 'Unknown')
        source_file = src.get('source', 'Unknown')
        print(f'    > \"{quote}\"')
        print(f'      -- {speaker} ({source_file})')
    print()
"

    local suggested
    suggested=$(echo "$conflict_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('suggestedResolution',''))")
    if [[ -n "$suggested" ]]; then
        echo -e "  ${DIM}Suggested: $suggested${NC}"
        echo ""
    fi

    return 0  # Signal: needs resolution
}

# ============================================================================
# Resolution Loop
# ============================================================================

resolve_conflict() {
    local index="$1"
    local conflict_json
    conflict_json=$(get_conflict "$index")

    # Count positions
    local pos_count
    pos_count=$(echo "$conflict_json" | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('positions',[])))")

    # Build option letters
    local options=""
    for ((i=0; i<pos_count; i++)); do
        local letter
        letter=$(printf "\\$(printf '%03o' $((65 + i)))")
        local label
        label=$(echo "$conflict_json" | python3 -c "import json,sys; d=json.load(sys.stdin); pos=d.get('positions',[]); print(pos[$i].get('label','Position $letter') if $i < len(pos) else 'Position $letter')")
        echo -e "  ${BOLD}[$letter]${NC} Accept: $label"
        options+="$letter"
    done
    echo -e "  ${BOLD}[c]${NC} Custom resolution"
    echo -e "  ${BOLD}[d]${NC} Defer to Open Questions"
    echo -e "  ${BOLD}[s]${NC} Skip (leave unresolved)"
    echo ""

    read -p "  Choice: " -n 1 -r choice
    echo ""

    local lower_choice
    lower_choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]')

    # Check if it's a position letter
    local pos_index=-1
    for ((i=0; i<pos_count; i++)); do
        local letter
        letter=$(printf "\\$(printf '%03o' $((97 + i)))")
        if [[ "$lower_choice" == "$letter" ]]; then
            pos_index=$i
            break
        fi
    done

    if [[ $pos_index -ge 0 ]]; then
        local label
        label=$(echo "$conflict_json" | python3 -c "import json,sys; d=json.load(sys.stdin); pos=d.get('positions',[]); print(pos[$pos_index].get('label','Position') if $pos_index < len(pos) else 'Position')")
        save_resolution "$index" "Accepted: $label" "position_$pos_index"
        echo -e "  ${GREEN}Resolved: Accepted $label${NC}"
    elif [[ "$lower_choice" == "c" ]]; then
        echo ""
        read -p "  Enter custom resolution: " -r custom
        if [[ -n "$custom" ]]; then
            save_resolution "$index" "$custom" "custom"
            echo -e "  ${GREEN}Resolved: $custom${NC}"
        else
            echo -e "  ${YELLOW}Skipped (empty input)${NC}"
        fi
    elif [[ "$lower_choice" == "d" ]]; then
        save_resolution "$index" "Deferred to Open Questions" "deferred"
        echo -e "  ${YELLOW}Deferred to Open Questions${NC}"
    elif [[ "$lower_choice" == "s" ]]; then
        echo -e "  ${DIM}Skipped${NC}"
    else
        echo -e "  ${RED}Invalid choice, skipping${NC}"
    fi
}

# ============================================================================
# Main
# ============================================================================

main() {
    parse_args "$@"

    # Validate CLU directory
    if [[ ! -f "$CLU_DIR/analysis.json" ]]; then
        echo -e "${RED}Error: $CLU_DIR/analysis.json not found${NC}"
        echo "Run CLU analysis first: claude /clu-analyze"
        exit 1
    fi

    print_header

    local total
    total=$(get_conflict_count)

    if [[ "$total" -eq 0 ]]; then
        echo -e "${GREEN}No conflicts found in analysis. Nothing to resolve.${NC}"
        exit 0
    fi

    echo -e "  Found ${BOLD}$total${NC} conflict(s) in $CLU_DIR/analysis.json"
    echo ""

    local resolved=0
    local skipped=0

    for ((i=0; i<total; i++)); do
        if print_conflict "$i" "$total"; then
            resolve_conflict "$i"
            if [[ "$(get_conflict_field "$i" "status")" == "resolved" ]]; then
                resolved=$((resolved + 1))
            else
                skipped=$((skipped + 1))
            fi
        else
            echo ""  # Already resolved — skip
        fi
    done

    # Regenerate conflicts.md
    echo ""
    echo -e "${BLUE}Regenerating conflicts.md...${NC}"
    regenerate_conflicts_md

    # Summary
    echo ""
    echo -e "${GREEN}==============================================================${NC}"
    echo -e "${GREEN}Wizard Complete${NC}"
    echo -e "${GREEN}==============================================================${NC}"
    echo ""
    echo "  Total conflicts: $total"
    echo "  Resolved this session: $resolved"
    echo "  Skipped: $skipped"
    echo ""
    echo "  Updated: $CLU_DIR/analysis.json"
    echo "  Updated: $CLU_DIR/conflicts.md"
    echo ""

    local remaining
    remaining=$(python3 -c "
import json
with open('${CLU_DIR}/analysis.json') as f:
    data = json.load(f)
unresolved = [c for c in data.get('conflicts', []) if c.get('status') != 'resolved']
print(len(unresolved))
")

    if [[ "$remaining" -eq 0 ]]; then
        echo -e "  ${GREEN}All conflicts resolved!${NC}"
        echo "  Next: claude /clu-prd  (generate PRD from resolved analysis)"
    else
        echo -e "  ${YELLOW}$remaining conflict(s) still unresolved${NC}"
        echo "  Re-run: clu-wizard.sh  (to resolve remaining)"
    fi
    echo ""
}

main "$@"
