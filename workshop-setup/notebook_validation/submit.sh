#!/usr/bin/env bash
# Submit a Python script as a one-time Databricks job run.
#
# Usage:
#   ./submit.sh                             # runs test_hello.py (default)
#   ./submit.sh run_lab2_02.py              # runs the Lab 2 notebook
#   ./submit.sh run_lab2_02.py --no-wait    # submit without waiting
#
# Scripts live in agent_modules/ on the remote workspace.
# Neo4j credentials from .env are automatically injected as script parameters.
# Scripts that don't use argparse (like test_hello.py) safely ignore them.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env
set -a
source "$SCRIPT_DIR/.env"
set +a

PROFILE="$DATABRICKS_PROFILE"
REMOTE_DIR="$WORKSPACE_DIR"
CLUSTER_ID="$DATABRICKS_CLUSTER_ID"

SCRIPT_NAME="${1:-test_hello.py}"
NO_WAIT=""
if [[ "${2:-}" == "--no-wait" ]]; then
    NO_WAIT="--no-wait"
fi

REMOTE_PATH="$REMOTE_DIR/agent_modules/$SCRIPT_NAME"
RUN_NAME="notebook_validation: $SCRIPT_NAME"

# shellcheck source=cluster_utils.sh
source "$SCRIPT_DIR/cluster_utils.sh"

echo "Submitting job (profile: $PROFILE)"
echo "  Script:   $REMOTE_PATH"
ensure_cluster_running "$PROFILE" "$CLUSTER_ID"
echo "  Run name: $RUN_NAME"

# Build parameters: inject credentials from .env.
# Uses Python to safely handle special characters in passwords.
PARAMS="[]"
if [[ -n "${NEO4J_URI:-}" && -n "${NEO4J_PASSWORD:-}" ]] || [[ -n "${MCP_ENDPOINT:-}" && -n "${MCP_API_KEY:-}" ]]; then
    PARAMS=$(python3 -c "
import json, os
params = []
# Neo4j credentials
if os.environ.get('NEO4J_URI') and os.environ.get('NEO4J_PASSWORD'):
    params += [
        '--neo4j-uri', os.environ['NEO4J_URI'],
        '--neo4j-username', os.environ.get('NEO4J_USERNAME', 'neo4j'),
        '--neo4j-password', os.environ['NEO4J_PASSWORD'],
    ]
data_path = os.environ.get('DATA_PATH', '')
if data_path:
    params += ['--data-path', data_path]
# MCP credentials
if os.environ.get('MCP_ENDPOINT') and os.environ.get('MCP_API_KEY'):
    params += [
        '--mcp-endpoint', os.environ['MCP_ENDPOINT'],
        '--mcp-api-key', os.environ['MCP_API_KEY'],
    ]
    mcp_path = os.environ.get('MCP_PATH', '')
    if mcp_path:
        params += ['--mcp-path', mcp_path]
print(json.dumps(params))
")
    [[ -n "${NEO4J_URI:-}" ]] && echo "  Neo4j:    credentials injected from .env"
    [[ -n "${MCP_ENDPOINT:-}" ]] && echo "  MCP:      credentials injected from .env"
fi

echo "---"

# Build the job JSON.
# Uses an existing all-purpose cluster (started automatically if terminated).
JOB_JSON=$(cat <<EOF
{
  "run_name": "$RUN_NAME",
  "tasks": [
    {
      "task_key": "run_script",
      "spark_python_task": {
        "python_file": "$REMOTE_PATH",
        "parameters": $PARAMS
      },
      "existing_cluster_id": "$CLUSTER_ID"
    }
  ]
}
EOF
)

databricks jobs submit \
    --profile "$PROFILE" \
    --json "$JOB_JSON" \
    $NO_WAIT

echo ""
echo "Job submission complete."
