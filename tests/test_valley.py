import os
import tempfile
import unittest
from collections import deque

from pyquest.jobs import JOBS
from pyquest.levels import LEVELS, WORLDS
from pyquest.progress import Progress
from pyquest.worldmap import GATES, START, WorldMap, open_gates

NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def reachable(world, gates):
    seen, queue = {START}, deque([START])
    while queue:
        x, y = queue.popleft()
        for dx, dy in NEIGHBOURS:
            nxt = (x + dx, y + dy)
            if nxt not in seen and not world.is_blocked(*nxt, gates):
                seen.add(nxt)
                queue.append(nxt)
    return seen


def can_talk_to(tiles, x, y):
    return any((x + dx, y + dy) in tiles for dx, dy in NEIGHBOURS)


class ValleyLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = WorldMap()

    def test_one_villager_per_level(self):
        self.assertEqual(sorted(v.level_id for v in self.world.villagers), sorted(lv.id for lv in LEVELS))

    def test_villagers_live_in_their_world(self):
        for v in self.world.villagers:
            zone = self.world.zone_at(v.x, v.y)
            self.assertIs(WORLDS[zone], LEVELS[v.level_index].world, v.name)

    def test_start_is_walkable(self):
        self.assertFalse(self.world.is_blocked(*START))

    def test_nothing_solid_overlaps(self):
        seen = {}
        for prop in self.world.props:
            if prop.solid:
                for tile in prop.tiles():
                    self.assertNotIn(tile, seen, f"{prop.kind} overlaps {seen.get(tile)} at {tile}")
                    seen[tile] = prop.kind
        for v in self.world.villagers:
            self.assertNotIn((v.x, v.y), seen, v.name)
            self.assertNotEqual(self.world.ground[v.y][v.x], "water", v.name)

    def test_everyone_reachable_when_gates_open(self):
        tiles = reachable(self.world, set(GATES))
        for v in self.world.villagers:
            self.assertTrue(can_talk_to(tiles, v.x, v.y), v.name)
        for sign in self.world.signs:
            self.assertTrue(can_talk_to(tiles, sign.x, sign.y), sign)

    def test_odd_jobs_sit_on_reachable_props(self):
        tiles = reachable(self.world, set(GATES))
        for job in JOBS:
            prop = self.world.prop_at(job.x, job.y)
            self.assertIsNotNone(prop, job.id)
            self.assertEqual(prop.kind, job.prop, job.id)
            self.assertTrue(can_talk_to(tiles, job.x, job.y), job.id)

    def test_odd_jobs_unlock_from_their_own_or_an_earlier_world(self):
        level_ids = [lv.id for lv in LEVELS]
        for job in JOBS:
            self.assertIn(job.requires, level_ids, job.id)
            required_world = WORLDS.index(LEVELS[level_ids.index(job.requires)].world)
            self.assertLessEqual(required_world, WORLDS.index(job.level.world), job.id)
            zone = self.world.zone_at(job.x, job.y)
            self.assertIs(WORLDS[zone], job.level.world, job.id)

    def test_closed_gates_keep_you_in_the_first_zone(self):
        zones = {self.world.zone_at(*tile) for tile in reachable(self.world, set())}
        self.assertEqual(zones - {None}, {0})

    def test_each_gate_opens_exactly_one_more_zone(self):
        for opened in range(1, len(WORLDS)):
            zones = {self.world.zone_at(*t) for t in reachable(self.world, set(range(1, opened + 1)))}
            self.assertEqual(zones - {None}, set(range(opened + 1)))


class GateProgressTests(unittest.TestCase):
    def test_gate_opens_after_finishing_a_world(self):
        with tempfile.TemporaryDirectory() as tmp:
            progress = Progress(os.path.join(tmp, "save.json"))
            self.assertEqual(open_gates(progress), set())
            for level in LEVELS[:3]:
                progress.record(level.id, 3)
            self.assertEqual(open_gates(progress), set())
            progress.record(LEVELS[3].id, 1)
            self.assertEqual(open_gates(progress), {1})


if __name__ == "__main__":
    unittest.main()
