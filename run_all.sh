#!/usr/bin/env bash
# Reproduce every result from the committed derived tables, in order.
# runs from data/derived/*.csv. Run from the repo root: ./run_all.sh
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python

echo "== survival table (needs SSD; skip with SKIP_STAGE1=1) =="
if [[ -z "${SKIP_STAGE1:-}" ]]; then $PY src/survival_table.py --build; else echo "skipped"; fi

echo "== descriptive + gate =="
$PY src/descriptive.py
