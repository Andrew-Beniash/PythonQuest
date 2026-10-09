"""Hand-coded pixel art: every tile, prop and character is drawn here, pixel by pixel.

Sprites are built at 1x on a tiny `Pixmap`, then turned into a Tk PhotoImage and
zoomed up, which gives the crisp chunky look of a farming RPG without any image files.
"""

import random
import tkinter as tk

from .theme import shade

SCALE = 3                 # screen pixels per art pixel
TILE = 16                 # art pixels per tile
TILE_PX = TILE * SCALE    # screen pixels per tile
OUT = "#2b1a0f"           # outline colour used on sprites

# ------------------------------------------------------------------ palettes
GRASS = {
    "grass": ("#68a83c", "#4f8b2d", "#86c24c"),
    "grass_dark": ("#4f8c3a", "#3d712e", "#66a54a"),
}
GROUND = {
    "path": ("#c9a06a", "#ab814f", "#dcb985"),
    "sand": ("#e7d093", "#d2b878", "#f3e2b0"),
    "soil": ("#83552f", "#663f22", "#9b6b3f"),
    "stone": ("#a7a095", "#7f786e", "#c2bcb1"),
    "cave": ("#7c7480", "#5b5460", "#958d99"),
    "plank": ("#b9864a", "#7e5329", "#d29e5f"),
}
WATER = ("#3f8fd2", "#2f74b5", "#7cc0f2", "#d7f0ff")
FLOWERS = ["#fff4f0", "#ffd84d", "#ff8fb1", "#a5c8ff", "#ff9a4d"]


