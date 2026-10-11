import unittest
from simulator import PagingSimulator
from controller import allocate_frames_by_working_set


class TestPagingSimulator(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
