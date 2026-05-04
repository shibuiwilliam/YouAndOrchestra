#!/usr/bin/env bash
# Update provenance hook for YaO
# Ensures provenance.json is written after any modification to a project's artifacts.
# Triggered: after any modification to project outputs.

set -euo pipefail

PROJECT_DIR="${1:-}"

if [ -z "$PROJECT_DIR" ]; then
    echo "Usage: update-provenance.sh <project-output-dir>"
    exit 1
fi

echo "=== Updating provenance graph ==="

# Provenance is typically updated programmatically by the Conductor/generators.
# This hook exists as a safety net to verify provenance.json exists and is valid JSON.

PROVENANCE_FILE="$PROJECT_DIR/provenance.json"

if [ -f "$PROVENANCE_FILE" ]; then
    # Validate JSON
    python -c "import json; json.load(open('$PROVENANCE_FILE'))" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "WARNING: provenance.json is not valid JSON"
        exit 1
    fi
    echo "Provenance file valid: $PROVENANCE_FILE"
else
    echo "WARNING: No provenance.json found in $PROJECT_DIR"
    echo "Generation steps must produce provenance. Check the pipeline."
    exit 1
fi

echo "=== Provenance check complete ==="
