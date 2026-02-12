# /clu - Multi-Transcript Analysis & Synthesis

End-to-end transcript analysis: extract structured data from each transcript, cross-reference across all sources, generate actionable reports, and optionally produce a Basher-compatible PRD.

## Usage

```
/clu                    # Analyze transcripts, generate reports
/clu --prd              # Analyze + generate Basher PRD
/clu --dir ./path       # Use custom transcript directory
```

## Prerequisites

Place text files (.txt, .md) in `./clu/transcripts/`:

```
./clu/transcripts/
├── meeting-kickoff.txt
├── architecture-review.md
├── stakeholder-interview.txt
└── slack-thread.txt
```

## What It Does

### Phase 1: Discovery
- Scans `./clu/transcripts/` for text files
- Auto-detects transcript type (meeting, interview, slack, spec)
- Generates `manifest.json` with metadata
- Pauses for your review (or proceeds after 2 min)

### Phase 2: Extraction (Parallel)
- Spawns Sonnet subagents (up to 3 concurrent) to extract structured data from each transcript
- Large files (>50K words) use Opus instead
- Extracts: participants, decisions, action items, requirements, constraints, open questions, risks, deferred items
- Saves per-transcript JSONs to `./clu/extractions/`

### Phase 3: Synthesis
- Opus orchestrator reads all extraction JSONs
- Cross-references: consensus ranking, conflict detection, decision tracking, stakeholder dedup, gap analysis
- Generates report files in `./clu/`

### Phase 4: PRD Generation (with --prd flag)
- Transforms analysis into Basher-compatible `./basher/prd.md`
- Consensus requirements become prioritized user stories
- Conflicts become Open Questions
- Ready for `/basher-convert`

## Output Files

| File | Contents | Priority |
|------|----------|----------|
| `SUMMARY.md` | Executive summary, key findings, statistics | Act on this |
| `conflicts.md` | Contradictions with both positions + source citations | Act on this |
| `gaps.md` | Referenced but undefined concepts | Act on this |
| `decisions.md` | Chronological decision log with confirmation status | Verified consensus |
| `requirements.md` | Consolidated requirements ranked by consensus | Verified consensus |
| `stakeholders.md` | Who cares about what, decision authority | Verified consensus |
| `action-items.md` | Action items with owners, sources, status | Verified consensus |
| `analysis.json` | Full structured synthesis (machine-readable) | Reference |
| `extractions/` | Per-document raw extraction JSONs | Reference |

## Process

### Step 1: Load Configuration

Read CLU config from `./clu/clu.config.json` (if exists) or use defaults:
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

### Step 2: Run the Orchestrator

Read and execute the orchestrator prompt:
```
Read prompts/clu-orchestrator.md
```

The orchestrator manages the full pipeline:
1. Discovery & manifest generation
2. Parallel extraction via subagents
3. Cross-reference synthesis
4. Report generation
5. (Optional) PRD generation

### Step 3: User Review Checkpoints

The orchestrator pauses at defined checkpoints:

| Checkpoint | When | You Can... |
|------------|------|------------|
| Manifest | After discovery | Exclude files, correct metadata |
| Extractions | After Phase 2 | Review/correct per-transcript extractions |
| Analysis | After Phase 3 | Resolve conflicts, edit reports |
| PRD | After Phase 4 | Edit stories before `/basher-convert` |

### Step 4: Summary

After completion, display:

```
CLU Analysis Complete!

Transcripts: [N] files ([total] words)
Entities extracted: [count]
Conflicts found: [count] (see conflicts.md)
Gaps identified: [count] (see gaps.md)

Output: ./clu/

Level 1 (Act on this):
  - SUMMARY.md
  - conflicts.md
  - gaps.md

Level 2 (Verified consensus):
  - decisions.md
  - requirements.md
  - stakeholders.md
  - action-items.md

Level 3 (Reference):
  - analysis.json
  - extractions/

Next steps:
1. Review conflicts.md and resolve contradictions
2. Review gaps.md and define missing concepts
3. Review requirements.md for prioritization
4. (Optional) Run /clu-prd to generate a Basher PRD
```

## Full Pipeline

```
Transcripts -> /clu (analysis) -> /clu-prd (PRD) -> /basher-convert (JSON) -> basher.sh (build)
```

## Configuration

Override defaults in `./clu/clu.config.json`:

| Option | Default | Description |
|--------|---------|-------------|
| `maxConcurrent` | 3 | Max parallel extraction subagents |
| `extractorModel` | sonnet | Model for extraction (sonnet/opus) |
| `synthesizerModel` | opus | Model for synthesis |
| `autoManifest` | true | Auto-generate manifest without pausing |
| `prdGeneration` | false | Generate PRD after analysis |
| `conflictHandling` | open-questions | How to handle conflicts in PRD: open-questions, strongest-consensus, ask-user |
