#!/usr/bin/env bash
# Quickstart: install, run, and inspect results in one command.
set -euo pipefail

if [[ ! -f pyproject.toml ]]; then
    echo "Run from the repo root." >&2
    exit 1
fi

echo "▸ Installing in editable mode..."
pip install -e ".[dev]" >/dev/null

echo "▸ Running smoke test against mock provider (no API key needed)..."
python -m aeris run \
    --config configs/smoke.yaml \
    --model mock/echo \
    --output results/quickstart \
    --i-have-permission-to-test

echo ""
echo "▸ Done. Inspect:"
echo "  results/quickstart/manifest.json   — reproducibility manifest"
echo "  results/quickstart/records.jsonl   — per-item records"
echo "  results/quickstart/summary.json    — aggregated metrics"
