#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${HOME}/.local/bin"
mkdir -p "${TARGET_DIR}"

if command -v pip >/dev/null 2>&1; then
  pip install --user --upgrade "shellsensei"
else
  echo "pip not found. Please install Python + pip first."
  exit 1
fi

echo "ShellSensei installed. Ensure ${TARGET_DIR} is on PATH."
echo "Run: shellsensei --help"
