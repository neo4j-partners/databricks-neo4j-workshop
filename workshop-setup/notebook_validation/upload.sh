#!/usr/bin/env bash
# Upload Python files to the Databricks workspace.
#
# All Python files live in agent_modules/. The remote structure mirrors local:
#   $WORKSPACE_DIR/agent_modules/*.py
#
# Usage:
#   ./upload.sh                    # uploads test_hello.py (default)
#   ./upload.sh run_lab2_02.py     # uploads a specific file
#   ./upload.sh --all              # uploads all agent_modules/*.py files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env
set -a
source "$SCRIPT_DIR/.env"
set +a

PROFILE="$DATABRICKS_PROFILE"
REMOTE_DIR="$WORKSPACE_DIR"

# Ensure remote directories exist
databricks workspace mkdirs --profile "$PROFILE" "$REMOTE_DIR" 2>/dev/null || true
databricks workspace mkdirs --profile "$PROFILE" "$REMOTE_DIR/agent_modules" 2>/dev/null || true

upload_file() {
    local local_file="$1"
    local remote_path="$2"

    echo "Uploading: $(basename "$local_file") -> $remote_path"
    databricks workspace import \
        --profile "$PROFILE" \
        --file "$local_file" \
        --format AUTO \
        --language PYTHON \
        --overwrite \
        "$remote_path"
    echo "  Done."
}

upload_agent_modules() {
    local local_dir="$SCRIPT_DIR/agent_modules"

    for f in "$local_dir"/*.py; do
        [[ -f "$f" ]] && upload_file "$f" "$REMOTE_DIR/agent_modules/$(basename "$f")"
    done
}

# Parse arguments
if [[ "${1:-}" == "--all" || "${1:-}" == "agent_modules" ]]; then
    echo "Uploading all agent_modules/ to $REMOTE_DIR/agent_modules (profile: $PROFILE)"
    echo "---"
    upload_agent_modules
elif [[ -n "${1:-}" ]]; then
    local_path="$SCRIPT_DIR/agent_modules/$1"
    if [[ ! -f "$local_path" ]]; then
        echo "Error: $local_path not found"
        exit 1
    fi
    echo "Uploading to $REMOTE_DIR/agent_modules (profile: $PROFILE)"
    echo "---"
    upload_file "$local_path" "$REMOTE_DIR/agent_modules/$(basename "$local_path")"
else
    echo "Uploading test_hello.py to $REMOTE_DIR/agent_modules (profile: $PROFILE)"
    echo "---"
    upload_file "$SCRIPT_DIR/agent_modules/test_hello.py" "$REMOTE_DIR/agent_modules/test_hello.py"
fi

echo ""
echo "Upload complete."
