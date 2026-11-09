#!/usr/bin/env bash
# Deletes the whole cluster. Nothing outside it is touched (ADR 0002); durable data in
# $RACK_DATA_DIR (default ~/k3d-rack-data) is kept on purpose (ADR 0006).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
k3d cluster delete rack
