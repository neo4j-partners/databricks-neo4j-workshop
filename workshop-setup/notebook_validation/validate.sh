#!/usr/bin/env bash
# Validate that files were uploaded to the Databricks workspace.
#
# Usage:
#   ./validate.sh                  # lists all files in the remote directory
#   ./validate.sh run_lab2_02.py   # checks a specific file exists

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env
set -a
source "$SCRIPT_DIR/.env"
set +a

PROFILE="$DATABRICKS_PROFILE"
REMOTE_DIR="$WORKSPACE_DIR"
CLUSTER_ID="$DATABRICKS_CLUSTER_ID"

# shellcheck source=cluster_utils.sh
source "$SCRIPT_DIR/cluster_utils.sh"

echo "Checking cluster and workspace (profile: $PROFILE)"
echo "---"
ensure_cluster_running "$PROFILE" "$CLUSTER_ID"

echo ""
echo "Listing workspace: $REMOTE_DIR"
echo "---"

if ! databricks workspace list --profile "$PROFILE" "$REMOTE_DIR" 2>/dev/null; then
    echo "Error: Remote directory $REMOTE_DIR does not exist."
    echo "Run ./upload.sh first to create it."
    exit 1
fi

echo ""
echo "Listing: $REMOTE_DIR/agent_modules"
echo "---"
databricks workspace list --profile "$PROFILE" "$REMOTE_DIR/agent_modules" 2>/dev/null || true

# If a specific file was requested, check it exists in agent_modules/
if [[ -n "${1:-}" ]]; then
    echo ""
    echo "Checking: $REMOTE_DIR/agent_modules/$1"
    if databricks workspace get-status --profile "$PROFILE" "$REMOTE_DIR/agent_modules/$1" 2>/dev/null; then
        echo "  Found."
    else
        echo "  Not found."
        exit 1
    fi
fi

echo ""
echo "Validation complete."
