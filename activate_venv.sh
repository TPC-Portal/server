#!/usr/bin/env bash
# Activate the project virtual environment (for local terminal use)
# Usage: run `source server/activate_venv.sh` from the repository root or
# `source activate_venv.sh` from the `server/` directory.

VENV_PATH="/Users/sankalpgupta/Desktop/BTP/.venv"
if [ -d "$VENV_PATH" ]; then
  # shellcheck disable=SC1090
  source "$VENV_PATH/bin/activate"
  echo "Activated venv: $VENV_PATH"
else
  echo "Virtual environment not found at $VENV_PATH"
  echo "Create it with: python -m venv /Users/sankalpgupta/Desktop/BTP/.venv"
fi
