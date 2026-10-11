"""Detect persistent memory pressure using rolling faults and working-set demand."""
from collections import deque

class ThrashingDetector:
    def __init__(self, window=8, fault_threshold=0.60, persistence_windows=2):
        self.window=window
        self.fault_threshold=fault_threshold
        self.persistence_windows=persistence_windows
        self.faults=deque(maxlen=window)
        self.high_pressure_count=0
        self.status="NORMAL"

    def observe(self, fault, total_working_set, frame_capacity):
        self.faults.append(bool(fault))
        rate=sum(self.faults)/len(self.faults) if self.faults else 0.0
        demand_exceeds=total_working_set>frame_capacity
        high=(len(self.faults)==self.window and rate>=self.fault_threshold and demand_exceeds)
        self.high_pressure_count=self.high_pressure_count+1 if high else 0
        if self.high_pressure_count>=self.persistence_windows:
            self.status="THRASHING DETECTED"
        elif demand_exceeds and rate>=self.fault_threshold:
            self.status="MEMORY PRESSURE"
        else:
            self.status="NORMAL"
        return {"status":self.status,"rolling_fault_rate":rate*100,
                "total_working_set":total_working_set,"frame_capacity":frame_capacity,
                "demand_exceeds_capacity":demand_exceeds}
