# Basher for Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude-Code-blueviolet)](https://claude.ai)

> **Build complete applications autonomously using AI — from meeting notes to working code.**

Basher is an automation system that runs Claude Code (Anthropic's AI coding assistant) repeatedly to implement entire software projects without manual intervention. You describe what you want to build, and Basher handles the rest.

---

## TL;DR

```bash
# 1. Install
curl -fsSL https://raw.githubusercontent.com/feelgreatfoodie/basher/main/install.sh | bash

# 2. Initialize in your project
cd my-project && git init
~/.basher/basher-init.sh

# 3. Describe what you want (edit ./basher/transcript.txt)

# 4. Generate PRD and convert
claude            # Start Claude Code
/prd              # Generate requirements
/basher-convert   # Convert to tasks

# 5. Run!
~/.basher/basher.sh
```

That's it. Basher builds your app while you grab coffee.

---

## Table of Contents

1. [TL;DR](#tldr)
2. [What is Basher?](#what-is-basher)
3. [How It Works](#how-it-works)
4. [Prerequisites](#prerequisites)
5. [Installation](#installation)
6. [Quick Start Guide](#quick-start-guide)
7. [Detailed Walkthrough](#detailed-walkthrough)
8. [Configuration Options](#configuration-options)
9. [CacheBash Integration](#cachebash-integration-optional)
10. [Sharing with Teammates](#sharing-with-teammates)
11. [Troubleshooting](#troubleshooting)
12. [FAQ](#faq)
13. [Contributing](#contributing)

---

## What is Basher?

Imagine you have a meeting where your team discusses a new feature. Someone takes notes. Normally, a developer would then spend hours or days turning those notes into working code.

**Basher changes this.**

With Basher, you:
1. Paste your meeting notes into a file
2. Run a few commands
3. Walk away while Basher builds your application

Basher breaks your project into small, manageable tasks and completes them one by one — writing code, running tests, fixing errors, and committing changes to git. Each task is done with a fresh perspective, preventing the AI from getting confused or making compounding mistakes.

### Key Benefits

- **Autonomous**: Runs without supervision until complete
- **Quality-focused**: Automatically runs linting, type checking, and tests
- **Knowledge-preserving**: Documents learnings for future iterations
- **Portable**: Easy to share with teammates
- **Iterative**: You can review, adjust, and re-run at any time

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   📝 Meeting Notes / Feature Description                        │
│                                                                 │
│   "We need a task manager with CRUD operations..."              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   📋 PRD Generation (claude /prd)                               │
│                                                                 │
│   Transforms notes into structured requirements                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   🔄 JSON Conversion (claude /basher-convert)                   │
│                                                                 │
│   Creates machine-readable task list                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   🤖 Autonomous Execution (basher.sh)                           │
│                                                                 │
│   For each task:                                                │
│   ├── Start fresh Claude instance                               │
│   ├── Read current state from files                             │
│   ├── Implement one task                                        │
│   ├── Run quality checks (lint, test, build)                    │
│   ├── Commit changes to git                                     │
│   ├── Document learnings                                        │
│   └── Mark task complete                                        │
│                                                                 │
│   Repeat until all tasks are done!                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ✅ Complete Application                                        │
│                                                                 │
│   All code written, tested, and committed                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### The Secret: Fresh Context

The key innovation is that **each task runs with fresh context**.

When you use AI tools manually for a long time, they can get confused — mixing up old code with new, forgetting what was changed, or making the same mistake repeatedly.

Basher avoids this by:
- Starting a completely new Claude instance for each task
- Forcing all important information to be written to files
- Letting each instance read the current state fresh

This means task #10 is just as accurate as task #1.

---

## Prerequisites

Before installing Basher, you'll need a few things set up on your computer.

### 1. Claude Code CLI

Claude Code is Anthropic's command-line AI coding assistant. Basher uses it to do the actual coding work.

**Installation:**
1. Visit [claude.ai/download](https://claude.ai/download) or the official documentation
2. Download and install Claude Code for your operating system
3. Open your terminal and run: `claude --version`
4. If you see a version number, you're good!

**Authentication:**
```bash
claude auth login
```
Follow the prompts to log in with your Anthropic account.

### 2. Git

Git tracks changes to your code. Basher uses it to save progress after each task.

**Check if installed:**
```bash
git --version
```

**If not installed:**
- **Mac**: Install Xcode Command Line Tools: `xcode-select --install`
- **Windows**: Download from [git-scm.com](https://git-scm.com/download/win)
- **Linux**: `sudo apt install git` (Ubuntu/Debian) or `sudo yum install git` (CentOS/RHEL)

### 3. A Terminal

You'll run commands in a terminal application:
- **Mac**: Terminal (built-in) or iTerm2
- **Windows**: PowerShell, Command Prompt, or Windows Terminal
- **Linux**: Your default terminal

### 4. A Text Editor (Optional but Helpful)

For reviewing and editing files:
- [VS Code](https://code.visualstudio.com/) (free, recommended)
- Any text editor you're comfortable with

---

## Installation

### Option A: One-Line Install (Recommended)

Open your terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/feelgreatfoodie/basher/main/install.sh | bash
```

This downloads and sets up Basher automatically.

### Option B: Manual Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/feelgreatfoodie/basher.git
   cd basher
   ```

2. **Run the installer:**
   ```bash
   ./install.sh
   ```

3. **Add Basher to your PATH** (so you can run it from anywhere):

   For **Zsh** (default on Mac):
   ```bash
   echo 'export PATH="$HOME/.basher:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

   For **Bash**:
   ```bash
   echo 'export PATH="$HOME/.basher:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

4. **Verify installation:**
   ```bash
   ls ~/.basher
   ```
   You should see files like `basher.sh`, `prompt.md`, etc.

---

## Quick Start Guide

Here's the fastest way to get Basher running on a new project:

### Step 1: Create or Navigate to Your Project

```bash
# Create a new project folder
mkdir my-awesome-app
cd my-awesome-app

# Initialize git (required)
git init
```

### Step 2: Initialize Basher

```bash
~/.basher/basher-init.sh
```

This creates a `./basher/` folder in your project with configuration files.

### Step 3: Add Your Feature Description

Open `./basher/transcript.txt` in your text editor and replace the placeholder with your feature description or meeting notes.

**Example:**
```
We need to build a simple task manager API.

Features:
- Create tasks with a title and description
- List all tasks
- Mark tasks as complete
- Delete tasks

Technical requirements:
- Use Node.js and Express
- Store data in memory (no database for now)
- Include basic input validation
```

### Step 4: Generate the PRD

In your terminal, start Claude Code:
```bash
claude
```

Then type:
```
/prd
```

Claude will read your notes and generate a structured Product Requirements Document at `./basher/prd.md`. Review it to make sure it captured your intent.

### Step 5: Convert to JSON

Still in Claude Code, type:
```
/basher-convert
```

This creates `./basher/prd.json` — the machine-readable task list that Basher will execute.

### Step 6: Run Basher!

Exit Claude Code (type `exit` or press Ctrl+C), then run:

```bash
~/.basher/basher.sh
```

**That's it!** Basher will now work through each task autonomously. You can watch the progress in your terminal, or come back later to see the finished result.

---

## Detailed Walkthrough

Let's walk through a complete example from start to finish.

### Scenario: Building a Task Manager API

You had a meeting with your team, and someone wrote down these notes:

```
Meeting Notes - Task Manager App
================================

Alice: We need a simple API for managing tasks.

Bob: Yeah, basic CRUD - create, read, update, delete.

Alice: Each task should have a title, description, and status.

Bob: Status should be like... todo, in-progress, done?

Alice: Perfect. Let's use Node.js since that's what we know.

Bob: Should we add a database?

Alice: Not yet. Let's start with in-memory storage and add a
database later. Keep it simple.

Bob: What about tests?

Alice: Yes, we need tests. Can't ship without them.
```

### Step-by-Step Execution

#### 1. Set Up the Project

```bash
# Create project folder
mkdir task-manager-api
cd task-manager-api

# Initialize git
git init

# Initialize Basher
~/.basher/basher-init.sh
```

Output:
```
╔══════════════════════════════════════════════════════════════╗
║            Basher Init - Project Setup                       ║
╚══════════════════════════════════════════════════════════════╝

[init] Creating ./basher directory...
[init] Creating configuration...
[init] Creating progress.txt...
[init] Creating transcript placeholder...
[init] Detecting tech stack...
[init] Could not auto-detect tech stack

════════════════════════════════════════════════════════════════
Basher initialized for: task-manager-api
════════════════════════════════════════════════════════════════
```

#### 2. Add Meeting Notes

Open `./basher/transcript.txt` and paste in your meeting notes (the ones above).

#### 3. Generate PRD

```bash
claude
```

Inside Claude Code:
```
/prd
```

Claude reads your transcript and creates `./basher/prd.md`:

```markdown
# Task Manager API - Product Requirements Document

## Overview
A simple REST API for managing tasks, supporting CRUD operations
with in-memory storage.

## User Stories

### US-001: Initialize Node.js project
**Priority:** 1 (Critical)
...

### US-002: Create task data model
**Priority:** 1 (Critical)
...
```

#### 4. Review the PRD

Open `./basher/prd.md` and review it. Make sure:
- All features are captured
- Stories are in the right order (dependencies first)
- Nothing important is missing

Edit if needed!

#### 5. Convert to JSON

In Claude Code:
```
/basher-convert
```

This creates `./basher/prd.json`. You'll see a summary:

```
PRD converted to JSON: ./basher/prd.json

Project: task-manager-api
Branch: basher/task-manager-api
Stories: 7 total (0 completed)

Story Summary:
  [P1] US-001: Initialize Node.js project
  [P1] US-002: Create task data model
  [P2] US-003: Add create task endpoint
  [P2] US-004: Add list tasks endpoint
  [P2] US-005: Add update task endpoint
  [P3] US-006: Add delete task endpoint
  [P3] US-007: Add test suite
```

#### 6. Exit Claude and Run Basher

```bash
exit  # or Ctrl+C to leave Claude Code
~/.basher/basher.sh
```

Output:
```
╔══════════════════════════════════════════════════════════════╗
║          Basher for Claude Code - Autonomous Agent Loop      ║
╚══════════════════════════════════════════════════════════════╝

[basher] Using PRD: ./basher/prd.json
[basher] Initialized progress.txt
[basher] Creating new branch: basher/task-manager-api from main
[basher] Stories remaining: 7

[basher] ══════════════════════════════════════════════════════════
[basher] ITERATION 1 / 20
[basher] ══════════════════════════════════════════════════════════
[basher] Running Claude iteration...
```

Basher will now:
1. Pick the first task (US-001)
2. Implement it
3. Run quality checks
4. Commit the changes
5. Mark it complete
6. Move to the next task

This continues until all tasks are done!

#### 7. Check the Results

When Basher finishes:
```
[basher] ══════════════════════════════════════════════════════════
[basher] BASHER COMPLETE - All stories implemented!
[basher] ══════════════════════════════════════════════════════════
```

Your project now has:
- Working code in the appropriate files
- Git commits for each task
- A complete API ready to test

```bash
# See what was created
ls -la

# See the git history
git log --oneline

# Run the application (example for Node.js)
npm start
```

---

## Configuration Options

Basher's behavior can be customized through `./basher/basher.config.json`.

### Full Configuration Reference

```json
{
  "project": "my-project",

  "git": {
    "strategy": "single-branch",
    "baseBranch": "main",
    "branchPrefix": "basher/"
  },

  "quality": {
    "autoDetect": true,
    "commands": {
      "lint": null,
      "typecheck": null,
      "test": null,
      "build": null
    }
  },

  "iterations": {
    "max": 20,
    "delaySeconds": 2
  },

  "claude": {
    "model": "sonnet"
  }
}
```

### Configuration Explained

#### Project Name
```json
"project": "my-project"
```
The name of your project. Used for branch names and logging.

#### Git Settings

```json
"git": {
  "strategy": "single-branch",
  "baseBranch": "main",
  "branchPrefix": "basher/"
}
```

- **strategy**: How Basher handles git branches
  - `"single-branch"`: All tasks on one branch (recommended)
  - `"branch-per-story"`: Each task gets its own branch

- **baseBranch**: The branch to create the Basher branch from (usually `main` or `master`)

- **branchPrefix**: Prefix for Basher's branch names (e.g., `basher/my-feature`)

#### Quality Gates

```json
"quality": {
  "autoDetect": true,
  "commands": {
    "lint": null,
    "typecheck": null,
    "test": null,
    "build": null
  }
}
```

- **autoDetect**: If `true`, Basher will automatically detect your project type and use appropriate commands

- **commands**: Override specific commands (set to `null` for auto-detection):
  ```json
  "commands": {
    "lint": "npm run lint:fix",
    "typecheck": "npm run typecheck",
    "test": "npm test",
    "build": "npm run build"
  }
  ```

#### Iteration Settings

```json
"iterations": {
  "max": 20,
  "delaySeconds": 2
}
```

- **max**: Maximum number of iterations before Basher stops (safety limit)
- **delaySeconds**: Pause between iterations (helps with rate limits)

#### Claude Settings

```json
"claude": {
  "model": "sonnet"
}
```

- **model**: Which Claude model to use
  - `"sonnet"`: Faster, cheaper (recommended for most tasks)
  - `"opus"`: More capable, use for complex tasks

### Tech Stack Auto-Detection

Basher automatically detects your project type and configures quality commands:

| Project Type | Detection | Lint | Typecheck | Test | Build |
|-------------|-----------|------|-----------|------|-------|
| Node.js/TypeScript | `package.json` | `npm run lint` | `npx tsc --noEmit` | `npm test` | `npm run build` |
| Python | `pyproject.toml` | `ruff check .` | `mypy .` | `pytest` | - |
| Rust | `Cargo.toml` | `cargo clippy` | `cargo check` | `cargo test` | `cargo build` |
| Go | `go.mod` | `golangci-lint run` | `go vet ./...` | `go test ./...` | `go build ./...` |

---

## CacheBash Integration (Optional)

Basher can optionally integrate with [CacheBash](https://github.com/feelgreatfoodie/cachebash), a mobile companion app that lets you monitor and interact with Basher from your phone.

### What is CacheBash?

CacheBash is a mobile app that:
- Shows real-time progress of your Basher runs
- Sends push notifications when Basher needs input
- Lets you answer questions and make decisions from anywhere
- Allows you to send course corrections mid-run

### What You'll See on Mobile

When Basher runs with CacheBash enabled:

| Event | Mobile Notification |
|-------|---------------------|
| Story starts | Status update: "Basher: 2/7 US-002 Adding login" |
| Need decision | Push: "Need clarification: REST or GraphQL?" |
| Error occurs | Push (high priority): "Build failed, how to proceed?" |
| Sprint complete | Push: "All stories done! Anything to add?" |

### Setting Up CacheBash

1. **Install the CacheBash mobile app** (iOS/Android)
   - Download from your app store or build from source

2. **Get your API key**
   - Open CacheBash app → Settings → Copy API Key

3. **Add CacheBash MCP server to Claude Code**
   ```bash
   claude mcp add --transport http cachebash \
     "https://cachebash-mcp-922749444863.us-central1.run.app/v1/mcp" \
     --header "Authorization: Bearer YOUR_API_KEY"
   ```

4. **Restart Claude Code**
   ```bash
   claude  # MCP servers load at startup
   ```

5. **Verify connection**
   ```bash
   claude mcp list
   # Should show: cachebash: ... (HTTP) - ✓ Connected
   ```

### Configuration

CacheBash is enabled by default in `basher.config.json`:

```json
{
  "cachebash": {
    "enabled": true,
    "pollIntervalSeconds": 30,
    "sessionId": "optional-session-id"
  }
}
```

| Option | Description |
|--------|-------------|
| `enabled` | Turn CacheBash integration on/off |
| `pollIntervalSeconds` | How often to check for responses (default: 30) |
| `sessionId` | Optional fixed session ID for tracking across runs |

### Responding to Questions

When Basher asks a question:

1. You'll receive a push notification on your phone
2. Open the CacheBash app
3. Select an option or type a custom response
4. Basher receives your answer and continues

### Sending Course Corrections

To change direction mid-run:

1. Open the CacheBash app
2. Find your active session
3. Send an interrupt message:
   - "pause" or "stop" - Pauses Basher
   - "skip US-XXX" - Skips a specific story
   - Any other message - Treated as guidance

### Running Without CacheBash

If you don't want mobile integration:

1. Set `"enabled": false` in `basher.config.json`
2. Basher will run without mobile notifications
3. Any blocking questions will cause Basher to pause until you check the terminal

---

## Sharing with Teammates

Basher is designed to be easily shared. Here's how to get your teammates set up.

### Creating a Portable Package

Run this command to create a shareable file:

```bash
~/.basher/package.sh
```

This creates `basher-portable.tar.gz` — a single file containing everything needed.

### Teammate Installation

Send the `basher-portable.tar.gz` file to your teammate. They should:

1. **Extract the package:**
   ```bash
   tar -xzf basher-portable.tar.gz -C ~/
   ```

2. **Install Claude Code CLI** (if they haven't already):
   - Download from the official Anthropic website
   - Run `claude auth login` with their own account

3. **Add to PATH:**
   ```bash
   echo 'export PATH="$HOME/.basher:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

4. **Verify:**
   ```bash
   ~/.basher/basher.sh --help
   ```

**Important:** Each person needs their own Claude Code credentials. Basher doesn't store or share API keys.

### Version Control for Basher Itself

Since Basher is just files, you can version control it:

```bash
cd ~/.basher
git init
git add .
git commit -m "Initial Basher setup"
git remote add origin git@github.com:your-org/basher-config.git
git push -u origin main
```

Now teammates can clone your organization's Basher configuration:

```bash
git clone git@github.com:your-org/basher-config.git ~/.basher
```

---

## Troubleshooting

### "claude: command not found"

**Problem:** The Claude Code CLI isn't installed or isn't in your PATH.

**Solution:**
1. Install Claude Code from [the official website](https://claude.ai/download)
2. Restart your terminal
3. Try again: `claude --version`

### "Not in a git repository"

**Problem:** Basher requires git to track changes.

**Solution:**
```bash
git init
git add .
git commit -m "Initial commit"
```

### Basher stops after a few iterations

**Problem:** A task might be failing repeatedly.

**Solution:**
1. Check `./basher/progress.txt` for error messages
2. Look at the last few git commits: `git log --oneline -5`
3. The task might be too large — edit `./basher/prd.json` to split it

### "Max iterations reached"

**Problem:** Basher hit the safety limit without completing all tasks.

**Solution:**
1. Check how many tasks remain: look at `./basher/prd.json`
2. Increase the limit: `~/.basher/basher.sh 50`
3. Or investigate why tasks aren't completing (check `progress.txt`)

### Tests keep failing

**Problem:** Quality gates are blocking progress.

**Solution:**
1. Check what's failing: run the test command manually
2. The AI might have introduced a bug — review recent commits
3. You may need to fix something manually, then resume

### Context window exceeded

**Problem:** A task is too complex for a single Claude session.

**Solution:**
Split the task into smaller pieces in `./basher/prd.json`:
- Instead of "Build user authentication"
- Use: "Create user model", "Add login endpoint", "Add registration endpoint", etc.

### How to Resume After Fixing Something

If you need to manually fix code and continue:

1. Make your fixes
2. Commit them: `git add . && git commit -m "Manual fix: description"`
3. Run Basher again: `~/.basher/basher.sh`

Basher will pick up where it left off.

---

## FAQ

### Q: How much does this cost?

Basher uses Claude Code, which requires an Anthropic account. Check [Anthropic's pricing](https://www.anthropic.com/pricing) for current rates. Costs depend on:
- Number of tasks
- Complexity of each task
- Which model you use (Sonnet is cheaper than Opus)

### Q: Can I use this for any programming language?

Yes! Basher is language-agnostic. It works with:
- JavaScript/TypeScript
- Python
- Rust
- Go
- Ruby
- Java
- And more...

Just make sure your quality gate commands are configured correctly.

### Q: What if I don't like what Basher built?

You have full control:
- Review each commit with `git log` and `git diff`
- Revert changes with `git revert` or `git reset`
- Edit the PRD and run again
- Make manual changes anytime

### Q: Can I run Basher on an existing project?

Absolutely! Just:
1. Navigate to your project
2. Run `~/.basher/basher-init.sh`
3. Create a PRD for the new features you want
4. Run Basher

It will create a new branch and won't touch your main code until you merge.

### Q: How do I stop Basher mid-run?

Press `Ctrl+C` in the terminal. Basher will stop after the current iteration completes. Your progress is saved — you can resume later.

### Q: Is my code sent to Anthropic?

Yes, Basher uses Claude Code, which sends your code to Anthropic's servers for processing. Review [Anthropic's privacy policy](https://www.anthropic.com/privacy) for details. Don't use Basher with code you can't share with Anthropic.

### Q: Can multiple people run Basher on the same repo?

Yes, but coordinate:
- Each person should use a different branch
- Or work on different features
- Merge carefully to avoid conflicts

### Q: What's the largest project Basher can handle?

Basher works best with focused features. For large projects:
- Break work into phases
- Create separate PRDs for each phase
- Run Basher for each phase sequentially

---

## Contributing

We welcome contributions! Here's how to help:

### Reporting Issues

Found a bug or have a suggestion?
1. Check existing issues first
2. Open a new issue with:
   - What you expected
   - What actually happened
   - Steps to reproduce
   - Your environment (OS, Claude Code version)

### Submitting Changes

1. Fork this repository
2. Create a branch: `git checkout -b my-improvement`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Areas for Contribution

- Documentation improvements
- Support for more tech stacks
- Better error messages
- New features
- Bug fixes

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Credits

- Inspired by [Ralph](https://github.com/snarktank/ralph) by Geoffrey Huntley
- Built for [Claude Code](https://claude.ai) by Anthropic

---

## Getting Help

- **Documentation**: You're reading it!
- **Issues**: [GitHub Issues](https://github.com/feelgreatfoodie/basher/issues)
- **Discussions**: [GitHub Discussions](https://github.com/feelgreatfoodie/basher/discussions)

---

Happy building!
