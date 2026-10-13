import unittest
from simulator import PagingSimulator
from controller import allocate_frames_by_working_set
from controller import (
    allocate_frames_by_working_set,
    check_demand_feasibility,
)


class TestPagingSimulator(unittest.TestCase):

    def test_c3_overcommitted_demand_is_reported(self):
        result = check_demand_feasibility(
            {"P1": 6, "P2": 6},
            total_frames=8
        )

        self.assertFalse(result["feasible"])
        self.assertEqual(result["total_demand"], 12)
        self.assertEqual(result["total_frames"], 8)
        self.assertEqual(
            result["status"],
            "OVERCOMMITTED_DEMAND"
        )

    
    def test_first_reference_faults(self):
        sim = PagingSimulator({"P1": 2})
        r = sim.request("P1", 1)
        self.assertTrue(r.fault)
        self.assertEqual(sim.metrics()["page_faults"], 1)

    def test_repeat_reference_hits(self):
        sim = PagingSimulator({"P1": 2})
        sim.request("P1", 1)
        r = sim.request("P1", 1)
        self.assertTrue(r.hit)
        self.assertEqual(sim.metrics()["page_faults"], 1)

    def test_lru_eviction(self):
        sim = PagingSimulator({"P1": 3})
        for p in [1, 2, 3, 1]:
            sim.request("P1", p)
        r = sim.request("P1", 4)
        self.assertEqual(r.evicted_page, 2)
        self.assertEqual(sim.processes["P1"].pages.keys(), {1, 3, 4})

    def test_frame_allocator_preserves_capacity(self):
        result = allocate_frames_by_working_set({"P1": 5, "P2": 3}, 8)
        self.assertEqual(sum(result.values()), 8)
        self.assertTrue(all(v >= 1 for v in result.values()))


    def test_c1_fixed_vs_demand_fit_fault_totals(self):
        # Eight repetitions of each process's reference pattern.
        workload = {
            "P1": [1, 2] * 8,
            "P2": [1, 2, 3, 4, 5, 6] * 8,
        }

        # Policy A: fixed 4/4 allocation, with empty caches.
        fixed_sim = PagingSimulator({"P1": 4, "P2": 4})
        fixed_sim.run(workload)
        fixed_faults = fixed_sim.metrics()["page_faults"]

        # Policy B: demand-fit 2/6 allocation, also with empty caches.
        demand_sim = PagingSimulator({"P1": 2, "P2": 6})
        demand_sim.run(workload)
        demand_faults = demand_sim.metrics()["page_faults"]

        # Verify actual trace-derived results.
        self.assertEqual(fixed_sim.metrics()["references"], 64)
        self.assertEqual(demand_sim.metrics()["references"], 64)
        self.assertEqual(fixed_faults, 50)
        self.assertEqual(demand_faults, 8)

        # Verify that both policies conserve all eight frames.
        self.assertEqual(fixed_sim.total_frames, 8)
        self.assertEqual(demand_sim.total_frames, 8)

if __name__ == "__main__":
    unittest.main()
