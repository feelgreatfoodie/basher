# Contributing to Basher for Claude Code

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Ways to Contribute

### 1. Report Issues

Found a bug or have a suggestion? Open an issue!

**Before opening an issue:**
- Search existing issues to avoid duplicates
- Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

**When opening an issue, include:**
- Clear description of the problem or suggestion
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Your environment (OS, Claude Code version, shell)
- Relevant logs or error messages

### 2. Improve Documentation

Documentation improvements are always welcome:
- Fix typos or unclear explanations
- Add examples
- Improve the README for specific audiences
- Translate documentation

### 3. Submit Code Changes

We welcome code contributions:
- Bug fixes
- New features
- Performance improvements
- Additional tech stack support

## Development Setup

### Prerequisites

- Git
- Claude Code CLI (for testing)
- Bash 3.0+

### Getting Started

1. **Fork the repository**
   - Click "Fork" on GitHub
   - Clone your fork locally:
     ```bash
     git clone https://github.com/feelgreatfoodie/basher-claude-code.git
     cd basher-claude-code
     ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make your changes**
   - Follow the code style guidelines below
   - Test your changes thoroughly

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add support for Ruby projects"
   # or
   git commit -m "fix: correct path detection on Windows"
   ```

5. **Push and create a PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a Pull Request on GitHub.

## Code Style Guidelines

### Bash Scripts

- Use `#!/usr/bin/env bash` shebang
- Enable strict mode: `set -euo pipefail`
- Use meaningful variable names in UPPER_CASE for globals
- Use lowercase for local variables
- Quote all variable expansions: `"$variable"`
- Add comments for complex logic
- Use functions for reusable code

**Example:**
```bash
#!/usr/bin/env bash
set -euo pipefail

# Global configuration
BASHER_HOME="${BASHER_HOME:-$HOME/.basher}"

# Check if a file exists and is readable
check_file() {
    local file_path="$1"
    if [[ -f "$file_path" && -r "$file_path" ]]; then
        return 0
    fi
    return 1
}
```

### Markdown Documentation

- Use ATX-style headers (`# Header`)
- Add blank lines around headers and code blocks
- Use fenced code blocks with language identifiers
- Keep lines under 100 characters when possible
- Use reference-style links for repeated URLs

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Formatting, no code change
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

**Examples:**
```
feat: add support for Python poetry projects
fix: handle spaces in project paths
docs: add Windows installation instructions
refactor: simplify tech stack detection logic
```

## Testing Your Changes

### Manual Testing

1. **Install your modified version:**
   ```bash
   ./install.sh
   ```

2. **Test in a sample project:**
   ```bash
   mkdir test-project && cd test-project
   git init
   ~/.basher/basher-init.sh
   ```

3. **Test the full workflow:**
   - Create a simple transcript
   - Generate PRD
   - Convert to JSON
   - Run basher.sh

### What to Test

- [ ] Installation on a fresh system
- [ ] Installation over an existing installation
- [ ] basher-init.sh in various project types
- [ ] Tech stack detection for affected languages
- [ ] The full PRD → JSON → execution workflow
- [ ] Error handling for edge cases

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows the style guidelines
- [ ] Changes are tested
- [ ] Documentation is updated (if applicable)
- [ ] Commit messages follow conventions

### PR Description

Include:
- What the change does
- Why it's needed
- How it was tested
- Any breaking changes

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge

## Adding Support for New Tech Stacks

To add detection for a new language/framework:

1. **Edit `lib/detect-stack.sh`:**
   ```bash
   # Add detection logic
   if [[ -f "$project_dir/your-config-file" ]]; then
       STACK_TYPE="your-stack"
       LINT_CMD="your-lint-command"
       TYPECHECK_CMD="your-typecheck-command"
       TEST_CMD="your-test-command"
       BUILD_CMD="your-build-command"
       return 0
   fi
   ```

2. **Update documentation:**
   - Add to the tech stack table in README.md
   - Add any special instructions

3. **Test thoroughly:**
   - Create a sample project of that type
   - Verify detection works
   - Verify commands execute correctly

## Questions?

- Open a Discussion on GitHub
- Check existing issues and discussions
- Read the [FAQ](README.md#faq)

## Code of Conduct

Be respectful and inclusive. We're all here to build something useful together.

---

Thank you for contributing!
