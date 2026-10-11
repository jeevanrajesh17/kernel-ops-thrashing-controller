"""Demand-paging simulator with LRU and live frame reallocation."""
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

@dataclass
class StepResult:
    pid: str
    page: int
    hit: bool
    fault: bool
    evicted_page: Optional[int]
    resident_pages: List[Tuple[str, int]]

class PagingSimulator:
    def __init__(self, allocations: Dict[str, int], working_set_window: int = 8):
        if not allocations or any(v < 1 for v in allocations.values()):
            raise ValueError("Each process must receive at least one frame.")
        self.processes = {
            pid: ProcessState(pid, int(frames), recent=deque(maxlen=working_set_window))
            for pid, frames in allocations.items()
        }
        self.total_frames = sum(allocations.values())
        self.trace: List[StepResult] = []

    def request(self, pid: str, page: int) -> StepResult:
        proc = self.processes[pid]
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
        result = StepResult(pid, page, hit, not hit, evicted,
            [(p.pid, pg) for p in self.processes.values() for pg in p.pages.keys()])
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
                    result = self.request(pid, pages[i])
                    results.append(result)

        return results



    def reallocate(self, allocations: Dict[str, int]) -> Dict[str, dict]:
        """Change per-process frame quotas while preserving total frame capacity.
        If a process receives fewer frames than resident pages, evict its LRU pages.
        """
        if set(allocations) != set(self.processes):
            raise ValueError("New allocations must include every process.")
        if any(v < 1 for v in allocations.values()):
            raise ValueError("Every process must keep at least one frame.")
        if sum(allocations.values()) != self.total_frames:
            raise ValueError("Reallocation must preserve total frame capacity.")
        changes = {}
        for pid, new_count in allocations.items():
            proc = self.processes[pid]
            old_count = proc.allocation
            evicted = []
            while len(proc.pages) > new_count:
                page, _ = proc.pages.popitem(last=False)
                evicted.append(page)
            proc.allocation = new_count
            changes[pid] = {"old_frames": old_count, "new_frames": new_count,
                            "evicted_pages": evicted}
        return changes

    def metrics(self) -> dict:
        refs=sum(p.references for p in self.processes.values())
        faults=sum(p.faults for p in self.processes.values())
        return {"references":refs,"page_faults":faults,"hits":sum(p.hits for p in self.processes.values()),
                "fault_rate":faults/refs*100 if refs else 0.0,
                "per_process":{pid:{"allocation":p.allocation,"references":p.references,
                    "faults":p.faults,"hits":p.hits,"working_set":len(set(p.recent)),
                    "resident_pages":list(p.pages.keys())} for pid,p in self.processes.items()}}

    def frame_map(self) -> List[dict]:
        cells=[]
        for pid,proc in self.processes.items():
            resident=list(proc.pages.keys())
            for i in range(proc.allocation):
                page=resident[i] if i<len(resident) else None
                cells.append({"frame":len(cells),"pid":pid if page is not None else None,"page":page})
        return cells

    
