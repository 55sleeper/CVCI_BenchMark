# CVCI_BenchMark

<p align="center">
  <img src="./assets/CVCI_2026_Benchmark_Poster_v2.png" alt="CVCI 2026 Benchmark Poster" width="900">
</p>

CVCI_BenchMark is an enhanced benchmark suite built on top of Bench2Drive for the CVCI 2026 challenge.  
It focuses on closed-loop evaluation of end-to-end autonomous driving models under safety-critical, long-tail scenarios.

## Highlights

- Built on the Bench2Drive closed-loop protocol.
- 12 scenario categories and 144 scenario instances.
- Scenario-specific parameter settings define three progressive difficulty levels.
- Multi-difficulty design with weather variants: `night&rain`, `night&sunny`, `day&rain`, `day&sunny`.
- Scenario-aware criteria and customized scoring for safety, task completion, and behavior quality.

## Repository Structure

```text
CVCI_BenchMark/
  assets/
  docs/
  leaderboard/
  scenario_runner/
  tools/
```

Main benchmark routes file:

- `scenario_runner/srunner/data/CVCI_BenchMark.xml`

## Environment Setup

### 1. Create Python Environment

```bash
conda create -n CVCI_Benchmark python=3.7 -y
conda activate CVCI_Benchmark
```

### 2. Install CARLA 0.9.15

```bash
mkdir -p ~/carla && cd ~/carla
wget https://carla-releases.s3.us-east-005.backblazeb2.com/Linux/CARLA_0.9.15.tar.gz
tar -xvf CARLA_0.9.15.tar.gz
cd Import
wget https://carla-releases.s3.us-east-005.backblazeb2.com/Linux/AdditionalMaps_0.9.15.tar.gz
cd ..
bash ImportAssets.sh
```

### 3. Install Python Dependencies

```bash
cd /path/to/CVCI_BenchMark
pip install -r scenario_runner/requirements.txt
pip install -r leaderboard/requirements.txt
```

### 4. Export Required Environment Variables

```bash
export CARLA_ROOT=/path/to/CARLA_0.9.15
export SCENARIO_RUNNER_ROOT=scenario_runner
export LEADERBOARD_ROOT=leaderboard
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg
export PYTHONPATH=$PYTHONPATH:leaderboard
export PYTHONPATH=$PYTHONPATH:scenario_runner
```

## Evaluation

### Quick Start (bash)

```bash
chmod +x leaderboard/scripts/run_cvci_eval.sh
bash leaderboard/scripts/run_cvci_eval.sh
```

Default script behavior:

- Routes: `scenario_runner/srunner/data/CVCI_BenchMark.xml`
- Route subset: `0-143` (all 144 routes)
- Agent: `leaderboard/leaderboard/autoagents/human_agent.py`
- Checkpoint: `./evaluation_results/cvci_benchmark.json`

### Equivalent Python Command

```bash
python leaderboard/leaderboard/leaderboard_evaluator.py \
  --routes scenario_runner/srunner/data/CVCI_BenchMark.xml \
  --routes-subset 0-143 \
  --agent leaderboard/leaderboard/autoagents/human_agent.py \
  --checkpoint ./evaluation_results/cvci_benchmark.json
```

## Metrics and Result Processing

Raw route-level output is written to the `--checkpoint` JSON file.

```bash
python tools/merge_route_json.py -f /path/to/json_folder/
python tools/ability_benchmark.py -r merge.json
python tools/efficiency_smoothness_benchmark.py -f merge.json -m /path/to/metric_folder/
```

## Data Download

### A. Bench2Drive Public Dataset (for training/validation)

<!-- Fill with your own data download links -->

### B. CVCI 2026 Challenge Package

<!-- Fill with your own challenge package access info -->

## CVCI 2026 Challenge Timeline

- Open benchmark and data: April 15, 2026
- Paper and challenge result submission: July 1, 2026
- Final result submission: September 1, 2026

## Challenge Procedure

1. Download the challenge description and benchmark documents released by organizers.
2. Complete registration and request benchmark access from the organizing committee.
3. Receive and run the official benchmark package and scenario configuration.
4. Submit model outputs and required result files before the deadline.
5. Organizer performs final official scoring and ranking.

## Notes

- CARLA can be unstable; use `tools/clean_carla.sh` if CARLA processes are not fully released.
- Avoid port conflicts (`--port`, `--traffic-manager-port`) when running multiple evaluations.
- If CARLA exits immediately, check Vulkan and GPU driver compatibility first.

## License

All assets and code are under the repository license unless specified otherwise.