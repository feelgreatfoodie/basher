#!/usr/bin/env bash
#
# Tech Stack Auto-Detection for Basher
#
# Detects the project's technology stack and outputs appropriate
# quality gate commands. Can be sourced or run directly.
#
# Usage:
#   source detect-stack.sh
#   detect_stack /path/to/project
#
# Outputs (as environment variables):
#   STACK_TYPE     - Detected stack (node, python, rust, go, unknown)
#   LINT_CMD       - Linting command
#   TYPECHECK_CMD  - Type checking command
#   TEST_CMD       - Test command
#   BUILD_CMD      - Build command
#

detect_stack() {
    local project_dir="${1:-.}"

    # Reset variables
    STACK_TYPE="unknown"
    LINT_CMD=""
    TYPECHECK_CMD=""
    TEST_CMD=""
    BUILD_CMD=""

    # ========================================================================
    # Node.js / JavaScript / TypeScript
    # ========================================================================
    if [[ -f "$project_dir/package.json" ]]; then
        STACK_TYPE="node"

        # Check for specific scripts in package.json
        local pkg="$project_dir/package.json"

        # Detect package manager (bun > pnpm > yarn > npm)
        local pkg_manager="npm"
        local pkg_runner="npx"
        if [[ -f "$project_dir/bun.lockb" ]] || [[ -f "$project_dir/bun.lock" ]]; then
            pkg_manager="bun"
            pkg_runner="bun"
        elif [[ -f "$project_dir/pnpm-lock.yaml" ]]; then
            pkg_manager="pnpm"
            pkg_runner="pnpm"
        elif [[ -f "$project_dir/yarn.lock" ]]; then
            pkg_manager="yarn"
            pkg_runner="yarn"
        fi

        # Lint command
        if grep -q '"lint"' "$pkg" 2>/dev/null; then
            LINT_CMD="$pkg_manager run lint"
        elif [[ -f "$project_dir/.eslintrc.js" ]] || [[ -f "$project_dir/.eslintrc.json" ]] || [[ -f "$project_dir/eslint.config.js" ]]; then
            LINT_CMD="$pkg_runner eslint ."
        elif [[ -f "$project_dir/biome.json" ]]; then
            LINT_CMD="$pkg_runner biome check ."
        fi

        # TypeScript detection
        if [[ -f "$project_dir/tsconfig.json" ]]; then
            STACK_TYPE="typescript"
            if grep -q '"typecheck"' "$pkg" 2>/dev/null; then
                TYPECHECK_CMD="$pkg_manager run typecheck"
            else
                TYPECHECK_CMD="$pkg_runner tsc --noEmit"
            fi
        fi

        # Test command
        if grep -q '"test"' "$pkg" 2>/dev/null; then
            # Check it's not the default "Error: no test specified"
            if ! grep -q 'no test specified' "$pkg" 2>/dev/null; then
                TEST_CMD="$pkg_manager test"
            fi
        fi
        if [[ -z "$TEST_CMD" ]]; then
            if [[ -f "$project_dir/vitest.config.ts" ]] || [[ -f "$project_dir/vitest.config.js" ]]; then
                TEST_CMD="$pkg_runner vitest run"
            elif [[ -f "$project_dir/jest.config.js" ]] || [[ -f "$project_dir/jest.config.ts" ]]; then
                TEST_CMD="$pkg_runner jest"
            fi
        fi

        # Build command
        if grep -q '"build"' "$pkg" 2>/dev/null; then
            BUILD_CMD="$pkg_manager run build"
        fi

        return 0
    fi

    # ========================================================================
    # Python
    # ========================================================================
    if [[ -f "$project_dir/pyproject.toml" ]] || [[ -f "$project_dir/setup.py" ]] || [[ -f "$project_dir/requirements.txt" ]]; then
        STACK_TYPE="python"

        # Lint command - prefer ruff, fall back to flake8
        if [[ -f "$project_dir/ruff.toml" ]] || grep -q 'ruff' "$project_dir/pyproject.toml" 2>/dev/null; then
            LINT_CMD="ruff check ."
        elif command -v ruff &>/dev/null; then
            LINT_CMD="ruff check ."
        elif command -v flake8 &>/dev/null; then
            LINT_CMD="flake8 ."
        fi

        # Type checking
        if [[ -f "$project_dir/mypy.ini" ]] || grep -q 'mypy' "$project_dir/pyproject.toml" 2>/dev/null; then
            TYPECHECK_CMD="mypy ."
        elif [[ -f "$project_dir/pyrightconfig.json" ]]; then
            TYPECHECK_CMD="pyright"
        fi

        # Test command
        if [[ -d "$project_dir/tests" ]] || [[ -d "$project_dir/test" ]]; then
            if grep -q 'pytest' "$project_dir/pyproject.toml" 2>/dev/null || [[ -f "$project_dir/pytest.ini" ]]; then
                TEST_CMD="pytest"
            elif command -v pytest &>/dev/null; then
                TEST_CMD="pytest"
            else
                TEST_CMD="python -m unittest discover"
            fi
        fi

        # Build command (for packages)
        if [[ -f "$project_dir/pyproject.toml" ]]; then
            if grep -q 'build-system' "$project_dir/pyproject.toml" 2>/dev/null; then
                BUILD_CMD="python -m build"
            fi
        fi

        return 0
    fi

    # ========================================================================
    # Rust
    # ========================================================================
    if [[ -f "$project_dir/Cargo.toml" ]]; then
        STACK_TYPE="rust"
        LINT_CMD="cargo clippy -- -D warnings"
        TYPECHECK_CMD="cargo check"
        TEST_CMD="cargo test"
        BUILD_CMD="cargo build"
        return 0
    fi

    # ========================================================================
    # Go
    # ========================================================================
    if [[ -f "$project_dir/go.mod" ]]; then
        STACK_TYPE="go"
        LINT_CMD="golangci-lint run"
        TYPECHECK_CMD="go vet ./..."
        TEST_CMD="go test ./..."
        BUILD_CMD="go build ./..."
        return 0
    fi

    # ========================================================================
    # Ruby
    # ========================================================================
    if [[ -f "$project_dir/Gemfile" ]]; then
        STACK_TYPE="ruby"

        if [[ -f "$project_dir/.rubocop.yml" ]]; then
            LINT_CMD="bundle exec rubocop"
        fi

        # Rails detection
        if [[ -f "$project_dir/config/application.rb" ]]; then
            STACK_TYPE="rails"
            TEST_CMD="bundle exec rails test"
        elif [[ -d "$project_dir/spec" ]]; then
            TEST_CMD="bundle exec rspec"
        fi

        return 0
    fi

    # ========================================================================
    # Java / Kotlin (Gradle)
    # ========================================================================
    if [[ -f "$project_dir/build.gradle" ]] || [[ -f "$project_dir/build.gradle.kts" ]]; then
        STACK_TYPE="gradle"
        LINT_CMD="./gradlew check"
        TEST_CMD="./gradlew test"
        BUILD_CMD="./gradlew build"
        return 0
    fi

    # ========================================================================
    # Java (Maven)
    # ========================================================================
    if [[ -f "$project_dir/pom.xml" ]]; then
        STACK_TYPE="maven"
        TEST_CMD="mvn test"
        BUILD_CMD="mvn package"
        return 0
    fi

    # ========================================================================
    # Unknown stack
    # ========================================================================
    return 1
}

