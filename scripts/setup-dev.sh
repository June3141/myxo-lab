#!/usr/bin/env bash
set -euo pipefail

echo "=== Myxo Lab Developer Setup ==="

# Check prerequisites
missing=()
for cmd in uv cargo task; do
  if ! command -v "$cmd" &>/dev/null; then
    missing+=("$cmd")
  fi
done

if [ ${#missing[@]} -gt 0 ]; then
  echo "ERROR: Missing required tools: ${missing[*]}"
  echo "Install them before running this script."
  exit 1
fi

echo "✓ All prerequisites found"

# Install Python dependencies
echo "Installing Python dependencies..."
uv sync

# Build Rust workspace
echo "Building Rust workspace..."
cargo build

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
uv run pre-commit install

echo ""
echo "=== Setup complete! ==="
echo "Run 'task check' to verify everything works."
