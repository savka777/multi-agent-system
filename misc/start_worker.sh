#!/bin/bash
# RQ Worker startup script with macOS fork safety disabled
# This is required because Claude Agent SDK spawns subprocesses

export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

echo "Starting RQ worker with fork safety disabled..."
cd "$(dirname "$0")"
uv run rq worker agents
