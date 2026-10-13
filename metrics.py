"""Baseline-versus-adaptive replay helpers."""
from simulator import PagingSimulator


def run_policy(workload, allocations):
    sim = PagingSimulator(allocations)
    sim.run(workload)
    return sim.metrics(), sim.frame_map()


def compare_policies(workload, fixed_allocations, adaptive_allocations):
    fixed_metrics, _ = run_policy(workload, fixed_allocations)
    adaptive_metrics, _ = run_policy(workload, adaptive_allocations)
    return {"Fixed allocation": fixed_metrics, "Adaptive allocation": adaptive_metrics}
