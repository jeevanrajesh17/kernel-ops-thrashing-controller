
"""Adaptive frame allocation based on working-set demand."""

def allocate_frames_by_working_set(
    working_sets,
    total_frames,
    minimum_per_process=1
):
    if not working_sets:
        return {}

    pids = list(working_sets)

    if total_frames < len(pids) * minimum_per_process:
        raise ValueError("Not enough frames to satisfy minimum allocations.")

    if total_frames < 1 or minimum_per_process < 1:
        raise ValueError("Frame counts must be positive.")

    demand = {
        pid: max(minimum_per_process, int(working_sets[pid]))
        for pid in pids
    }

    allocation = {pid: minimum_per_process for pid in pids}
    remaining = total_frames - sum(allocation.values())

    while remaining > 0:
        eligible = [
            pid for pid in pids
            if allocation[pid] < demand[pid]
        ]

        if not eligible:
            # Demand is satisfied or capped. Distribute remaining frames
            # fairly so the total always equals total_frames.
            for i in range(remaining):
                allocation[pids[i % len(pids)]] += 1
            break

        # Prioritize the process with the greatest unmet working-set demand.
        pid = max(
            eligible,
            key=lambda p: demand[p] - allocation[p]
        )

        allocation[pid] += 1
        remaining -= 1

    return allocation
