#!/usr/bin/env bash
set -euo pipefail

HOST="${RPI_HOST:-inky}"
USER="${RPI_USER:-inky}"
REMOTE_DIR="/home/${USER}/src/inky-dashboard"

echo "Deploying to ${HOST}:${REMOTE_DIR}"

# Sync project files, excluding local venv and dev artifacts
rsync -avz --delete \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.git/' \
  --exclude='scripts/' \
  . "${HOST}:${REMOTE_DIR}"

# Install/sync dependencies on the remote using uv
ssh "${HOST}" "cd ${REMOTE_DIR} && ~/.local/bin/uv sync --no-dev"

echo "Deploy complete."
