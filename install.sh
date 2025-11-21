#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

usage() {
  echo "Usage: $0 [--dev]" >&2
  echo "  --dev   Install with all extras and dev dependencies, setup pre-commit" >&2
}

DEV_MODE=false
if [[ ${1:-} == "--dev" ]]; then
  DEV_MODE=true
elif [[ $# -gt 0 ]]; then
  usage
  exit 1
fi

echo "Pin Python and create venv"
uv python pin 3.12.9
uv venv .venv

if [[ "$DEV_MODE" == true ]]; then
  echo "Sync dependencies (all extras + dev)"
  uv sync --all-extras --dev
  echo "Install pre-commit hooks"
  rm -f .git/hooks/pre-commit && rm -f .git/hooks/pre-commit.legacy || true
  pre-commit install
else
  echo "Sync dependencies"
  uv sync
fi

echo "Done. Activate with: source .venv/bin/activate"
