"""Python Valley: the walkable overworld, its six zones, gates, signs and villagers.

Pure data (no Tk), so it can be tested. Coordinates are in tiles; (0, 0) is top-left.
Each villager hands out one level, matched by level id.
"""

import random
from dataclasses import dataclass

from .levels import LEVELS, WORLDS

COLS, ROWS = 48, 33

# interior tile rectangle (x1, y1, x2, y2) of each world's zone, in WORLDS order
ZONES = [
    (2, 2, 15, 15),     # Print Plains     - the farm
    (17, 2, 30, 15),    # Variable Valley  - the village square
    (32, 2, 45, 15),    # Logic Lagoon     - the lake
    (32, 17, 45, 30),   # Loop Mountain    - rocky hills
    (17, 17, 30, 30),   # List Labs        - the market
    (2, 17, 15, 30),    # Function Forge   - the mine
]
DARK_ZONES = {3, 5}

# gate tiles in the tree walls; a gate opens once its world is unlocked
GATES = {
    1: ((16, 8), (16, 9)),
    2: ((31, 8), (31, 9)),
    3: ((38, 16), (39, 16)),
    4: ((31, 23), (31, 24)),
    5: ((16, 23), (16, 24)),
}

START = (5, 7)  # in front of the farmhouse door

# kind: (footprint width, footprint height, solid)
PROP_SIZES = {
    "house": (5, 3, True), "house_blue": (5, 3, True), "house_green": (5, 3, True),
    "well": (2, 1, True), "boulder": (2, 1, True), "furnace": (2, 1, True), "mine": (3, 2, True),
    "stall": (3, 1, True), "stall_blue": (3, 1, True), "stall_green": (3, 1, True),
    "crop0": (1, 1, False), "crop1": (1, 1, False), "crop2": (1, 1, False), "crop3": (1, 1, False),
    "lily": (1, 1, False), "lily_flower": (1, 1, False),
}
for _kind in ("oak", "pine", "bush", "rock", "fence", "crate", "barrel", "lamp", "sign", "mailbox",
              "scarecrow", "anvil"):
    PROP_SIZES[_kind] = (1, 1, True)


@dataclass
class Prop:
    kind: str
    x: int
    y: int

    @property
    def size(self):
        return PROP_SIZES[self.kind][:2]

    @property
    def solid(self):
        return PROP_SIZES[self.kind][2]

    def tiles(self):
        w, h = self.size
        return [(self.x + dx, self.y + dy) for dy in range(h) for dx in range(w)]


@dataclass
class Villager:
    level_id: str
    name: str
    x: int
    y: int
    look: dict
    greeting: str

    @property
    def level_index(self):
        return next(i for i, lv in enumerate(LEVELS) if lv.id == self.level_id)


@dataclass
class Sign:
    x: int
    y: int
    world: int   # the world this sign points to (None for the welcome sign)


# ------------------------------------------------------------------ villagers

HAIRS = ["#3b2414", "#6b3e1e", "#c26a2b", "#e8c066", "#2a2a35", "#9b9b9b", "#7a3f8f", "#d65a5a"]
SHIRTS = ["#d9453b", "#3f8fd0", "#4f9a3c", "#e0a020", "#8048b8", "#e07a9a", "#2f9e9a", "#f0f0e0",
          "#d0662a", "#5a6fd0"]
PANTS = ["#4a5a8a", "#5e3a1c", "#3d3a40", "#6b7a3a", "#7a4b6b"]
STYLES = ["short", "long", "spiky", "short", "long"]

PLAYER_LOOK = {"skin": "#f6cfa4", "hair": "#8a4b22", "shirt": "#3f8fd0", "pants": "#4a5a8a",
               "shoes": "#5e3a1c", "style": "short"}

