#!/usr/bin/env bash
set -euo pipefail

# Sim + SDK + Dora one-click launcher
# - Starts sim, driver, interface, locomotion, manipulation (SDK side)
# - Starts Dora workflow that uses sim_udp_client (replaces UI)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
TOOLS_DIR="$ROOT_DIR/loong_sim_sdk_release/tools"
WORKFLOW_DIR="$ROOT_DIR/workflow"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$LOG_DIR"

JNT=1
MANI=1

usage() {
  echo "Usage: $0 [--no-jnt] [--no-mani]"
  echo "  --no-jnt   Do not start locomotion controller"
  echo "  --no-mani  Do not start manipulation controller"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-jnt)
      JNT=0
      shift
      ;;
    --no-mani)
      MANI=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

require_cmd dora

PIDS=()

start_bg() {
  local name="$1"; shift
  local log_file="$LOG_DIR/${name}.log"
  echo "[START] $name (logs: $log_file)"
  ( "$@" ) >"$log_file" 2>&1 &
  local pid=$!
  PIDS+=("$pid")
}

cleanup() {
  echo "\n[CLEANUP] Stopping background processes..."
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
  # One more pass with SIGKILL if needed
  sleep 0.5 || true
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
  done
}

trap cleanup EXIT INT TERM

# 1) Sim window
start_bg sim "bash" -lc "cd '$TOOLS_DIR' && ./run_sim.sh"

# 2) Driver window
start_bg driver "bash" -lc "cd '$TOOLS_DIR' && ./run_driver.sh"

# 3) Interface window
start_bg interface "bash" -lc "cd '$TOOLS_DIR' && ./run_interface.sh"

# 4) Locomotion (if enabled)
if [[ "$JNT" -eq 1 ]]; then
  start_bg locomotion "bash" -lc "cd '$TOOLS_DIR' && ./run_locomotion.sh"
fi

# 5) Manipulation (if enabled)
if [[ "$MANI" -eq 1 ]]; then
  start_bg manipulation "bash" -lc "cd '$TOOLS_DIR' && ./run_manipulation.sh"
fi

echo "[INFO] Waiting a moment for SDK processes to initialize..."
sleep 2

echo "[INFO] Starting Dora workflow (foreground). Press Ctrl-C to stop."
cd "$WORKFLOW_DIR"
dora start -c dataflow.yml | cat


