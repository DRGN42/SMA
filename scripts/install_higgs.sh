#!/usr/bin/env bash
set -euo pipefail

HIGGS_REPO_URL="${HIGGS_REPO_URL:-}"
HIGGS_DIR="${HIGGS_DIR:-third_party/higgs-audio}"
HIGGS_VENV_DIR="${HIGGS_VENV_DIR:-.venv-higgs}"

if [[ -z "$HIGGS_REPO_URL" ]]; then
  echo "HIGGS_REPO_URL is not set. Export it to the Higgs Audio v2 repo URL." >&2
  echo "Example: export HIGGS_REPO_URL=git@github.com:YOUR_ORG/higgs-audio.git" >&2
  exit 1
fi

if [[ ! -d "$HIGGS_DIR" ]]; then
  echo "Cloning Higgs repo into $HIGGS_DIR"
  git clone "$HIGGS_REPO_URL" "$HIGGS_DIR"
else
  echo "Higgs repo already exists at $HIGGS_DIR"
fi

cd "$HIGGS_DIR"

if [[ -f "pyproject.toml" || -f "setup.py" ]]; then
  if [[ ! -d "$HIGGS_VENV_DIR" ]]; then
    python -m venv "$HIGGS_VENV_DIR"
  fi
  # shellcheck disable=SC1090
  source "$HIGGS_VENV_DIR/bin/activate"
  pip install --upgrade pip
  if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
  fi
  pip install -e .
  echo "Installed Higgs in editable mode."
else
  echo "No Python packaging files found. Follow Higgs repo build instructions." >&2
  exit 1
fi

echo "Done. Ensure the Higgs CLI is available in PATH (see repo docs)."