# level id, name, tile position, greeting
_VILLAGERS = [
    ("hello", "Hazel", (4, 11), "Morning, neighbour! My little robot Pixel just woke up, but it can't say a word. "
                                "Can you teach it to talk?"),
    ("countdown_chant", "Otto", (7, 11), "I'm racing a snail today! I need someone to shout the countdown. "
                                         "Can Pixel do it?"),
    ("calculator", "Juniper", (13, 10), "My sums never come out right. Is it true Python can do math faster "
                                        "than me?"),
    ("echo", "Bram", (14, 13), "Have you been to Echo Cave? Ha... ha... ha... Can you make Pixel echo like that?"),
    ("name_tag", "Rosa", (20, 11), "I keep forgetting my new friend's name! Could you store it somewhere safe?"),
    ("coins", "Felix", (22, 13), "I found some coins... and then MORE coins! Help me keep count?"),
    ("badge", "Marigold", (27, 11), "The robot party is tonight and nobody has a name badge yet!"),
    ("birthday", "Quinn", (26, 14), "My birthday card machine only speaks in text. Can you help it do math?"),
    ("sunny", "Willow", (40, 3), "Should I go out to play? It depends on the weather... Can Pixel decide for me?"),
    ("hot_or_not", "Theo", (34, 11), "Hot or cool? My thermometer just beeps at me. Teach it to give advice!"),
    ("medals", "Ivy", (36, 14), "The Robot Games need a medal machine. Gold, silver, bronze!"),
    ("ticket", "Rowan", (43, 9), "Welcome to the Roller Coaster of Doom! Only riders with a ticket who are "
                                 "tall enough may ride."),
    ("hop", "Clover", (36, 19), "Boing! I taught Pixel to hop once. Can you make it hop again and again?"),
    ("liftoff", "Basil", (42, 20), "My cardboard rocket is ready. All it needs is a proper countdown!"),
    ("treasure_sum", "Fern", (35, 27), "The treasure stairs have coins on every step. How many coins in total?"),
    ("power_up", "Moss", (43, 27), "Pixel's battery doubles every second up here. Let's watch it charge!"),
    ("snacks", "Poppy", (21, 20), "Road trip snacks! Can you pack them all into one list?"),
    ("backpack", "Cedar", (25, 20), "Never go on an adventure without a map. Help me pack my bag!"),
    ("roll_call", "Sage", (20, 27), "My crew is here for the mission. Could you greet every one of them?"),
    ("biggest_gem", "Dot", (27, 27), "I dug up a pile of gems! Which one is the biggest?"),
    ("greet", "Elm", (13, 20), "Welcome to the Forge, where we craft our own commands. Your first spell: "
                               "a greeting!"),
    ("double", "Wren", (8, 20), "This cloning machine doubles everything. Can you write its program?"),
    ("even", "Flint", (11, 28), "My dance moves only work on even beats. Can you tell even from odd?"),
    ("fizzbuzz", "Granny Gears", (7, 28), "So, you made it to the deepest corner of the valley. Only a true hero "
                                          "can beat my FizzBuzz game!"),
]


def _look(i, name):
    look = {
        "skin": ["#f6cfa4", "#e8b48a", "#c98d5f", "#9a6440", "#704428"][(i * 3) % 5],
        "hair": HAIRS[(i * 5) % len(HAIRS)],
        "shirt": SHIRTS[(i * 7) % len(SHIRTS)],
        "pants": PANTS[i % len(PANTS)],
        "style": STYLES[(i * 2) % len(STYLES)],
    }
    if i % 6 == 1:
        look["hat"] = "#e0b04a"
    if name == "Granny Gears":
        look.update(hair="#d9d4cc", shirt="#8048b8", pants="#5e3a6b", style="long", hat=None)
    return look


# ------------------------------------------------------------------ the map


