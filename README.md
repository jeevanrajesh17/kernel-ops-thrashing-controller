# Kernel Ops: Thrashing-Aware Virtual Memory Controller

A user-space Operating Systems simulation developed for hackathon problem statement **OSH019**. The project demonstrates demand paging, Least Recently Used (LRU) page replacement, working-set estimation, thrashing detection, and adaptive physical-frame allocation.

The dashboard allows users to experiment with different memory workloads and compare fixed allocation against a working-set-based adaptive allocation policy.

## Features

- **Demand paging:** Simulates page requests and generates page faults when requested pages are not resident in memory.
- **LRU page replacement:** Evicts the least recently used resident page when a process reaches its frame limit.
- **Working-set estimation:** Estimates each process's recent page demand.
- **Thrashing detection:** Uses a rolling page-fault rate and working-set pressure to identify sustained memory stress.
- **Live adaptive intervention:** Reallocates frame quotas during a simulation after thrashing is detected and records the intervention.
- **Fixed-versus-adaptive comparison:** Replays the same workload under fixed and suggested adaptive allocations.
- **RAM frame heatmap:** Visualizes occupied and free simulated physical frames.
- **Workload scenarios:** Includes normal locality, memory pressure, thrashing, and asymmetric demand.
- **Explainable intervention log:** Displays the detection reason, allocation change, and page evictions.

## Technology Stack

- Python
- Streamlit
- Pandas
- Plotly
- Python `unittest` framework

## Requirements

- Python 3.10 or newer
- Dependencies listed in `requirements.txt`

## Run Locally

1. Open a terminal in the project directory.
2. Install the dependencies:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. Start the dashboard:

   ```bash
   python3 -m streamlit run app.py
   ```

4. Open the local URL displayed in the terminal, usually `http://localhost:8501`.

5. Select a workload, configure the number of physical frames and detection parameters, and click **Run simulation**.

## Run Tests

Run the unit tests from the project directory:

```bash
python3 -m unittest discover -s tests -v
```

The current test suite covers first-reference page faults, repeated-reference hits, LRU eviction, and frame-allocation capacity.

## Architecture

- `app.py` — Streamlit dashboard, simulation orchestration, visualizations, and intervention log.
- `simulator.py` — Demand-paging engine, per-process page replacement, frame state, and metrics.
- `detector.py` — Working-set pressure and rolling page-fault-rate detection.
- `controller.py` — Working-set-based adaptive frame-allocation algorithm.
- `workloads.py` — Preset page-reference workloads.
- `metrics.py` — Supporting metrics, if used by the current implementation.
- `tests/` — Unit tests for core simulator behavior.

## Demonstration Results

For the asymmetric-demand workload with eight simulated physical frames, one observed comparison produced:

| Policy | Page faults | Fault rate |
|---|---:|---:|
| Fixed allocation | 26 | 54.2% |
| Adaptive allocation | 8 | 16.7% |

This represents a **69.2% reduction in page faults for that workload**. Results depend on the workload, frame count, and simulation parameters; this is not a guarantee of improvement for every scenario.

The live intervention demonstration also shows a frame-quota change from `P1: 4, P2: 4` to `P1: 3, P2: 5` after thrashing is detected, with eviction details recorded in the intervention log.

## Scope and Limitations

This is a **user-space simulation**. It does not control the host computer's actual RAM, modify kernel page tables, or manage real operating-system processes.

The live intervention changes simulated per-process frame quotas and may evict pages to enforce those quotas. The fixed-versus-adaptive comparison separately replays the workload from a clean initial state using the selected allocations; it is not a direct comparison of the live run's mixed-allocation history.

The prototype is intended to demonstrate memory-management concepts and compare allocation strategies in controlled workloads.
