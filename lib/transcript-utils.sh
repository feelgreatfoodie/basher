#!/usr/bin/env bash
#
# CLU Transcript Utilities
#
# Shared bash functions for transcript processing.
# Can be sourced or run directly for testing.
#
# Usage:
#   source transcript-utils.sh
#   generate_manifest /path/to/transcripts
#
# Outputs (as environment variables):
#   TRANSCRIPT_COUNT  - Number of transcripts found
#   TOTAL_WORDS       - Total word count across all transcripts
#   MANIFEST_FILE     - Path to generated manifest.json
#

# ============================================================================
# Word Counting
# ============================================================================

# Count words in a file
# Usage: count_words /path/to/file.txt
count_words() {
    local file="$1"
    if [[ -f "$file" ]]; then
        wc -w < "$file" | tr -d ' '
    else
        echo "0"
    fi
}

# ============================================================================
# Type Detection
# ============================================================================

# Detect transcript type from content and filename
# Usage: detect_transcript_type /path/to/file.txt
# Returns: meeting|interview|slack|spec|other
detect_transcript_type() {
    local file="$1"
    local filename
    filename=$(basename "$file")
    local content_sample

    # Read first 200 lines for detection
    content_sample=$(head -200 "$file" 2>/dev/null || true)

    # Check filename hints first
    case "$filename" in
        *meeting*|*standup*|*retro*|*sync*|*huddle*)
            echo "meeting"; return ;;
        *interview*|*user-research*|*stakeholder*)
            echo "interview"; return ;;
        *slack*|*discord*|*chat*|*thread*)
            echo "slack"; return ;;
        *spec*|*rfc*|*prd*|*requirement*|*design-doc*)
            echo "spec"; return ;;
    esac

    # Check content patterns
    # Meeting: multiple speakers with colon format (e.g., "Alice: We should...")
    local speaker_lines
    speaker_lines=$(echo "$content_sample" | grep -cE '^[A-Z][a-zA-Z ]+:' 2>/dev/null || echo "0")
    if [[ "$speaker_lines" -gt 5 ]]; then
        echo "meeting"; return
    fi

    # Interview: Q&A format or interviewer/interviewee labels
    if echo "$content_sample" | grep -qiE '(interviewer|interviewee|Q:|A:|question:|answer:)' 2>/dev/null; then
        echo "interview"; return
    fi

    # Slack: timestamps + short messages, @mentions
    local slack_patterns
    slack_patterns=$(echo "$content_sample" | grep -cE '(\d{1,2}:\d{2}|@[a-zA-Z]+|#[a-z-]+)' 2>/dev/null || echo "0")
    if [[ "$slack_patterns" -gt 5 ]]; then
        echo "slack"; return
    fi

    # Spec: formal sections, numbered requirements
    local spec_patterns
    spec_patterns=$(echo "$content_sample" | grep -cE '(^#{1,3} |^[0-9]+\.|Requirements?:|Specification|RFC|shall |must )' 2>/dev/null || echo "0")
    if [[ "$spec_patterns" -gt 3 ]]; then
        echo "spec"; return
    fi

    echo "other"
}

# ============================================================================
# Transcript Directory Validation
# ============================================================================

# Validate that a transcripts directory exists and contains files
# Usage: validate_transcripts_dir /path/to/transcripts
# Returns: 0 if valid, 1 if not
validate_transcripts_dir() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        echo "Error: Transcripts directory not found: $dir" >&2
        return 1
    fi

    local file_count
    file_count=$(find "$dir" -maxdepth 1 \( -name "*.txt" -o -name "*.md" -o -name "*.pdf" -o -name "*.docx" \) -not -name "manifest.json" 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$file_count" -eq 0 ]]; then
        echo "Error: No supported files found in $dir" >&2
        echo "Supported formats: .txt, .md, .pdf, .docx" >&2
        echo "Place your transcripts in $dir and try again." >&2
        return 1
    fi

    echo "$file_count"
    return 0
}

# ============================================================================
# Manifest Generation
# ============================================================================

# Generate manifest.json from transcript files
# Usage: generate_manifest /path/to/transcripts
generate_manifest() {
    local dir="$1"
    local manifest_file="$dir/manifest.json"

    # Validate directory
    local file_count
    file_count=$(validate_transcripts_dir "$dir") || return 1

    local total_words=0
    local entries=""
    local first=true

    # Process each transcript file
    while IFS= read -r file; do
        local name
        name=$(basename "$file")
        local words
        words=$(count_words "$file")
        local type
        type=$(detect_transcript_type "$file")

        # Determine model based on word count
        local model="sonnet"
        if [[ "$words" -ge 50000 ]]; then
            model="opus"
        fi

        total_words=$((total_words + words))

        # Build JSON entry
        if [[ "$first" == "true" ]]; then
            first=false
        else
            entries+=","
        fi

        entries+="
    {
      \"name\": \"$name\",
      \"type\": \"$type\",
      \"wordCount\": $words,
      \"model\": \"$model\"
    }"

    done < <(find "$dir" -maxdepth 1 \( -name "*.txt" -o -name "*.md" -o -name "*.pdf" -o -name "*.docx" \) -not -name "manifest.json" | sort)

    # Write manifest
    cat > "$manifest_file" << EOF
{
  "generatedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "totalFiles": $file_count,
  "totalWords": $total_words,
  "transcripts": [$entries
  ]
}
EOF

    # Set output variables
    TRANSCRIPT_COUNT="$file_count"
    TOTAL_WORDS="$total_words"
    MANIFEST_FILE="$manifest_file"

    echo "$manifest_file"
}

# ============================================================================
# Output Helpers
# ============================================================================

# Print manifest summary
# Usage: print_manifest_summary /path/to/manifest.json
print_manifest_summary() {
    local manifest="$1"

    if [[ ! -f "$manifest" ]]; then
        echo "No manifest found at: $manifest" >&2
        return 1
    fi

    echo "Transcript Manifest"
    echo "==================="

    if command -v jq &>/dev/null; then
        local total_files total_words
        total_files=$(jq -r '.totalFiles' "$manifest")
        total_words=$(jq -r '.totalWords' "$manifest")
        echo "Files: $total_files"
        echo "Total words: $total_words"
        echo ""
        echo "Transcripts:"
        jq -r '.transcripts[] | "  \(.name) (\(.type), \(.wordCount) words, \(.model))"' "$manifest"
    else
        echo "  (install jq for formatted output)"
        cat "$manifest"
    fi
}

# ============================================================================
# Direct Execution
# ============================================================================

# Run manifest generation if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    dir="${1:-.}"

    if [[ "$dir" == "--help" || "$dir" == "-h" ]]; then
        echo "Usage: transcript-utils.sh [transcripts-directory]"
        echo ""
        echo "Generate a manifest.json for transcript files in the given directory."
        echo "Defaults to current directory if no path provided."
        exit 0
    fi

    manifest=$(generate_manifest "$dir") || exit 1
    echo ""
    print_manifest_summary "$manifest"
fi
