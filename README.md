# CVCI_BenchMark

<p align="center">
  <a href="./assets/CVCI_2026_Benchmark_Poster_1.pdf">
    <img src="./assets/CVCI_2026_Benchmark_Poster_1.png" alt="CVCI 2026 Benchmark Poster" width="1100">
  </a>
</p>

CVCI_BenchMark (Bench2InterActDrive) is a closed-loop benchmark for end-to-end autonomous driving at CVCI 2026.  
Built on Bench2Drive and CARLA, it is designed for safety-critical, long-tail, and highly interactive traffic scenarios.

This repository provides the complete benchmark routes, scenario implementations, and evaluation pipeline used in CVCI 2026.  
For a full overview of motivation, benchmark design, and protocol details, please read [introduction.pdf](./assets/introduction.pdf).  
The benchmark description referenced on the poster is available as [web_description.docx](./assets/web_description.docx).  

## Highlights

- Closed-loop online evaluation in CARLA.
- 12 scenario categories and 144 scenario instances.
- Scenario-specific parameters define three progressive difficulty levels.
- Four weather/lighting variants: `night&rain`, `night&sunny`, `day&rain`, `day&sunny`.
- Dual-score protocol: Bench2Drive route score + CVCI scenario-aware score (weighted fusion).

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

### 3. Install Dependencies

```bash
cd /path/to/CVCI_BenchMark
pip install -r scenario_runner/requirements.txt
pip install -r leaderboard/requirements.txt
```

### 4. Export Environment Variables

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

```bash
python leaderboard/leaderboard/leaderboard_evaluator.py \
  --routes scenario_runner/srunner/data/CVCI_BenchMark.xml \
  --routes-subset 0-143 \
  --agent leaderboard/leaderboard/autoagents/human_agent.py \
  --checkpoint ./evaluation_results/cvci_benchmark.json
```

## Metrics and Result Processing

```bash
python tools/merge_route_json.py -f /path/to/json_folder/
python tools/ability_benchmark.py -r merge.json
python tools/efficiency_smoothness_benchmark.py -f merge.json -m /path/to/metric_folder/
```

## Scoring System

The final score is computed by weighted fusion of:

1. Bench2Drive route-level driving score.
2. CVCI scenario-aware score on interactive risk scenarios.

For the CVCI scenario-aware part:

- Scenario score starts from criterion-level evaluation aligned with scenario intent (for example, deceleration, avoidance, and safe resume).
- Safety gates/penalties are applied for severe violations (for example, collisions and critical infractions).
- Final scenario score balances safety, task completion, and behavior quality.

This protocol reduces over-rewarding of overly conservative "stop-only" policies.

## Data Download

Benchmark data is available at:

https://huggingface.co/datasets/55sleeper/CVCI_BENCHmark/tree/main

## CVCI 2026 Timeline

- Benchmark and data release: April 15, 2026.
- Paper + challenge result submission: July 1, 2026.
- Final result submission: September 1, 2026.

## License

All assets and code are under the repository license unless specified otherwise.