class Pixmap:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.px = [[fill] * w for _ in range(h)]

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.put(x, y, c)

    def disc(self, cx, cy, r, c):
        self.ellipse(cx, cy, r, r, c)

    def blit(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                if other.px[y][x]:
                    self.put(ox + x, oy + y, other.px[y][x])

    def mirrored(self):
        out = Pixmap(self.w, self.h)
        out.px = [row[::-1] for row in self.px]
        return out

    def crop(self, x, y, w, h):
        out = Pixmap(w, h)
        for yy in range(h):
            for xx in range(w):
                out.px[yy][xx] = self.get(x + xx, y + yy)
        return out

    def outlined(self, color=OUT):
        """Pad by one pixel and draw a dark outline around everything that's filled."""
        out = Pixmap(self.w + 2, self.h + 2)
        out.blit(self, 1, 1)
        edge = []
        for y in range(out.h):
            for x in range(out.w):
                if out.px[y][x] is None and any(
                        out.get(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    edge.append((x, y))
        for x, y in edge:
            out.px[y][x] = color
        return out

    def photo(self, scale=SCALE):
        img = tk.PhotoImage(width=self.w, height=self.h)
        for y, row in enumerate(self.px):
            x = 0
            while x < self.w:
                if row[x] is None:
                    x += 1
                    continue
                start = x
                while x < self.w and row[x] is not None:
                    x += 1
                img.put("{" + " ".join(row[start:x]) + "}", to=(start, y))
        return img.zoom(scale) if scale > 1 else img


def _rng(*key):
    return random.Random("|".join(str(k) for k in key))


# ------------------------------------------------------------------ ground tiles


def grass_tile(kind, variant):
    base, dark, light = GRASS[kind]
    rng = _rng("grass", kind, variant)
    p = Pixmap(TILE, TILE, base)
    for _ in range(9):
        x, y = rng.randrange(1, 15), rng.randrange(2, 16)
        p.put(x, y, dark)
        p.put(x - 1, y - 1, dark)
        p.put(x + 1, y - 1, dark)
    for _ in range(7):
        x, y = rng.randrange(16), rng.randrange(1, 16)
        p.put(x, y, light)
        p.put(x, y - 1, light)
    if variant >= 4:  # flowers
        for _ in range(rng.choice([1, 2, 3])):
            x, y = rng.randrange(2, 14), rng.randrange(2, 14)
            petal = rng.choice(FLOWERS)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p.put(x + dx, y + dy, petal)
            p.put(x, y, "#ffcf33" if petal != "#ffd84d" else "#d9642b")
            p.put(x, y + 2, dark)
    return p


def _fringe(p, mask, grass_kind, seed):
    """Let grass creep over the edges of a ground tile that touches grass."""
    base, dark, _light = GRASS[grass_kind]
    for side, bit in (("n", 1), ("e", 2), ("s", 4), ("w", 8)):
        if not mask & bit:
            continue
        for i in range(TILE):
            depth = 1 + ((i * 5 + seed) % 4 == 0) + ((i * 3 + seed) % 7 == 0)
            for k in range(depth + 1):
                color = dark if k == depth else base
                x, y = {"n": (i, k), "s": (i, 15 - k), "w": (k, i), "e": (15 - k, i)}[side]
                p.put(x, y, color)


def ground_tile(kind, mask, grass_kind, variant):
    base, dark, light = GROUND[kind]
    rng = _rng("ground", kind, variant)
    p = Pixmap(TILE, TILE, base)
    if kind in ("stone", "cave"):
        p.rect(0, 0, 16, 16, dark)
        for row in range(4):
            offset = (row % 2) * 4
            for col in range(-1, 3):
                x0 = col * 8 + offset
                tone = rng.choice([base, base, base, shade(base, 0.93), shade(base, 1.06)])
                p.rect(x0 + 1, row * 4, 6, 3, tone)
                p.put(x0 + 1, row * 4, light)
                p.put(x0 + 2, row * 4, light)
    elif kind == "soil":
        for y in (3, 7, 11, 15):
            p.rect(0, y, 16, 1, dark)
            p.rect(0, y - 1, 16, 1, shade(base, 1.04))
        for _ in range(6):
            p.put(rng.randrange(16), rng.randrange(16), light)
    elif kind == "plank":
        for y in (3, 7, 11, 15):
            p.rect(0, y, 16, 1, dark)
        for y in (0, 4, 8, 12):
            seam = (y * 3 + 5) % 16
            p.rect(seam, y, 1, 3, dark)
            p.rect(0, y, 16, 1, light)
            p.put((seam + 3) % 16, y + 1, shade(dark, 0.8))
    else:
        for _ in range(12):
            p.put(rng.randrange(16), rng.randrange(16), dark)
        for _ in range(9):
            p.put(rng.randrange(16), rng.randrange(16), light)
        if kind == "path":
            for _ in range(2):
                x, y = rng.randrange(1, 14), rng.randrange(1, 14)
                p.rect(x, y, 2, 2, "#9c8a76")
                p.put(x, y, "#c4b4a0")
    _fringe(p, mask, grass_kind, variant)
    return p


def water_tile(mask, frame, variant):
    base, deep, light, foam = WATER
    rng = _rng("water", variant)
    p = Pixmap(TILE, TILE, base)
    for _ in range(10):
        p.put(rng.randrange(16), rng.randrange(16), deep)
    for i in range(3):
        x, y = rng.randrange(0, 12), rng.randrange(3, 15)
        x = (x + frame * 2 + i) % 13
        p.rect(x, y, 3, 1, light)
        if frame:
            p.put(x + 1, y - 1, light)
    if frame and rng.random() < 0.5:
        p.put(rng.randrange(16), rng.randrange(16), foam)
    if mask & 1:  # land to the north: a shadowed bank
        p.rect(0, 0, 16, 1, "#6b4a2b")
        p.rect(0, 1, 16, 2, deep)
    for bit, (x, y, w, h) in ((2, (15, 0, 1, 16)), (4, (0, 15, 16, 1)), (8, (0, 0, 1, 16))):
        if mask & bit:
            p.rect(x, y, w, h, foam)
    return p


# ------------------------------------------------------------------ props


def oak():
    p = Pixmap(32, 48)
    p.rect(13, 30, 6, 16, "#7a4b25")
    p.rect(17, 30, 2, 16, "#5e3a1c")
    p.rect(11, 44, 10, 2, "#7a4b25")
    p.rect(14, 33, 1, 4, "#94603a")
    for cx, cy, r in ((16, 17, 14), (8, 22, 8), (24, 22, 8), (16, 26, 9)):
        p.disc(cx, cy, r, "#2f6e2c")
    for cx, cy, r in ((16, 15, 12), (9, 19, 6), (23, 19, 6)):
        p.disc(cx, cy, r, "#3f8f34")
    for cx, cy, r in ((13, 10, 6), (21, 13, 4), (8, 17, 3)):
        p.disc(cx, cy, r, "#5cae45")
    rng = _rng("oak")
    for _ in range(14):
        x, y = rng.randrange(6, 26), rng.randrange(4, 26)
        if p.get(x, y) in ("#3f8f34", "#5cae45"):
            p.put(x, y, "#7cc95a")
    return p.outlined()


def pine():
    p = Pixmap(32, 48)
    p.rect(14, 38, 4, 9, "#6e4524")
    p.rect(16, 38, 2, 9, "#553419")
    tiers = ((3, 17, 2, 9), (11, 28, 3, 12), (20, 40, 4, 15))
    for top, bottom, w0, w1 in tiers:
        for y in range(top, bottom):
            half = w0 + (w1 - w0) * (y - top) / max(1, bottom - top - 1)
            x0, x1 = int(16 - half), int(16 + half)
            p.rect(x0, y, x1 - x0, 1, "#2c6136")
            p.rect(16, y, max(0, x1 - 16), 1, "#3b7d44")
            p.put(x0 + 1, y, "#4f9a55")
        p.rect(int(16 - w1), bottom - 1, int(2 * w1), 1, "#244f2c")
    return p.outlined()


def bush():
    p = Pixmap(16, 14)
    for cx, cy, r in ((8, 8, 6), (4, 9, 4), (12, 9, 4)):
        p.disc(cx, cy, r, "#3a7a30")
    for cx, cy, r in ((7, 6, 4), (11, 7, 2.5)):
        p.disc(cx, cy, r, "#4f9a3c")
    p.disc(6, 5, 1.6, "#70bb52")
    for x, y in ((4, 9), (10, 10), (12, 6)):
        p.put(x, y, "#d8414a")
    return p.outlined()


def rock(big=False):
    w, h = (30, 22) if big else (14, 11)
    p = Pixmap(w, h)
    p.ellipse(w / 2, h / 2 + 1, w / 2, h / 2 - 0.5, "#8d8a86")
    p.ellipse(w / 2, h / 2 + 2.5, w / 2 - 1, h / 2 - 2, "#7a7773")
    p.ellipse(w / 2 - w / 7, h / 3 + 1, w / 3, h / 5, "#aeaaa4")
    p.ellipse(w / 2 - w / 5, h / 3, w / 8, h / 9 + 0.6, "#c9c5be")
    return p.outlined()


def fence():
    p = Pixmap(16, 16)
    for x in (1, 12):
        p.rect(x, 2, 3, 13, "#a87444")
        p.rect(x + 2, 2, 1, 13, "#7a5028")
        p.put(x, 2, "#c99561")
    for y in (5, 10):
        p.rect(0, y, 16, 2, "#b5824f")
        p.rect(0, y + 1, 16, 1, "#7a5028")
    return p.outlined()


def gate():
    p = Pixmap(16, 18)
    for x in range(1, 15, 3):
        p.rect(x, 1, 2, 16, "#9c6a3a")
        p.put(x, 1, "#c48d52")
    p.rect(0, 5, 16, 2, "#6e4524")
    p.rect(0, 12, 16, 2, "#6e4524")
    for i in range(14):
        p.put(1 + i, 13 - int(i * 0.55), "#6e4524")
    p.rect(6, 7, 4, 4, "#e2b13c")
    p.rect(7, 5, 2, 2, "#8a8580")
    p.put(7, 9, OUT)
    return p.outlined()


def house(roof="#b5473a"):
    p = Pixmap(80, 80)
    wall, wall_dark = "#c49058", "#95683a"
    p.rect(5, 40, 70, 37, wall)
    for y in range(43, 77, 4):
        p.rect(5, y, 70, 1, wall_dark)
    p.rect(5, 40, 70, 3, shade(wall, 0.7))
    p.rect(3, 76, 74, 4, "#7d776e")
    # roof
    for y in range(6, 44):
        half = 26 + (y - 6) * 14 / 37
        x0, x1 = int(40 - half), int(40 + half)
        color = roof if (y - 6) % 5 else shade(roof, 0.75)
        p.rect(x0, y, x1 - x0, 1, color)
        if (y - 6) % 5 == 2:
            for x in range(x0 + (y % 10), x1, 10):
                p.put(x, y, shade(roof, 0.75))
    p.rect(14, 6, 52, 2, shade(roof, 1.25))
    p.rect(58, 0, 8, 14, "#8a8580")
    p.rect(58, 0, 8, 2, "#a8a39d")
    p.rect(64, 2, 2, 12, "#6f6a66")
    # door
    p.rect(33, 54, 14, 23, "#4a2c14")
    p.rect(35, 56, 10, 21, "#7a4b25")
    p.rect(39, 56, 1, 21, "#5e3a1c")
    p.rect(42, 66, 2, 2, "#ffd84d")
    # windows with warm light
    for x0 in (11, 55):
        p.rect(x0, 50, 15, 13, "#4a2c14")
        p.rect(x0 + 2, 52, 11, 9, "#ffe08a")
        p.rect(x0 + 2, 52, 4, 3, "#fff4c4")
        p.rect(x0 + 7, 52, 1, 9, "#4a2c14")
        p.rect(x0 + 2, 56, 11, 1, "#4a2c14")
        p.rect(x0, 63, 15, 3, "#7a4b25")
        for i, c in enumerate(("#ff8fb1", "#ffd84d", "#ff8fb1", "#a5c8ff", "#ffd84d")):
            p.put(x0 + 1 + i * 3, 62, c)
            p.put(x0 + 2 + i * 3, 62, "#4f9a3c")
    return p.outlined()


def well():
    p = Pixmap(32, 34)
    p.rect(3, 4, 2, 16, "#7a4b25")
    p.rect(27, 4, 2, 16, "#7a4b25")
    for y in range(0, 8):
        half = 6 + y * 2
        p.rect(16 - half, y, half * 2, 1, "#b5473a" if y % 3 else "#8f3329")
    p.rect(10, 9, 12, 1, "#5e3a1c")
    p.rect(15, 9, 2, 6, "#8a8580")
    p.rect(2, 18, 28, 15, "#9c968c")
    for y in (21, 25, 29):
        p.rect(2, y, 28, 1, "#77716a")
        off = 0 if y % 2 else 4
        for x in range(2 + off, 30, 8):
            p.rect(x, y - 3, 1, 3, "#77716a")
    p.ellipse(16, 18, 13, 3, "#c2bcb1")
    p.ellipse(16, 18, 10, 2, "#2a4f73")
    return p.outlined()


def stall(awning="#d9453b"):
    p = Pixmap(48, 46)
    p.rect(4, 12, 2, 20, "#7a4b25")
    p.rect(42, 12, 2, 20, "#7a4b25")
    p.rect(1, 28, 46, 14, "#a87444")
    p.rect(1, 28, 46, 2, "#c99561")
    for y in (33, 37):
        p.rect(1, y, 46, 1, "#7a5028")
    rng = _rng("stall", awning)
    for x in range(5, 44, 6):
        c = rng.choice(["#e0503f", "#ffcf33", "#7cc95a", "#ff9a4d", "#a77bff"])
        p.disc(x + 1, 26, 2.6, c)
        p.put(x, 25, shade(c, 1.4))
    for y in range(2, 14):
        for x in range(0, 48):
            p.put(x, y, awning if (x // 6) % 2 == 0 else "#fff3d6")
    for x in range(0, 48, 6):
        p.disc(x + 3, 14, 3, awning if (x // 6) % 2 == 0 else "#fff3d6")
    p.rect(0, 2, 48, 1, shade(awning, 1.3))
    return p.outlined()


def crate():
    p = Pixmap(14, 14)
    p.rect(0, 0, 14, 14, "#a87444")
    p.rect(0, 0, 14, 2, "#c99561")
    p.rect(0, 12, 14, 2, "#7a5028")
    p.rect(0, 0, 2, 14, "#7a5028")
    p.rect(12, 0, 2, 14, "#7a5028")
    for i in range(10):
        p.put(2 + i, 2 + i, "#7a5028")
        p.put(11 - i, 2 + i, "#7a5028")
    return p.outlined()


def barrel():
    p = Pixmap(12, 15)
    p.ellipse(6, 7.5, 6, 7.5, "#9c6a3a")
    p.rect(1, 1, 10, 13, "#9c6a3a")
    p.rect(8, 1, 2, 13, "#7a5028")
    p.rect(2, 1, 1, 13, "#b5824f")
    for y in (3, 11):
        p.rect(0, y, 12, 2, "#5b5460")
    p.ellipse(6, 1.5, 5, 1.5, "#b5824f")
    return p.outlined()


def lamp():
    p = Pixmap(10, 32)
    p.rect(4, 8, 2, 23, "#3d3a40")
    p.rect(2, 29, 6, 3, "#3d3a40")
    p.rect(1, 1, 8, 8, "#3d3a40")
    p.rect(2, 2, 6, 6, "#ffd84d")
    p.rect(3, 3, 2, 2, "#fff4c4")
    p.rect(0, 0, 10, 1, "#3d3a40")
    return p.outlined()


def sign():
    p = Pixmap(16, 16)
    p.rect(7, 8, 2, 8, "#7a4b25")
    p.rect(0, 1, 16, 9, "#b5824f")
    p.rect(0, 1, 16, 1, "#d29e5f")
    p.rect(0, 9, 16, 1, "#7a5028")
    for y in (4, 6):
        p.rect(3, y, 10, 1, "#6e4524")
    p.rect(12, 3, 2, 5, "#6e4524")
    return p.outlined()


def mailbox():
    p = Pixmap(12, 20)
    p.rect(5, 8, 2, 12, "#7a4b25")
    p.rect(0, 2, 12, 7, "#d9453b")
    p.rect(0, 2, 12, 1, "#ff7a6b")
    p.rect(1, 1, 10, 1, "#d9453b")
    p.rect(10, 0, 1, 5, "#3d3a40")
    p.rect(10, 0, 2, 2, "#ffd84d")
    return p.outlined()


def scarecrow():
    p = Pixmap(16, 30)
    p.rect(7, 8, 2, 22, "#7a4b25")
    p.rect(1, 13, 14, 2, "#7a4b25")
    p.rect(4, 12, 8, 9, "#4f78b8")
    p.rect(4, 12, 8, 1, "#6f95d1")
    p.put(6, 16, "#ffd84d")
    p.disc(8, 8, 4, "#f2d27a")
    p.put(6, 8, OUT)
    p.put(10, 8, OUT)
    p.rect(1, 4, 14, 2, "#d9b04a")
    p.rect(4, 0, 8, 5, "#d9b04a")
    p.rect(4, 3, 8, 1, "#b5473a")
    return p.outlined()


def crop(variant):
    p = Pixmap(14, 12)
    if variant == 0:      # sprout
        p.rect(6, 6, 2, 6, "#4f9a3c")
        p.ellipse(4, 6, 3, 1.6, "#70bb52")
        p.ellipse(10, 5, 3, 1.6, "#70bb52")
    elif variant == 1:    # cabbage
        p.disc(7, 7, 5, "#5ba84a")
        p.disc(7, 6, 3, "#9ad874")
        p.put(6, 5, "#c3eea0")
    elif variant == 2:    # pumpkin
        p.ellipse(7, 8, 6, 4, "#e07a2b")
        p.rect(5, 5, 1, 7, "#c45f1d")
        p.rect(9, 5, 1, 7, "#c45f1d")
        p.rect(6, 2, 2, 3, "#4f9a3c")
        p.put(4, 6, "#ffad66")
    else:                 # carrots
        for x in (3, 7, 11):
            p.rect(x, 4, 1, 6, "#4f9a3c")
            p.put(x - 1, 4, "#70bb52")
            p.put(x + 1, 5, "#70bb52")
            p.rect(x - 1, 10, 3, 2, "#ff8a2b")
    return p.outlined()


def lily(flower):
    p = Pixmap(12, 9)
    p.ellipse(6, 4.5, 6, 4.5, "#4f9a3c")
    p.rect(6, 1, 1, 4, "#3a7a30")
    p.ellipse(4, 3, 2, 1.5, "#70bb52")
    if flower:
        p.disc(8, 4, 2, "#ff8fb1")
        p.put(8, 4, "#ffd84d")
    return p


def anvil():
    p = Pixmap(16, 12)
    p.rect(0, 0, 13, 4, "#55525a")
    p.rect(13, 1, 3, 2, "#55525a")
    p.rect(0, 0, 16, 1, "#8a8693")
    p.rect(4, 4, 6, 4, "#45424a")
    p.rect(2, 8, 10, 4, "#3a373e")
    return p.outlined()


def furnace():
    p = Pixmap(30, 34)
    p.ellipse(15, 17, 15, 17, "#8a8580")
    p.rect(0, 17, 30, 17, "#8a8580")
    for y in range(6, 34, 5):
        p.rect(0, y, 30, 1, "#6f6a66")
    p.ellipse(15, 26, 8, 8, "#2b1a0f")
    p.rect(7, 26, 16, 8, "#2b1a0f")
    p.ellipse(15, 29, 6, 4, "#ff7a2b")
    p.ellipse(15, 30, 4, 3, "#ffd84d")
    p.rect(11, 0, 8, 6, "#6f6a66")
    return p.outlined()


def mine():
    p = Pixmap(48, 44)
    p.ellipse(24, 26, 24, 22, "#7c7480")
    p.rect(0, 26, 48, 18, "#7c7480")
    rng = _rng("mine")
    for _ in range(40):
        x, y = rng.randrange(48), rng.randrange(6, 44)
        if p.get(x, y):
            p.put(x, y, rng.choice(["#5b5460", "#958d99"]))
    p.ellipse(24, 30, 11, 12, "#120c08")
    p.rect(13, 30, 22, 14, "#120c08")
    p.rect(11, 18, 4, 26, "#7a4b25")
    p.rect(33, 18, 4, 26, "#7a4b25")
    p.rect(9, 16, 30, 4, "#9c6a3a")
    p.rect(9, 16, 30, 1, "#c48d52")
    p.rect(21, 34, 6, 1, "#ffd84d")
    return p.outlined()


# ------------------------------------------------------------------ markers


def bubble(kind):
    p = Pixmap(11, 13)
    p.rect(0, 1, 11, 8, "#fffaf0")
    p.rect(1, 0, 9, 10, "#fffaf0")
    p.rect(4, 10, 3, 1, "#fffaf0")
    p.put(5, 11, "#fffaf0")
    if kind == "exclaim":
        p.rect(5, 2, 1, 4, "#d9453b")
        p.rect(4, 2, 1, 3, "#d9453b")
        p.put(5, 7, "#d9453b")
        p.put(4, 7, "#d9453b")
    elif kind == "star":
        for x, y in ((5, 1), (5, 2), (4, 3), (5, 3), (6, 3), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4),
                     (8, 4), (3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (4, 6), (6, 6), (3, 7), (7, 7)):
            p.put(x, y, "#f2b200")
    elif kind == "coin":
        p.disc(5.5, 4.5, 3.6, "#c98a0e")
        p.disc(5.5, 4.5, 2.6, "#ffcf33")
        p.rect(5, 3, 1, 3, "#c98a0e")
        p.put(4, 3, "#fff4c4")
    else:
        for x in (2, 5, 8):
            p.put(x, 5, "#9c968c")
    return p.outlined()


# ------------------------------------------------------------------ characters

SKINS = ["#f6cfa4", "#e8b48a", "#c98d5f", "#9a6440", "#704428"]
BLUSH = "#f19a8f"


def character(look, facing="down", frame=0):
    """A 16x24 villager. look: skin, hair, shirt, pants, shoes, style (short|long|spiky), hat."""
    if facing == "right":
        return character(look, "left", frame).mirrored()
    skin, hair, shirt, pants = look["skin"], look["hair"], look["shirt"], look["pants"]
    shoes = look.get("shoes", "#4a2f1b")
    style, hat = look.get("style", "short"), look.get("hat")
    shirt_d, pants_d, skin_d = shade(shirt, 0.78), shade(pants, 0.8), shade(skin, 0.86)
    p = Pixmap(16, 24)

    if facing in ("down", "up"):
        for x0, lifted in ((5, frame == 1), (8, frame == 2)):
            p.rect(x0, 17, 3, 4 - lifted, pants)
            p.rect(x0, 21 - lifted, 3, 2, shoes)
        p.rect(4, 16, 8, 2, pants)
        p.rect(10, 16, 1, 2, pants_d)
        p.rect(4, 10, 8, 7, shirt)
        p.rect(11, 10, 1, 7, shirt_d)
        left_arm, right_arm = (1 if frame == 1 else 0), (1 if frame == 2 else 0)
        p.rect(3, 11 + left_arm, 1, 4, shirt_d)
        p.put(3, 15 + left_arm, skin)
        p.rect(12, 11 + right_arm, 1, 4, shirt_d)
        p.put(12, 15 + right_arm, skin)
        p.rect(4, 2, 8, 8, skin)
        p.rect(3, 3, 10, 6, skin)
        if facing == "down":
            p.rect(6, 10, 4, 1, shirt_d)
            p.rect(5, 6, 1, 2, OUT)
            p.rect(10, 6, 1, 2, OUT)
            p.put(4, 8, BLUSH)
            p.put(11, 8, BLUSH)
            p.rect(7, 9, 2, 1, skin_d)
            p.rect(3, 1, 10, 3, hair)
            p.rect(4, 0, 8, 1, hair)
            p.rect(3, 4, 1, 2, hair)
            p.rect(12, 4, 1, 2, hair)
            p.put(5, 4, hair)
            p.put(9, 4, hair)
            p.put(10, 4, hair)
            if style == "long":
                p.rect(2, 3, 1, 10, hair)
                p.rect(13, 3, 1, 10, hair)
                p.rect(3, 6, 1, 6, hair)
                p.rect(12, 6, 1, 6, hair)
        else:
            p.rect(3, 1, 10, 8, hair)
            p.rect(4, 0, 8, 1, hair)
            p.rect(11, 2, 1, 6, shade(hair, 0.82))
            if style == "long":
                p.rect(3, 9, 10, 4, hair)
    else:  # facing left
        front, back = {0: (5, 8), 1: (3, 9), 2: (8, 5)}[frame]
        p.rect(back, 17, 3, 4, pants_d)
        p.rect(back, 21, 3, 2, shade(shoes, 0.8))
        p.rect(front, 17, 3, 4, pants)
        p.rect(front, 21, 3, 2, shoes)
        p.rect(5, 16, 6, 2, pants)
        p.rect(5, 10, 6, 7, shirt)
        p.rect(10, 10, 1, 7, shirt_d)
        arm_x = {0: 7, 1: 5, 2: 9}[frame]
        p.rect(arm_x, 11, 2, 4, shirt_d)
        p.rect(arm_x, 15, 2, 1, skin)
        p.rect(4, 2, 8, 8, skin)
        p.rect(3, 4, 1, 4, skin)
        p.rect(5, 5, 1, 2, OUT)
        p.put(5, 8, BLUSH)
        p.rect(4, 1, 8, 3, hair)
        p.rect(5, 0, 7, 1, hair)
        p.rect(9, 3, 3, 5, hair)
        p.rect(12, 2, 1, 6, hair)
        p.put(4, 4, hair)
        if style == "long":
            p.rect(9, 8, 4, 5, hair)
    if style == "spiky":
        for x in (4, 7, 10):
            p.put(x, 0, None)
            p.put(x + 1, 1, shade(hair, 1.25))
    if hat:
        brim_x, brim_w = (1, 14) if facing in ("down", "up") else (2, 13)
        p.rect(brim_x, 3, brim_w, 1, hat)
        p.rect(4, 0, 8, 3, hat)
        p.rect(4, 2, 8, 1, shade(hat, 0.72))
        p.rect(4, 0, 8, 1, shade(hat, 1.15))
    return p.outlined()


ROBOT_BODY, ROBOT_DARK, ROBOT_SCREEN, ROBOT_EYE = "#d6cfff", "#8f7bff", "#1d1730", "#5ef0f0"


def robot(mood="idle"):
    """Pixel the robot, 16x16, for the big mascot. mood: idle|blink|happy|sad|think."""
    p = Pixmap(16, 17)
    tip = {"happy": "#ff6fb5", "sad": "#9c968c", "think": "#ffd84d"}.get(mood, "#ff6fb5")
    p.rect(7, 1, 2, 2, "#a59cd3")
    p.rect(7, 0, 2, 1, tip)
    p.rect(2, 3, 12, 8, ROBOT_BODY)
    for x, y in ((2, 3), (13, 3), (2, 10), (13, 10)):
        p.put(x, y, None)
    p.rect(2, 4, 12, 1, "#eeeaff")
    p.rect(1, 5, 1, 3, "#ff6fb5")
    p.rect(14, 5, 1, 3, "#ff6fb5")
    p.rect(4, 5, 8, 4, ROBOT_SCREEN)
    eyes = {
        "idle": [(5, 6), (5, 7), (10, 6), (10, 7)],
        "blink": [(5, 7), (6, 7), (9, 7), (10, 7)],
        "happy": [(5, 6), (4, 7), (6, 7), (10, 6), (9, 7), (11, 7)],
        "sad": [(5, 7), (10, 7), (4, 6), (11, 6)],
        "think": [(6, 5), (6, 6), (11, 5), (11, 6)],
    }[mood]
    for x, y in eyes:
        p.put(x, y, ROBOT_EYE)
    if mood == "happy":
        p.rect(7, 8, 2, 1, "#ff6fb5")
    p.rect(4, 11, 8, 4, ROBOT_DARK)
    p.rect(7, 12, 2, 2, "#ffd84d")
    if mood == "happy":
        p.rect(3, 9, 1, 3, ROBOT_DARK)
        p.rect(12, 9, 1, 3, ROBOT_DARK)
    elif mood == "sad":
        p.rect(3, 12, 1, 3, ROBOT_DARK)
        p.rect(12, 12, 1, 3, ROBOT_DARK)
    else:
        p.rect(3, 11, 1, 3, ROBOT_DARK)
        p.rect(12, 11, 1, 3, ROBOT_DARK)
    p.rect(4, 15, 3, 2, "#4b3fa6")
    p.rect(9, 15, 3, 2, "#4b3fa6")
    return p.outlined()


def mini_robot(frame=0):
    """A small Pixel that follows you around the valley."""
    p = Pixmap(12, 13)
    p.rect(5, 0, 2, 1, "#ff6fb5")
    p.rect(5, 1, 2, 1, "#a59cd3")
    p.rect(1, 2, 10, 6, ROBOT_BODY)
    p.put(1, 2, None)
    p.put(10, 2, None)
    p.rect(2, 3, 8, 3, ROBOT_SCREEN)
    if frame == 1:
        p.rect(3, 5, 2, 1, ROBOT_EYE)
        p.rect(7, 5, 2, 1, ROBOT_EYE)
    else:
        p.rect(3, 4, 1, 2, ROBOT_EYE)
        p.rect(8, 4, 1, 2, ROBOT_EYE)
    p.rect(3, 8, 6, 3, ROBOT_DARK)
    p.rect(5, 9, 2, 1, "#ffd84d")
    p.rect(3, 11, 2, 2, "#4b3fa6")
    p.rect(7, 11, 2, 2, "#4b3fa6")
    return p.outlined()


# ------------------------------------------------------------------ the image bank

PROP_BUILDERS = {
    "oak": oak, "pine": pine, "bush": bush, "rock": rock, "boulder": lambda: rock(big=True),
    "fence": fence, "gate": gate, "house": house, "house_blue": lambda: house("#3f6fb5"),
    "house_green": lambda: house("#4f8a3a"), "well": well, "stall": stall,
    "stall_blue": lambda: stall("#3f6fb5"), "stall_green": lambda: stall("#4f9a3c"), "crate": crate,
    "barrel": barrel, "lamp": lamp, "sign": sign, "mailbox": mailbox, "scarecrow": scarecrow,
    "crop0": lambda: crop(0), "crop1": lambda: crop(1), "crop2": lambda: crop(2), "crop3": lambda: crop(3),
    "lily": lambda: lily(False), "lily_flower": lambda: lily(True), "anvil": anvil, "furnace": furnace,
    "mine": mine,
}


class Art:
    """Builds PhotoImages on demand and keeps them alive (Tk forgets unreferenced images)."""

    def __init__(self):
        self._cache = {}

    def _get(self, key, build, scale=SCALE):
        full_key = (key, scale)
        if full_key not in self._cache:
            self._cache[full_key] = build().photo(scale)
        return self._cache[full_key]

    def grass(self, kind, variant):
        return self._get(("grass", kind, variant), lambda: grass_tile(kind, variant))

    def ground(self, kind, mask, grass_kind, variant):
        return self._get(("ground", kind, mask, grass_kind, variant),
                         lambda: ground_tile(kind, mask, grass_kind, variant))

    def water(self, mask, frame, variant):
        return self._get(("water", mask, frame, variant), lambda: water_tile(mask, frame, variant))

    def prop(self, kind):
        return self._get(("prop", kind), PROP_BUILDERS[kind])

    def prop_icon(self, kind, max_px):
        """A prop scaled up as large as fits in a max_px box - used as a portrait."""
        key = ("icon", kind, max_px)
        if key not in self._cache:
            pixmap = PROP_BUILDERS[kind]()
            scale = max(1, min(6, max_px // max(pixmap.w, pixmap.h)))
            self._cache[key] = pixmap.photo(scale)
        return self._cache[key]

    def bubble(self, kind):
        return self._get(("bubble", kind), lambda: bubble(kind))

    def character(self, look_key, look, facing, frame):
        return self._get(("char", look_key, facing, frame), lambda: character(look, facing, frame))

    def portrait(self, look_key, look, scale=6):
        return self._get(("portrait", look_key), lambda: character(look, "down", 0).crop(0, 0, 18, 17), scale)

    def robot(self, mood, scale=6):
        return self._get(("robot", mood), lambda: robot(mood), scale)

    def mini_robot(self, frame):
        return self._get(("mini_robot", frame), lambda: mini_robot(frame))
