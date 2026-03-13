#!/usr/bin/env bash
set -euo pipefail
python3 runtime/maw.py routing set --profile balanced
python3 runtime/maw.py dispatch --task "Audit the repository layout and report whether the orchestrator is ready for a dry run."
