#!/usr/bin/env bash
# Deletes the whole cluster. Nothing outside it is touched (ADR 0002).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
k3d cluster delete rack
