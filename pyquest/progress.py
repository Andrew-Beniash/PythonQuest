"""Saves stars and unfinished code between play sessions."""

import json
import os
from pathlib import Path

from .jobs import GOLD_PER_STAR, JOBS
from .levels import LEVELS, MAX_STARS

DEFAULT_PATH = Path(os.environ.get("PYTHON_QUEST_SAVE", Path.home() / ".python_quest" / "save.json"))

RANKS = [
    (0, "Byte Beginner"),
    (9, "Print Pro"),
    (21, "Variable Voyager"),
    (33, "Logic Ranger"),
    (45, "Loop Master"),
    (57, "List Wrangler"),
    (MAX_STARS, "Python Hero"),
]


def stars_for(hints_used):
    """3 stars with no hints, 2 with one, 1 once the answer has been revealed."""
    return max(1, 3 - hints_used)


class Progress:
    def __init__(self, path=DEFAULT_PATH):
        self.path = Path(path)
        self.stars = {}
        self.drafts = {}
        self.load()

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        self.stars = {k: int(v) for k, v in data.get("stars", {}).items()}
        self.drafts = dict(data.get("drafts", {}))

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"stars": self.stars, "drafts": self.drafts}, indent=2), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            pass  # progress is a nice-to-have; never crash the game over it

    def best(self, level_id):
        return self.stars.get(level_id, 0)

    def record(self, level_id, stars):
        """Store a result. Returns True when it beats the previous best."""
        improved = stars > self.best(level_id)
        if improved:
            self.stars[level_id] = stars
            self.save()
        return improved

    def set_draft(self, level_id, code):
        self.drafts[level_id] = code

    def is_complete(self, index):
        return LEVELS[index].id in self.stars

    def is_unlocked(self, index):
        return index == 0 or self.is_complete(index - 1)

    def next_index(self):
        for index in range(len(LEVELS)):
            if not self.is_complete(index):
                return index
        return len(LEVELS) - 1

    @property
    def total_stars(self):
        return sum(self.stars.get(level.id, 0) for level in LEVELS)

    @property
    def gold(self):
        """Odd jobs pay gold for their best result, so replaying can't farm it."""
        return GOLD_PER_STAR * sum(self.stars.get(job.id, 0) for job in JOBS)

    def is_done(self, level_id):
        return level_id in self.stars

    @property
    def started(self):
        return bool(self.stars)

    def rank(self):
        title = RANKS[0][1]
        for needed, name in RANKS:
            if self.total_stars >= needed:
                title = name
        return title

    def reset(self):
        self.stars.clear()
        self.drafts.clear()
        self.save()
