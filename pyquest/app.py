"""The main window: owns progress, the valley and the sprite cache, and switches screens."""

import tkinter as tk

from . import theme as T
from .pixelart import Art
from .progress import Progress
from .screens import LevelScreen, VictoryScreen
from .valley import TitleScreen, WorldScreen
from .worldmap import WorldMap


class App(tk.Tk):
    def __init__(self, progress=None):
        super().__init__()
        self.title("Python Quest")
        self.configure(bg=T.BG)
        self.resizable(False, False)
        x = max(0, (self.winfo_screenwidth() - T.WIDTH) // 2)
        y = max(0, (self.winfo_screenheight() - T.HEIGHT) // 3)
        self.geometry(f"{T.WIDTH}x{T.HEIGHT}+{x}+{y}")
        self.fonts = T.Fonts(self)
        self.progress = progress or Progress()
        self.art = Art()
        self.world = WorldMap()
        self.world_state = None       # where the player stood when they left the valley
        self.pending_message = None   # e.g. "The gate to ... is open!"
        self.screen = None
        self.protocol("WM_DELETE_WINDOW", self.quit_game)
        self.show_title()

    def _swap(self, factory):
        if isinstance(self.screen, LevelScreen):
            self.screen.save_draft()
        if isinstance(self.screen, WorldScreen):
            self.screen.save_state()
        if self.screen is not None:
            self.screen.destroy()
        self.screen = factory()
        self.screen.pack(fill="both", expand=True)

    def show_title(self):
        self._swap(lambda: TitleScreen(self))

    def show_world(self):
        self._swap(lambda: WorldScreen(self))

    def show_level(self, level):
        self._swap(lambda: LevelScreen(self, level))

    def show_victory(self, level, stars, new_best):
        self._swap(lambda: VictoryScreen(self, level, stars, new_best))

    def quit_game(self):
        if isinstance(self.screen, LevelScreen):
            self.screen.save_draft()
        self.progress.save()
        self.destroy()


def main():
    App().mainloop()
