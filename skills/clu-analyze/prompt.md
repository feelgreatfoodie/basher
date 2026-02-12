# /clu-analyze - Extract & Synthesize (No PRD)

Extract structured data from transcripts and generate cross-reference analysis reports. Same as `/clu` but explicitly excludes PRD generation.

## Usage

```
/clu-analyze                # Analyze transcripts in ./clu/transcripts/
/clu-analyze --dir ./path   # Use custom transcript directory
```

## Prerequisites

Place text files (.txt, .md) in `./clu/transcripts/`.

## What It Does

Runs Phases 1-3 of the CLU pipeline:

1. **Discovery** - Scan transcripts, generate manifest, auto-detect types
2. **Extraction** - Parallel per-transcript extraction via Sonnet subagents
3. **Synthesis** - Cross-reference analysis: consensus, conflicts, gaps, decisions

Explicitly skips Phase 4 (PRD generation). Use `/clu-prd` separately if you want a PRD after reviewing the analysis.

## Process

### Step 1: Load Configuration

Read CLU config, override `prdGeneration` to `false`.

### Step 2: Run the Orchestrator

Read `prompts/clu-orchestrator.md` and execute Phases 1-3 only.

The orchestrator will:
- Generate `manifest.json`
- Spawn extraction subagents (up to 3 concurrent)
- Perform cross-reference synthesis
- Generate all report files

### Step 3: Display Results

```
CLU Analysis Complete (no PRD)

Transcripts: [N] files ([total] words)
Entities extracted: [count]
Conflicts found: [count]
Gaps identified: [count]

Output: ./clu/
  SUMMARY.md | conflicts.md | gaps.md
  decisions.md | requirements.md | stakeholders.md | action-items.md
  analysis.json | extractions/

Next steps:
1. Review and resolve conflicts
2. Define gaps
3. Run /clu-prd when ready to generate a Basher PRD
```

## Output Files

Same as `/clu` minus any PRD output. See `/clu` documentation for full file descriptions.

## When to Use This

- You want to analyze transcripts but aren't ready for a PRD yet
- You want to review and resolve conflicts before generating requirements
- You're using CLU for analysis only (no Basher integration needed)
- You want to run analysis first, then selectively generate PRD with `/clu-prd`
