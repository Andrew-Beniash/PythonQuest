import unittest

from pyquest.pixelart import OUT, character
from pyquest.worldmap import PLAYER_LOOK


def eyes(sprite):
    """Dark pixels with face on both sides - outline pixels always have empty space on one side."""
    def face(x, y):
        return sprite.get(x, y) not in (None, OUT)

    return {(x, y) for y in range(3, 12) for x in range(1, sprite.w - 1)
            if sprite.get(x, y) == OUT and face(x - 1, y) and face(x + 1, y)}


class GazeTests(unittest.TestCase):
    def test_eyes_follow_the_gaze(self):
        for facing in ("down", "left", "right"):
            ahead = eyes(character(PLAYER_LOOK, facing))
            self.assertTrue(ahead, facing)
            for gaze in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
                with self.subTest(facing=facing, gaze=gaze):
                    moved = eyes(character(PLAYER_LOOK, facing, 0, gaze))
                    shifted = {(x + gaze[0], y + gaze[1]) for x, y in ahead}
                    self.assertTrue(moved, "eyes disappeared")
                    self.assertTrue(moved <= shifted, f"{sorted(moved)} vs {sorted(shifted)}")

    def test_gaze_only_moves_the_eyes(self):
        plain = character(PLAYER_LOOK, "down")
        looking = character(PLAYER_LOOK, "down", 0, (1, 1))
        changed = {(x, y) for y in range(plain.h) for x in range(plain.w) if plain.get(x, y) != looking.get(x, y)}
        self.assertTrue(changed)
        self.assertTrue(all(5 <= y <= 10 for _x, y in changed), changed)


if __name__ == "__main__":
    unittest.main()