class WorldMap:
    def __init__(self):
        self.ground = [["grass"] * COLS for _ in range(ROWS)]
        self.variant = [[0] * COLS for _ in range(ROWS)]
        self.props = []
        self.blocked = set()
        self.villagers = []
        self.signs = []
        self.gate_tiles = {tile: world for world, tiles in GATES.items() for tile in tiles}
        self._build()

    # queries ----------------------------------------------------------------
    def in_bounds(self, x, y):
        return 0 <= x < COLS and 0 <= y < ROWS

    def zone_at(self, x, y):
        for index, (x1, y1, x2, y2) in enumerate(ZONES):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return index
        return None

    def grass_kind(self, x, y):
        zone = self.zone_at(x, y)
        return "grass_dark" if zone in DARK_ZONES else "grass"

    def is_blocked(self, x, y, open_gates=()):
        if not self.in_bounds(x, y) or self.ground[y][x] == "water" or (x, y) in self.blocked:
            return True
        world = self.gate_tiles.get((x, y))
        return world is not None and world not in open_gates

    def prop_at(self, x, y):
        return next((p for p in self.props if (x, y) in p.tiles()), None)

    def villager_for(self, level_id):
        return next(v for v in self.villagers if v.level_id == level_id)

    # building ---------------------------------------------------------------
    def _fill(self, kind, x1, y1, x2, y2):
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.ground[y][x] = kind

    def _add(self, kind, x, y):
        prop = Prop(kind, x, y)
        self.props.append(prop)
        if prop.solid:
            self.blocked.update(prop.tiles())
        return prop

    def _build(self):
        rng = random.Random("python-valley")
        for zone in DARK_ZONES:
            self._fill("grass_dark", *ZONES[zone])

        # the main road: along the top, down the east side, back along the bottom
        self._fill("path", 4, 8, 39, 9)
        self._fill("path", 38, 8, 39, 24)
        self._fill("path", 4, 23, 39, 24)

        self._build_farm(rng)
        self._build_village()
        self._build_lake(rng)
        self._build_mountain()
        self._build_market()
        self._build_forge()
        self._build_walls(rng)

        for i, (level_id, name, (x, y), greeting) in enumerate(_VILLAGERS):
            self.villagers.append(Villager(level_id, name, x, y, _look(i, name), greeting))
            self.blocked.add((x, y))
        for sign in self.signs:
            self.blocked.add((sign.x, sign.y))
        self._scatter(rng)

        for y in range(ROWS):
            for x in range(COLS):
                roll = rng.random()
                if self.ground[y][x] in ("grass", "grass_dark") and roll < 0.12:
                    self.variant[y][x] = rng.choice([4, 5])
                else:
                    self.variant[y][x] = rng.randrange(4)

    def _build_farm(self, rng):
        self._add("house", 3, 4)
        self.ground[7][5] = "path"
        self._add("mailbox", 7, 7)
        self.signs.append(Sign(3, 7, None))
        self._fill("soil", 10, 3, 14, 6)
        self._add("scarecrow", 12, 4)
        for y in range(3, 7):
            for x in range(10, 15):
                if (x, y) != (12, 4):
                    self._add(f"crop{rng.randrange(4)}", x, y)
        self._fill("water", 9, 12, 12, 14)
        for x in range(9, 13):
            self._add("fence", x, 15)
        self._add("oak", 3, 14)
        self.signs.append(Sign(15, 7, 1))

    def _build_village(self):
        self._add("house_blue", 18, 3)
        self._add("house_green", 25, 3)
        self._fill("stone", 18, 7, 29, 14)
        self.ground[6][20] = "path"
        self.ground[6][27] = "path"
        self._add("well", 23, 11)
        for x, y in ((18, 7), (29, 7), (18, 14), (29, 14)):
            self._add("lamp", x, y)
        self._add("bush", 17, 12)
        self._add("bush", 30, 12)
        self.signs.append(Sign(30, 7, 2))

    def _build_lake(self, rng):
        self._fill("water", 34, 2, 45, 6)
        self._fill("sand", 33, 7, 45, 7)
        self._fill("plank", 40, 3, 40, 7)
        self._fill("sand", 40, 10, 45, 10)
        self._fill("sand", 40, 11, 40, 14)
        self._fill("water", 41, 11, 45, 14)
        for y in range(2, 15):
            for x in range(33, 46):
                if self.ground[y][x] == "water" and rng.random() < 0.12 and x != 40:
                    self._add(rng.choice(["lily", "lily", "lily_flower"]), x, y)
        self._add("oak", 33, 12)
        self._add("bush", 37, 11)
        self._add("crate", 36, 7)   # the fisher's tackle box
        self.signs.append(Sign(40, 15, 3))

    def _build_mountain(self):
        self._add("boulder", 33, 19)
        self._add("boulder", 43, 24)
        self._add("boulder", 40, 29)
        for x, y in ((35, 22), (44, 18), (33, 29), (36, 30), (45, 29), (41, 18)):
            self._add("pine", x, y)
        for x, y in ((37, 21), (44, 21), (34, 25), (42, 27), (37, 26)):
            self._add("rock", x, y)
        self.signs.append(Sign(32, 22, 4))

    def _build_market(self):
        self._add("stall", 18, 19)
        self._add("stall_blue", 22, 19)
        self._add("stall_green", 26, 19)
        self._fill("path", 18, 20, 29, 21)
        for x, y in ((29, 18), (29, 19), (18, 29), (19, 29)):
            self._add("crate", x, y)
        for x, y in ((21, 18), (25, 18), (30, 29), (17, 26)):
            self._add("barrel", x, y)
        self._add("oak", 23, 28)
        self.signs.append(Sign(17, 22, 5))

    def _build_forge(self):
        self._fill("cave", 3, 25, 14, 30)
        self._add("mine", 3, 27)
        self._add("anvil", 9, 26)
        self._add("furnace", 11, 26)
        self._add("lamp", 7, 26)
        self._add("lamp", 14, 26)
        for x, y in ((3, 19), (6, 18), (14, 30), (9, 30)):
            self._add("rock", x, y)
        self._add("boulder", 10, 18)
        self._add("pine", 2, 21)
        self._add("pine", 4, 18)

    def _build_walls(self, rng):
        for y in range(ROWS):
            for x in range(COLS):
                border = x < 2 or x >= COLS - 2 or y < 2 or y >= ROWS - 2
                divider = (x in (16, 31) and 2 <= y <= 30) or (y == 16 and 2 <= x <= 45)
                if (border or divider) and (x, y) not in self.gate_tiles:
                    dark = self.zone_at(min(max(x, 2), 45), min(max(y, 2), 30)) in DARK_ZONES or y >= 16
                    kind = "pine" if rng.random() < (0.6 if dark else 0.25) else "oak"
                    # fence posts beside a gate, so tree tops don't hide it
                    if any((x, y - k) in self.gate_tiles or (x - k, y) in self.gate_tiles
                           or (x + k, y) in self.gate_tiles for k in (1, 2)):
                        kind = "fence"
                    self._add(kind, x, y)

    def _scatter(self, rng):
        """Sprinkle bushes, rocks and trees on open grass, away from anything important."""
        keep_clear = set(self.blocked) | {t for p in self.props for t in p.tiles()}
        keep_clear |= {(x, y) for y in range(ROWS) for x in range(COLS)
                       if self.ground[y][x] not in ("grass", "grass_dark")}
        keep_clear |= set(self.gate_tiles) | {START}
        for zone, (x1, y1, x2, y2) in enumerate(ZONES):
            choices = ["rock", "rock", "pine", "bush"] if zone in DARK_ZONES else ["bush", "bush", "oak", "rock"]
            placed = 0
            for _ in range(200):
                if placed >= 7:
                    break
                x, y = rng.randint(x1, x2), rng.randint(y1, y2)
                if any((x + dx, y + dy) in keep_clear for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    continue
                self._add(rng.choice(choices), x, y)
                keep_clear.add((x, y))
                placed += 1


def gate_open(progress, world):
    """A gate opens once the first level of its world is unlocked."""
    first = next(i for i, lv in enumerate(LEVELS) if lv.world is WORLDS[world])
    return progress.is_unlocked(first)


def open_gates(progress):
    return {world for world in GATES if gate_open(progress, world)}