# Output detected configuration as JSON (for use by other scripts)
output_detection_json() {
    cat << EOF
{
  "stackType": "$STACK_TYPE",
  "commands": {
    "lint": $(if [[ -n "$LINT_CMD" ]]; then echo "\"$LINT_CMD\""; else echo "null"; fi),
    "typecheck": $(if [[ -n "$TYPECHECK_CMD" ]]; then echo "\"$TYPECHECK_CMD\""; else echo "null"; fi),
    "test": $(if [[ -n "$TEST_CMD" ]]; then echo "\"$TEST_CMD\""; else echo "null"; fi),
    "build": $(if [[ -n "$BUILD_CMD" ]]; then echo "\"$BUILD_CMD\""; else echo "null"; fi)
  }
}
EOF
}

# Print human-readable detection results
print_detection() {
    echo "Stack Detection Results"
    echo "======================"
    echo "Stack Type: $STACK_TYPE"
    echo ""
    echo "Commands:"
    echo "  Lint:      ${LINT_CMD:-<not detected>}"
    echo "  Typecheck: ${TYPECHECK_CMD:-<not detected>}"
    echo "  Test:      ${TEST_CMD:-<not detected>}"
    echo "  Build:     ${BUILD_CMD:-<not detected>}"
}

# Run detection if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    detect_stack "${1:-.}"
    print_detection
fi
