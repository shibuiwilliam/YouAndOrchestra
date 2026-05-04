#!/usr/bin/env bash
# Post-generate critique hook for YaO
# Automatically runs the Adversarial Critic after generation completes.
# Triggered: after any generation step produces a new iteration.

set -euo pipefail

PROJECT_NAME="${1:-}"

if [ -z "$PROJECT_NAME" ]; then
    echo "Usage: post-generate-critique.sh <project-name>"
    exit 1
fi

echo "=== Post-generate: Running Adversarial Critique ==="

yao critique "$PROJECT_NAME"

echo "=== Post-generate critique complete ==="
