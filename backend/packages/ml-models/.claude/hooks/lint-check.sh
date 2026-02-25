#!/usr/bin/env zsh
# Claude Code PreToolUse Hook - Lint Check
# Runs ruff and pyright on changed Python files
# Receives JSON via stdin, outputs JSON to stdout

# Read the hook input from stdin
INPUT=$(cat)

# Extract the file path from the input
FILEPATH=$(echo "$INPUT" | jq -r '.file_path // empty')

# Only process Python files
if [ -n "$FILEPATH" ] && [[ "$FILEPATH" == *.py ]]; then
    # Change to project directory for correct context
    cd "$(dirname "$FILEPATH")"

    # Run ruff check
    ruff check "$FILEPATH" 2>&1 || true

    # Run pyright (if available)
    if command -v pyright >/dev/null 2>&1; then
        pyright "$FILEPATH" 2>&1 || true
    fi
fi

# Output required JSON response
echo '{"hookSpecificOutput": {"hookEventName": "PreToolUse"}}'
