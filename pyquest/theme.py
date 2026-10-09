"""Colours, fonts and colour helpers for the cozy pixel-farm look."""

import tkinter.font as tkfont

WIDTH, HEIGHT = 1200, 780

# wood and paper
BG = "#3b2718"          # dark wood behind every screen
BG_DEEP = "#24170e"
OUTLINE = "#2b1a0f"
WOOD = "#9c6a3a"
WOOD_DARK = "#6e4524"
WOOD_LIGHT = "#c48d52"
PAPER = "#f7e5b9"
PAPER_DARK = "#ead196"
PAPER_EDGE = "#c9a466"
INK = "#3d2614"
INK_SOFT = "#7b5a3c"
CREAM = "#fff3d6"       # text on wood
CREAM_SOFT = "#d9bf98"

# code areas
EDITOR_BG = "#2b2420"
CONSOLE_BG = "#211a16"
CODE_TEXT = "#f3e6cf"
GUTTER = "#8c7a66"
SELECTION = "#5a4636"
CURSOR = "#ffd84d"

# accents that read well on paper
SKY = "#2f7fc1"
ROSE = "#c9406e"
GOLD = "#c98a0e"
LEAF = "#4b8f2f"
PUMPKIN = "#d0662a"
PLUM = "#8048b8"
RED = "#d9453b"
GREEN = "#5fae3a"
STAR = "#ffcf33"
STAR_EMPTY = "#c9a466"

# console colours (on dark)
OK = "#a6e07f"
WARN = "#ffcf6b"
ERR = "#ff8a7a"
HINT = "#8fd3ff"

SYNTAX = {
    "kw": "#ff8f6b",
    "const": "#ff9e5e",
    "builtin": "#7fd1c7",
    "string": "#b5e07a",
    "number": "#ffc861",
    "comment": "#8c7a66",
    "defname": "#ffd84d",
}


def _rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """Blend colour a towards colour b by fraction t (0..1)."""
    t = max(0.0, min(1.0, t))
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    return "#%02x%02x%02x" % (
        round(ra + (rb - ra) * t),
        round(ga + (gb - ga) * t),
        round(ba + (bb - ba) * t),
    )


def shade(color, factor):
    """factor < 1 darkens, factor > 1 lightens."""
    if factor < 1:
        return mix(color, "#000000", 1 - factor)
    return mix(color, "#ffffff", factor - 1)


def _pick(available, candidates, fallback):
    for name in candidates:
        if name in available:
            return name
    return fallback


class Fonts:
    """Font tuples chosen from what is installed on this computer."""

    def __init__(self, root):
        available = set(tkfont.families(root))
        ui = _pick(available, ["Avenir Next", "Segoe UI", "Helvetica Neue", "Ubuntu", "Arial"], "Helvetica")
        retro = _pick(available, ["Silom", "Rockwell", "Georgia", "Cambria", "DejaVu Serif"], ui)
        mono = _pick(available, ["Menlo", "SF Mono", "Cascadia Code", "Consolas", "DejaVu Sans Mono"], "Courier")
        self.logo = (retro, 64, "bold")
        self.h1 = (retro, 26)
        self.h2 = (retro, 19)
        self.h3 = (retro, 15)
        self.label = (retro, 12)
        self.button = (retro, 14)
        self.dialog = (ui, 17, "bold")
        self.body = (ui, 14)
        self.body_bold = (ui, 14, "bold")
        self.small = (ui, 12)
        self.small_bold = (ui, 12, "bold")
        self.tiny = (ui, 10, "bold")
        self.code = (mono, 15)
        self.code_small = (mono, 13)
