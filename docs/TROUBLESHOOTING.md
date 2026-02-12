# Troubleshooting Guide

This guide covers common issues and their solutions when using Basher for Claude Code.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Runtime Errors](#runtime-errors)
3. [Quality Gate Failures](#quality-gate-failures)
4. [Git Issues](#git-issues)
5. [Anti-Patterns & Known Pitfalls](#anti-patterns--known-pitfalls)
6. [CLU API & Docker Issues](#clu-api--docker-issues)
7. [Performance Issues](#performance-issues)
8. [Getting Help](#getting-help)

---

## Installation Issues

### "curl: command not found"

**Problem:** You're trying to use the one-line installer but curl isn't available.

**Solution:**

On Mac (curl should be pre-installed, but if not):
```bash
brew install curl
```

On Ubuntu/Debian:
```bash
sudo apt update && sudo apt install curl
```

On CentOS/RHEL:
```bash
sudo yum install curl
```

**Alternative:** Clone the repository manually instead:
```bash
git clone https://github.com/feelgreatfoodie/basher-claude-code.git
cd basher-claude-code
./install.sh
```

---

### "Permission denied" when running install.sh

**Problem:** The script doesn't have execute permissions.

**Solution:**
```bash
chmod +x install.sh
./install.sh
```

---

### "claude: command not found"

**Problem:** Claude Code CLI isn't installed or isn't in your PATH.

**Solution:**

1. **Install Claude Code:**
   - Visit [claude.ai/download](https://claude.ai/download)
   - Download the installer for your operating system
   - Run the installer

2. **Add to PATH (if installed but not found):**

   Find where Claude was installed:
   ```bash
   which claude
   # or
   find /usr -name "claude" 2>/dev/null
   find /opt -name "claude" 2>/dev/null
   ```

   Add to your PATH in `~/.zshrc` or `~/.bashrc`:
   ```bash
   export PATH="/path/to/claude/directory:$PATH"
   ```

3. **Restart your terminal** after making changes.

---

### Installation succeeds but basher.sh not found

**Problem:** Basher was installed but the command isn't recognized.

**Solution:**

Add Basher to your PATH:

For Zsh (default on Mac):
```bash
echo 'export PATH="$HOME/.basher:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

For Bash:
```bash
echo 'export PATH="$HOME/.basher:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verify:
```bash
which basher.sh
# Should output: /Users/yourname/.basher/basher.sh
```

---

## Runtime Errors

### "Not in a git repository"

**Problem:** Basher requires git to track changes.

**Solution:**

Initialize git in your project:
```bash
cd your-project
git init
git add .
git commit -m "Initial commit"
```

---

### "No prd.json found"

**Problem:** Basher can't find the task list.

**Solution:**

1. Make sure you've run the PRD generation steps:
   ```bash
   # Start Claude Code
   claude

   # Generate PRD from your notes
   /prd

   # Convert to JSON
   /basher-convert
   ```

2. Check that the files exist:
   ```bash
   ls -la ./basher/
   # Should show prd.md and prd.json
   ```

3. If files are in the wrong location, move them:
   ```bash
   mkdir -p ./basher
   mv prd.json ./basher/
   ```

---

### "Max iterations reached"

**Problem:** Basher hit the safety limit without completing all tasks.

**Possible causes:**
- Tasks are too complex
- Quality gates keep failing
- A task is stuck in a loop

**Solutions:**

1. **Check remaining tasks:**
   ```bash
   # Look at prd.json to see what's incomplete
   cat ./basher/prd.json | grep '"passes": false'
   ```

2. **Increase the iteration limit:**
   ```bash
   ~/.basher/basher.sh 50  # Run up to 50 iterations
   ```

3. **Check progress.txt for patterns:**
   ```bash
   cat ./basher/progress.txt
   # Look for repeated errors or stuck tasks
   ```

4. **Split complex tasks:**
   Edit `./basher/prd.json` and break large tasks into smaller ones.

---

### "Context window exceeded" or similar Claude errors

**Problem:** A task is too complex for Claude to handle in one session.

**Solution:**

1. **Make tasks smaller.** Edit `./basher/prd.json` and split:

   Instead of:
   ```json
   {
     "id": "US-001",
     "title": "Build user authentication system",
     ...
   }
   ```

   Use:
   ```json
   {
     "id": "US-001",
     "title": "Create user data model",
     ...
   },
   {
     "id": "US-002",
     "title": "Add registration endpoint",
     ...
   },
   {
     "id": "US-003",
     "title": "Add login endpoint",
     ...
   }
   ```

2. **Simplify acceptance criteria.** Each task should have 2-4 clear criteria, not 10+.

---

### Script exits immediately without output

**Problem:** The script crashes before producing any output.

**Solutions:**

1. **Run with debug mode:**
   ```bash
   bash -x ~/.basher/basher.sh 2>&1 | head -100
   ```

2. **Check for syntax errors:**
   ```bash
   bash -n ~/.basher/basher.sh
   ```

3. **Verify file integrity:**
   ```bash
   # Re-run the installer
   ./install.sh
   ```

---

## Quality Gate Failures

### Lint errors blocking progress

**Problem:** Linting fails repeatedly.

**Solutions:**

1. **Check the specific errors:**
   ```bash
   # For Node.js
   npm run lint

   # For Python
   ruff check .
   ```

2. **Fix automatically if possible:**
   ```bash
   # Node.js with ESLint
   npm run lint -- --fix

   # Python with Ruff
   ruff check . --fix
   ```

3. **Disable auto-detection and specify custom command:**
   Edit `./basher/basher.config.json`:
   ```json
   {
     "quality": {
       "autoDetect": false,
       "commands": {
         "lint": "npm run lint -- --fix",
         ...
       }
     }
   }
   ```

---

### Tests keep failing

**Problem:** Tests fail and block task completion.

**Solutions:**

1. **Run tests manually to see details:**
   ```bash
   npm test
   # or
   pytest -v
   ```

2. **Check if tests existed before Basher:**
   Maybe there were pre-existing failing tests.

3. **Review recent changes:**
   ```bash
   git log --oneline -10
   git diff HEAD~3
   ```

4. **Temporarily skip tests** (not recommended for production):
   ```json
   {
     "quality": {
       "commands": {
         "test": "echo 'Skipping tests'"
       }
     }
   }
   ```

---

### Type checking errors

**Problem:** TypeScript or type checking fails.

**Solutions:**

1. **See the specific errors:**
   ```bash
   npx tsc --noEmit
   ```

2. **Check for missing type definitions:**
   ```bash
   npm install --save-dev @types/node @types/whatever
   ```

3. **Review generated code** for type issues.

---

## Git Issues

### "Branch already exists"

**Problem:** The feature branch Basher wants to use already exists.

**Solutions:**

1. **Delete the old branch (if safe):**
   ```bash
   git branch -D basher/your-feature
   ```

2. **Or use the existing branch:**
   ```bash
   git checkout basher/your-feature
   ```

3. **Or change the branch name** in `./basher/prd.json`:
   ```json
   {
     "branchName": "basher/your-feature-v2",
     ...
   }
   ```

---

### "Merge conflicts"

**Problem:** Git can't merge changes automatically.

**Solutions:**

1. **Resolve conflicts manually:**
   ```bash
   git status  # See conflicted files
   # Edit files to resolve conflicts
   git add .
   git commit -m "Resolve merge conflicts"
   ```

2. **Start fresh:**
   ```bash
   git checkout main
   git branch -D basher/your-feature
   # Reset prd.json passes to false
   # Run Basher again
   ```

---

### "Nothing to commit"

**Problem:** A task completes but makes no changes.

**Possible causes:**
- Task was already done
- Claude misunderstood the task
- Files were modified but not saved

**Solution:** Check `./basher/progress.txt` to see what Claude did (or didn't do).

---

## Anti-Patterns & Known Pitfalls

These are hard-won lessons from live testing. Avoid these mistakes.

### `--prompt-file` is NOT a valid Claude CLI flag

**Problem:** Scripts using `--prompt-file` will fail silently when combined with `|| true`.

```bash
# BROKEN — --prompt-file is not a valid Claude CLI flag
output=$(claude --prompt-file "$prompt_file" --dangerously-skip-permissions 2>&1) || true
```

**Symptom:** Iterations complete instantly (< 1 second each) with no actual work done. The `|| true` swallows the error, so the script keeps looping through all iterations doing nothing.

**Fix:** Pipe the prompt file via stdin with `-p` (print/non-interactive mode):

```bash
# CORRECT — pipe prompt via stdin
output=$(cat "$prompt_file" | claude -p --dangerously-skip-permissions 2>&1) || true
```

**Key insight:** If iterations are completing in under 2 seconds, Claude isn't actually running. Check the invocation method.

---

### Silent failures from `|| true`

**Problem:** `|| true` at the end of a command suppresses all errors, making failures invisible.

**Symptom:** Scripts appear to work but produce no output. No error messages. Progress logs show rapid empty iterations.

**Best practice:** When using `|| true` for fault tolerance, add a validation check:

```bash
output=$(some_command 2>&1) || true

# Validate the output isn't empty
if [[ -z "$output" || ${#output} -lt 50 ]]; then
    log_error "Command produced no output — likely failed silently"
    exit 1
fi
```

---

### `main` vs `master` branch mismatch

**Problem:** Basher defaults to creating branches from `main`, but some repos use `master`.

**Symptom:** `fatal: 'main' is not a commit and a branch cannot be created from it`

**Fix:** Either rename your branch or update `basher.config.json`:

```bash
# Option A: Rename master to main
git branch -m master main

# Option B: Update Basher config
# In ./basher/basher.config.json:
{
  "git": {
    "baseBranch": "master"
  }
}
```

---

### Hardcoded model IDs break on updates

**Problem:** Using full model IDs like `claude-opus-4-5-20251101` will break when Anthropic releases new versions.

**Fix:** Use model aliases instead:

```bash
# BROKEN — hardcoded model ID, will go stale
claude --model claude-opus-4-5-20251101

# CORRECT — alias always resolves to latest
claude --model opus
```

Valid aliases: `opus`, `sonnet`, `haiku`

---

### Skills not discoverable as slash commands

**Problem:** Skills defined in `skills/*/prompt.md` aren't automatically registered with Claude Code.

**Symptom:** Typing `/clu` in Claude Code shows "unknown command."

**Fix:** Skills must also be registered in `.claude/commands/`. The `install.sh` script handles this, but if you've added new skills manually:

```bash
# Skills need to be in .claude/commands/ (symlinked or copied)
ls ~/.claude/commands/
# Should show: clu.md, clu-analyze.md, clu-prd.md, basher-convert.md, etc.
```

Re-run `install.sh` to fix missing skill registrations.

---

### Initial commit required before basher.sh

**Problem:** `basher.sh` tries to create a branch, which requires at least one commit.

**Symptom:** `fatal: Not a valid object name: 'main'`

**Fix:** Make an initial commit before running Basher:

```bash
git add .
git commit -m "Initial commit"
~/.basher/basher.sh
```

---

## CLU API & Docker Issues

### docker-compose up fails

**Problem:** Services won't start or crash on startup.

**Solutions:**

1. **Check Docker is running:**
   ```bash
   docker info
   ```

2. **Check port conflicts (5432, 6379, 8000):**
   ```bash
   lsof -i :5432   # PostgreSQL
   lsof -i :6379   # Redis
   lsof -i :8000   # API
   ```

3. **Reset everything:**
   ```bash
   cd clu-api
   docker-compose down -v   # Remove containers AND volumes
   docker-compose up -d     # Fresh start
   docker-compose exec api alembic upgrade head
   ```

---

### Alembic migration errors

**Problem:** `alembic upgrade head` fails.

**Solutions:**

1. **Check the database is ready:**
   ```bash
   docker-compose exec db pg_isready
   ```

2. **Reset migrations (development only):**
   ```bash
   docker-compose exec api alembic downgrade base
   docker-compose exec api alembic upgrade head
   ```

3. **Check migration files for syntax:**
   ```bash
   ls clu-api/alembic/versions/
   ```

---

### Redis connection refused

**Problem:** API returns 500 errors related to Redis.

**Solution:** Verify Redis is running and accessible:
```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

If Redis isn't started, check `docker-compose.yml` includes the Redis service.

---

### ChromaDB not responding

**Problem:** Semantic search features return errors.

**Solution:** ChromaDB takes a few seconds to initialize:
```bash
# Check health
curl http://localhost:8000/health
# Look for "chromadb": "healthy" in response
```

If ChromaDB is unhealthy, restart it:
```bash
docker-compose restart chromadb
```

---

### API returns 401 Unauthorized

**Problem:** All API requests fail with 401.

**Solution:** The v0.4 API requires an API key header:
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/projects
```

For local development, check if auth middleware is active. You may need to create an API key in the database or disable auth for development.

---

### kickoff-clu.sh hangs in background

**Problem:** `kickoff-clu.sh` stops responding when run in background.

**Cause:** Interactive `read -p` prompts can't receive input in background mode.

**Fix:** Use the `--yes` flag to skip all interactive prompts:
```bash
./scripts/kickoff-clu.sh --from v0.2 --yes
```

---

## Performance Issues

### Basher is very slow

**Possible causes:**
- Large codebase (more context to process)
- Many files to read
- Complex tasks

**Solutions:**

1. **Use Sonnet instead of Opus:**
   ```json
   {
     "claude": {
       "model": "sonnet"
     }
   }
   ```

2. **Reduce iteration delay:**
   ```json
   {
     "iterations": {
       "delaySeconds": 1
     }
   }
   ```

3. **Add a `.claudeignore` file** to exclude unnecessary files:
   ```
   node_modules/
   dist/
   .git/
   *.log
   ```

---

### High API costs

**Solutions:**

1. **Use smaller models** when possible
2. **Break work into phases** (smaller PRDs)
3. **Review tasks before running** to avoid wasted iterations

---

## Getting Help

### Checking logs

**Progress log:**
```bash
cat ./basher/progress.txt
```

**Git history:**
```bash
git log --oneline
git log -p  # With diffs
```

**Last iteration output:**
Check your terminal scrollback, or redirect output:
```bash
~/.basher/basher.sh 2>&1 | tee basher-output.log
```

### Reporting issues

When reporting issues, please include:

1. **Operating system and version**
2. **Output of:** `claude --version`
3. **The error message** (full text)
4. **Contents of:**
   - `./basher/basher.config.json`
   - `./basher/progress.txt` (last 50 lines)
5. **Steps to reproduce**

Open issues at: https://github.com/feelgreatfoodie/basher-claude-code/issues

### Community support

- GitHub Discussions: https://github.com/feelgreatfoodie/basher-claude-code/discussions
- Search existing issues first — your problem may already be solved!
