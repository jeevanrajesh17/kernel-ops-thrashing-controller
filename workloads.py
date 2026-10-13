
"""Repeatable demonstration workloads."""


def normal_locality():
    return {"P1": [1, 2] * 6, "P2": [5, 6] * 6}


def memory_pressure():
    return {"P1": [1, 2, 3, 4] * 4, "P2": [5, 6, 7, 8] * 4}


def thrashing():
    return {"P1": [1, 2, 3, 4, 5] * 4, "P2": [6, 7, 8, 9, 10] * 4}


def asymmetric_workload():
    """P1 has a 2-page working set; P2 has a 6-page working set."""
    p1 = [1, 2] * 12
    p2 = [10, 11, 12, 13, 14, 15] * 4
    return {"P1": p1, "P2": p2}


def repeated_locality_phases():
    """C4: Each process changes from low to high demand, then vice versa.

    Phase A: P1 uses 2 pages; P2 uses 6 pages.
    Phase B: P1 uses 6 pages; P2 uses 2 pages.
    Each process makes 30 references in each phase.
    """
    p1_phase_a = [1, 2] * 15
    p2_phase_a = [10, 11, 12, 13, 14, 15] * 5

    p1_phase_b = [3, 4, 5, 6, 7, 8] * 5
    p2_phase_b = [16, 17] * 15

    return {
        "P1": p1_phase_a + p1_phase_b,
        "P2": p2_phase_a + p2_phase_b,
    }


SCENARIOS = {
    "Normal locality": normal_locality,
    "Memory pressure": memory_pressure,
    "Thrashing": thrashing,
    "Asymmetric demand (allocation demo)": asymmetric_workload,
    "Repeated locality phases (C4)": repeated_locality_phases,
}
