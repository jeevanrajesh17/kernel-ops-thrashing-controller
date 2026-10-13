
"""C5: Process suspension and resumption with preserved reference progress."""

from simulator import PagingSimulator


def run_c5_demo():
    # Six physical frames in total.
    # Initially, P1 gets 2 frames and P2 gets 4 frames.
    sim = PagingSimulator(
        {"P1": 2, "P2": 4},
        working_set_window=8
    )

    workload = {
        "P1": [1, 2, 1, 2, 1, 2],
        "P2": [10, 11, 12, 13, 14, 15],
    }

    # Each cursor stores the index of the next reference to execute.
    cursor = {"P1": 0, "P2": 0}
    events = []

    # --------------------------------------------------
    # STEP 1: P2 executes its first three references.
    # Pages accessed: 10, 11, 12
    # --------------------------------------------------
    for _ in range(3):
        page = workload["P2"][cursor["P2"]]
        result = sim.request("P2", page)
        cursor["P2"] += 1

        events.append({
            "event": "P2 memory reference",
            "page": page,
            "result": "FAULT" if result.fault else "HIT",
            "cursor": cursor["P2"],
        })

    # --------------------------------------------------
    # STEP 2: Suspend P2 after its third reference.
    # Its resident pages are released.
    # Its cursor remains at index 3.
    # --------------------------------------------------
    suspension = sim.suspend_process("P2")

    events.append({
        "event": "P2 suspended",
        "details": suspension,
        "cursor": cursor["P2"],
    })

    # --------------------------------------------------
    # STEP 3: P1 temporarily receives all six frames.
    # P2 has zero frames while suspended.
    # --------------------------------------------------
    changes = sim.reallocate({
        "P1": 6,
        "P2": 0,
    })

    events.append({
        "event": "Frames reassigned while P2 is suspended",
        "details": changes,
        "allocations": {
            pid: proc.allocation
            for pid, proc in sim.processes.items()
        },
    })

    # P1 continues making memory references.
    for _ in range(3):
        page = workload["P1"][cursor["P1"]]
        result = sim.request("P1", page)
        cursor["P1"] += 1

        events.append({
            "event": "P1 reference while P2 is suspended",
            "page": page,
            "result": "FAULT" if result.fault else "HIT",
            "cursor": cursor["P1"],
        })

    # --------------------------------------------------
    # STEP 4: Prepare two frames for P1 and four for P2.
    # P2 is still suspended, so assigning it four frames
    # here does not resume it yet.
    # --------------------------------------------------
    changes = sim.reallocate({
        "P1": 2,
        "P2": 4,
    })

    events.append({
        "event": "Frames prepared for P2 resumption",
        "details": changes,
    })

    # --------------------------------------------------
    # STEP 5: Resume P2.
    # Its reference count remains 3.
    # Its resident pages remain empty.
    # --------------------------------------------------
    resumption = sim.resume_process("P2", allocation=4)

    events.append({
        "event": "P2 resumed",
        "details": resumption,
        "cursor": cursor["P2"],
    })

    # --------------------------------------------------
    # STEP 6: Continue from P2's fourth reference.
    # The next page must be 13, not 10.
    # --------------------------------------------------
    page = workload["P2"][cursor["P2"]]
    result = sim.request("P2", page)
    cursor["P2"] += 1

    events.append({
        "event": "P2 resumed memory reference",
        "page": page,
        "result": "FAULT" if result.fault else "HIT",
        "cursor": cursor["P2"],
    })

    # Return all results for display and testing.
    return {
        "events": events,
        "metrics": sim.metrics(),
        "cursor": cursor,
        "suspended": {
            pid: proc.suspended
            for pid, proc in sim.processes.items()
        },
        "allocations": {
            pid: proc.allocation
            for pid, proc in sim.processes.items()
        },
        "resident_pages": {
            pid: list(proc.pages.keys())
            for pid, proc in sim.processes.items()
        },
        "total_frames": sim.total_frames,
        "frame_map": sim.frame_map(),
    }


if __name__ == "__main__":
    result = run_c5_demo()

    print("=" * 60)
    print("C5: SUSPEND AND RESUME DEMONSTRATION")
    print("=" * 60)

    for event in result["events"]:
        print(f"\nEvent: {event['event']}")
        for key, value in event.items():
            if key != "event":
                print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("FINAL STATE")
    print("=" * 60)
    print("Reference cursors:", result["cursor"])
    print("Allocations:", result["allocations"])
    print("Suspended processes:", result["suspended"])
    print("Resident pages:", result["resident_pages"])
    print("Total physical frames:", result["total_frames"])
    print("Frame map:", result["frame_map"])
    print("Metrics:", result["metrics"])

    # Explicit checks for the challenge requirements.
    assert result["cursor"]["P2"] == 4
    assert result["metrics"]["per_process"]["P2"]["references"] == 4
    assert result["allocations"] == {"P1": 2, "P2": 4}
    assert result["suspended"] == {"P1": False, "P2": False}
    assert result["total_frames"] == 6
    assert len(result["frame_map"]) == 6

    print("\nC5 DEMONSTRATION PASSED")
