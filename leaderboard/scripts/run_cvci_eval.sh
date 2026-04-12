#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

CARLA_ROOT="${CARLA_ROOT:-/path/to/CARLA_0.9.15}"
if [[ "${CARLA_ROOT}" == "/path/to/CARLA_0.9.15" ]]; then
  echo "[run_cvci_eval] Please set CARLA_ROOT first."
  echo "Example: export CARLA_ROOT=/home/yourname/carla0.9.15/CARLA_0.9.15"
  exit 1
fi

export SCENARIO_RUNNER_ROOT="${SCENARIO_RUNNER_ROOT:-scenario_runner}"
export LEADERBOARD_ROOT="${LEADERBOARD_ROOT:-leaderboard}"
export PYTHONPATH="${PYTHONPATH:-}:${CARLA_ROOT}/PythonAPI:${CARLA_ROOT}/PythonAPI/carla:${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg:${ROOT_DIR}/leaderboard:${ROOT_DIR}/scenario_runner"

ROUTES="${ROUTES:-scenario_runner/srunner/data/CVCI_BenchMark.xml}"
ROUTES_SUBSET="${ROUTES_SUBSET:-0-143}"
AGENT="${AGENT:-leaderboard/leaderboard/autoagents/human_agent.py}"
AGENT_CONFIG="${AGENT_CONFIG:-}"
CHECKPOINT="${CHECKPOINT:-./evaluation_results/cvci_benchmark.json}"
PORT="${PORT:-2000}"
TM_PORT="${TM_PORT:-8000}"
GPU_RANK="${GPU_RANK:-0}"
REPETITIONS="${REPETITIONS:-1}"
TRACK="${TRACK:-SENSORS}"

mkdir -p "$(dirname "${CHECKPOINT}")"

CMD=(
  python leaderboard/leaderboard/leaderboard_evaluator.py
  --routes "${ROUTES}"
  --routes-subset "${ROUTES_SUBSET}"
  --repetitions "${REPETITIONS}"
  --track "${TRACK}"
  --agent "${AGENT}"
  --checkpoint "${CHECKPOINT}"
  --port "${PORT}"
  --traffic-manager-port "${TM_PORT}"
  --gpu-rank "${GPU_RANK}"
)

if [[ -n "${AGENT_CONFIG}" ]]; then
  CMD+=(--agent-config "${AGENT_CONFIG}")
fi

echo "[run_cvci_eval] Running command:"
printf '%q ' "${CMD[@]}"
echo

"${CMD[@]}"
