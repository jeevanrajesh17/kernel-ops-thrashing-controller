
"""Demand-paging simulator with LRU, frame reallocation, and process suspension."""

from dataclasses import dataclass, field
from collections import OrderedDict, deque
from typing import Dict, List, Optional, Tuple


@dataclass
class ProcessState:
    pid: str
    allocation: int
    pages: OrderedDict = field(default_factory=OrderedDict)
    faults: int = 0
    hits: int = 0
    references: int = 0
    recent: deque = field(default_factory=deque)
    suspended: bool = False


@dataclass
class StepResult:
    pid: str
    page: int
    hit: bool
    fault: bool
    evicted_page: Optional[int]
    resident_pages: List[Tuple[str, int]]


class PagingSimulator:
    def __init__(
        self,
        allocations: Dict[str, int],
        working_set_window: int = 8
    ):
        if not allocations:
            raise ValueError("At least one process is required.")

        if any(
            not isinstance(v, int) or isinstance(v, bool) or v < 1
            for v in allocations.values()
        ):
            raise ValueError("Each process must receive at least one frame.")

        if working_set_window < 1:
            raise ValueError("Working-set window must be positive.")

        self.processes = {
            pid: ProcessState(
                pid=pid,
                allocation=frames,
                recent=deque(maxlen=working_set_window)
            )
            for pid, frames in allocations.items()
        }

        self.total_frames = sum(allocations.values())
        self.trace: List[StepResult] = []

    def request(self, pid: str, page: int) -> StepResult:
        """Process one memory reference using per-process LRU."""
        proc = self.processes[pid]

        if proc.suspended:
            raise ValueError(
                f"Process {pid} is suspended and cannot request a page."
            )

        if proc.allocation < 1:
            raise ValueError(
                f"Process {pid} has no allocated frames."
            )

        proc.references += 1
        proc.recent.append(page)

        hit = page in proc.pages
        evicted = None

        if hit:
            proc.hits += 1
            proc.pages.move_to_end(page)
        else:
            proc.faults += 1

            if len(proc.pages) >= proc.allocation:
                evicted, _ = proc.pages.popitem(last=False)

            proc.pages[page] = None

        result = StepResult(
            pid=pid,
            page=page,
            hit=hit,
            fault=not hit,
            evicted_page=evicted,
            resident_pages=[
                (p.pid, pg)
                for p in self.processes.values()
                for pg in p.pages.keys()
            ]
        )

        self.trace.append(result)
        return result

    def run(self, workload):
        """Run page references in round-robin process order."""
        results = []
        process_ids = list(workload.keys())

        max_references = max(
            (len(pages) for pages in workload.values()),
            default=0
        )

        for i in range(max_references):
            for pid in process_ids:
                pages = workload[pid]

                if i < len(pages):
                    results.append(self.request(pid, pages[i]))

        return results

    def reallocate(
        self,
        allocations: Dict[str, int]
    ) -> Dict[str, dict]:
        """Change frame quotas while preserving total frame capacity.

        Active processes require at least one frame. Suspended processes
        may have zero frames. LRU pages are evicted when a quota shrinks.
        """
        if set(allocations) != set(self.processes):
            raise ValueError(
                "New allocations must include every process."
            )

        for pid, frames in allocations.items():
            if (
                not isinstance(frames, int)
                or isinstance(frames, bool)
            ):
                raise ValueError("Frame allocations must be integers.")

            minimum = 0 if self.processes[pid].suspended else 1

            if frames < minimum:
                raise ValueError(
                    f"{pid} must receive at least {minimum} frame(s)."
                )

        if sum(allocations.values()) != self.total_frames:
            raise ValueError(
                "Reallocation must preserve total frame capacity."
            )

        changes = {}

        for pid, new_count in allocations.items():
            proc = self.processes[pid]
            old_count = proc.allocation
            evicted = []

            while len(proc.pages) > new_count:
                page, _ = proc.pages.popitem(last=False)
                evicted.append(page)

            proc.allocation = new_count

            changes[pid] = {
                "old_frames": old_count,
                "new_frames": new_count,
                "evicted_pages": evicted
            }

        return changes

    def suspend_process(self, pid) -> dict:
        """Suspend a process and release its resident pages and frames."""
        proc = self.processes[pid]

        if proc.suspended:
            raise ValueError(f"Process {pid} is already suspended.")

        reclaimed_pages = list(proc.pages.keys())
        reclaimed_frames = proc.allocation

        proc.pages.clear()
        proc.allocation = 0
        proc.suspended = True

        return {
            "pid": pid,
            "reclaimed_frames": reclaimed_frames,
            "evicted_pages": reclaimed_pages,
            "references_completed": proc.references,
            "status": "SUSPENDED"
        }

    def resume_process(self, pid, allocation: int) -> dict:
        """Resume a suspended process with empty resident memory.

        Reference counts and working-set history are preserved.
        Evicted resident pages are not restored.
        """
        proc = self.processes[pid]

        if not proc.suspended:
            raise ValueError(f"Process {pid} is not suspended.")

        if (
            not isinstance(allocation, int)
            or isinstance(allocation, bool)
            or allocation < 1
        ):
            raise ValueError(
                "A resumed process must receive at least one frame."
            )

        allocated_elsewhere = sum(
            p.allocation
            for other_pid, p in self.processes.items()
            if other_pid != pid
        )

        if allocated_elsewhere + allocation > self.total_frames:
            raise ValueError(
                "Resume allocation exceeds total frame capacity."
            )

        proc.allocation = allocation
        proc.suspended = False

        return {
            "pid": pid,
            "allocation": allocation,
            "references_completed": proc.references,
            "resident_pages": list(proc.pages.keys()),
            "status": "RUNNING"
        }

    def metrics(self) -> dict:
        """Return aggregate and per-process paging metrics."""
        refs = sum(p.references for p in self.processes.values())
        faults = sum(p.faults for p in self.processes.values())
        hits = sum(p.hits for p in self.processes.values())

        return {
            "references": refs,
            "page_faults": faults,
            "hits": hits,
            "fault_rate": faults / refs * 100 if refs else 0.0,
            "per_process": {
                pid: {
                    "allocation": proc.allocation,
                    "references": proc.references,
                    "faults": proc.faults,
                    "hits": proc.hits,
                    "working_set": len(set(proc.recent)),
                    "resident_pages": list(proc.pages.keys()),
                    "suspended": proc.suspended
                }
                for pid, proc in self.processes.items()
            }
        }

    def frame_map(self) -> List[dict]:
        """Return exactly total_frames entries, including free frames."""
        cells = []

        for pid, proc in self.processes.items():
            resident = list(proc.pages.keys())

            for i in range(proc.allocation):
                page = resident[i] if i < len(resident) else None

                cells.append({
                    "frame": len(cells),
                    "pid": pid if page is not None else None,
                    "page": page
                })

        while len(cells) < self.total_frames:
            cells.append({
                "frame": len(cells),
                "pid": None,
                "page": None
            })

        return cells
