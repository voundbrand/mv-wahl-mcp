#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"

print_config() {
    local client="${1:-cursor}"
    cat <<EOF
{
  "mcpServers": {
    "mv-wahl": {
      "command": "$ROOT/run.sh",
      "args": [],
      "cwd": "$ROOT"
    }
  }
}
EOF
}

print_usage() {
    echo "Usage: $0 [--print-config [cursor|claude]]"
    echo
    echo "Without arguments: start the MCP server (stdio)."
    echo
    echo "Options:"
    echo "  --print-config [cursor|claude]  Print ready-to-use MCP config JSON."
    echo "                                  Copy into ~/.cursor/mcp.json or"
    echo "                                  claude_desktop_config.json."
}

if [[ "${1:-}" == "--print-config" ]]; then
    print_config "${2:-cursor}"
    exit 0
fi

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    print_usage
    exit 0
fi

# Bootstrap venv if missing
if [[ ! -d "$VENV" ]]; then
    echo "Creating virtual environment..." >&2
    python3 -m venv "$VENV"
fi

# Install dependencies if mcp package is missing
if ! "$VENV/bin/python" -c "import mcp" 2>/dev/null; then
    echo "Installing dependencies..." >&2
    "$VENV/bin/pip" install --quiet -r "$ROOT/requirements.txt"
    "$VENV/bin/pip" install --quiet -e "$ROOT"
fi

export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$VENV/bin/python" -m mv_wahl_mcp.server "$@"
