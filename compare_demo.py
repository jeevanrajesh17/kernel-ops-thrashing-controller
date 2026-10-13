
from simulator import PagingSimulator
from controller import allocate_frames_by_working_set
from workloads import asymmetric_workload

workload = asymmetric_workload()
total_frames = 8

# Baseline: split frames equally.
fixed = {"P1": 4, "P2": 4}

# Adaptive: allocate according to working-set demand.
adaptive = allocate_frames_by_working_set(
    {"P1": 2, "P2": 6},
    total_frames,
)

for label, allocation in [
    ("Fixed", fixed),
    ("Adaptive", adaptive),
]:
    sim = PagingSimulator(allocation)
    sim.run(workload)
    metrics = sim.metrics()

    print(f"\n{label} allocation: {allocation}")
    print(f"Page faults: {metrics['page_faults']}")
    print(f"Fault rate: {metrics['fault_rate']:.1f}%")
