"""Repeatable demonstration workloads."""
def normal_locality():
    return {"P1":[1,2]*6,"P2":[5,6]*6}
def memory_pressure():
    return {"P1":[1,2,3,4]*4,"P2":[5,6,7,8]*4}
def thrashing():
    return {"P1":[1,2,3,4,5]*4,"P2":[6,7,8,9,10]*4}


def asymmetric_workload():
    """P1 has a 2-page working set; P2 has a 6-page working set."""
    p1 = [1, 2] * 12
    p2 = [10, 11, 12, 13, 14, 15] * 4
    return {"P1": p1, "P2": p2}


SCENARIOS={"Normal locality":normal_locality,"Memory pressure":memory_pressure,
           "Thrashing":thrashing,"Asymmetric demand (allocation demo)":asymmetric_workload}
