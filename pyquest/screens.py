"""The coding challenge screen and the victory screen."""

import math
import tkinter as tk

from . import theme as T
from .checker import check
from .jobs import GOLD_PER_STAR, JOBS_BY_ID
from .levels import LEVELS, MAX_STARS, WORLDS, level_code
from .progress import stars_for
from .widgets import (Confetti, CodeEditor, Mascot, PixelButton, Ticker, code_view, frame_box, outlined_text,
                      star_points, wood_background)

W, H = T.WIDTH, T.HEIGHT


def lighter(color):
    return T.mix(color, "#ffffff", 0.45)


def world_indices(world):
    return [i for i, lv in enumerate(LEVELS) if lv.world is world]


class Giver:
    """Who (or what) handed out a task: a villager, or a thing on the map for odd jobs."""

    def __init__(self, app, level):
        self.job = JOBS_BY_ID.get(level.id)
        if self.job:
            self.name, self.kind = self.job.name, "Odd job"
            self.small = app.art.prop_icon(self.job.prop, 56)
            self.big = app.art.prop_icon(self.job.prop, 130)
        else:
            villager = app.world.villager_for(level.id)
            self.name, self.kind = villager.name, "Quest from"
            self.small = app.art.portrait(villager.name, villager.look, scale=3)
            self.big = app.art.portrait(villager.name, villager.look)


# =========================================================================== level


class LevelScreen(Ticker, tk.Frame):
    LEFT_WIDTH = 430

    def __init__(self, app, level):
        super().__init__(app, bg=T.BG, padx=22, pady=10)
        self.app, self.level = app, level
        self.giver = Giver(app, level)
        self.index = None if self.giver.job else LEVELS.index(level)
        self.hints_used = 0
        self.solved = False
        self._build_top()
        body = tk.Frame(self, bg=T.BG)
        body.pack(fill="both", expand=True, pady=(10, 0))
        body.columnconfigure(0, minsize=self.LEFT_WIDTH)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self._build_left(body)
        self._build_right(body)

        draft = app.progress.drafts.get(self.level.id)
        self.editor.set(draft if draft is not None else self.level.starter)
        self.editor.focus()
        self.mascot.say(self._intro(), "idle")

    def _intro(self):
        if self.app.progress.is_done(self.level.id):
            return "You've solved this one already! Try again for 3 stars?"
        return "Read the mission, write your code, then press Run!"

    # layout ---------------------------------------------------------------
    def _build_top(self):
        f, world = self.app.fonts, self.level.world
        bar = tk.Frame(self, bg=T.BG)
        bar.pack(fill="x")
        PixelButton(bar, "◀ Valley", self.leave, T.WOOD, fonts=f, width=118, height=40,
                    font=f.label).pack(side="left")
        titles = tk.Frame(bar, bg=T.BG)
        titles.pack(side="left", padx=18)
        where = "ODD JOB" if self.giver.job else f"CHALLENGE {level_code(self.index)}"
        tk.Label(titles, text=f"{world.name.upper()}  •  {where}", font=f.tiny,
                 fg=lighter(world.color), bg=T.BG).pack(anchor="w")
        tk.Label(titles, text=self.level.title, font=f.h1, fg=T.CREAM, bg=T.BG).pack(anchor="w")

        p = self.app.progress
        right = tk.Frame(bar, bg=T.BG)
        right.pack(side="right")
        tk.Label(right, image=self.giver.small, bg=T.PAPER_DARK, highlightthickness=3,
                 highlightbackground=T.OUTLINE).pack(side="right", padx=(12, 0))
        info = tk.Frame(right, bg=T.BG)
        info.pack(side="right")
        tk.Label(info, text=f"{self.giver.kind}: {self.giver.name}", font=f.label, fg=T.CREAM,
                 bg=T.BG).pack(anchor="e")
        best = p.best(self.level.id)
        best_text = "Best: " + "★" * best + "☆" * (3 - best) if best else "Not solved yet"
        total = f"pays up to {3 * GOLD_PER_STAR}g" if self.giver.job else f"★ {p.total_stars}/{MAX_STARS}"
        tk.Label(info, text=f"{best_text}     {total}", font=f.small_bold, fg=T.STAR, bg=T.BG).pack(anchor="e")

    def _section(self, parent, title, color):
        tk.Label(parent, text=title, font=self.app.fonts.label, fg=color, bg=T.PAPER).pack(anchor="w", pady=(8, 2))

    def _build_left(self, body):
        f, lv = self.app.fonts, self.level
        wrap = self.LEFT_WIDTH - 58
        wood = tk.Frame(body, bg=T.WOOD, padx=5, pady=5, highlightthickness=3, highlightbackground=T.OUTLINE)
        wood.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        card = tk.Frame(wood, bg=T.PAPER, padx=18, pady=4, highlightthickness=2, highlightbackground=T.OUTLINE)
        card.pack(fill="both", expand=True)

        self.mascot = Mascot(card, f, self.app.art, width=self.LEFT_WIDTH - 62, height=134)
        self.mascot.pack(side="bottom", fill="x", pady=(2, 4))

        self._section(card, "MISSION", lv.world.color)
        tk.Label(card, text=lv.story, font=f.body, fg=T.INK, bg=T.PAPER, wraplength=wrap,
                 justify="left").pack(anchor="w")

        self._section(card, f"NEW SKILL • {lv.skill.upper()}", T.SKY)
        tk.Label(card, text=lv.concept, font=f.small, fg=T.INK_SOFT, bg=T.PAPER, wraplength=wrap,
                 justify="left").pack(anchor="w")
        code_view(card, lv.example, f.code_small).pack(anchor="w", fill="x", pady=(5, 0))

        self._section(card, "YOUR TASK", T.RED)
        tk.Label(card, text=lv.task, font=f.body_bold, fg=T.INK, bg=T.PAPER, wraplength=wrap,
                 justify="left").pack(anchor="w")

        if lv.given:
            self._section(card, "GIVEN • ALREADY SET FOR YOU", T.PLUM)
            lines = "\n".join(f"{name} = {value!r}" for name, value in lv.given.items())
            code_view(card, lines, f.code_small).pack(anchor="w", fill="x")
            tk.Label(card, text="Pixel will also test your code with other values!", font=f.small,
                     fg=T.INK_SOFT, bg=T.PAPER).pack(anchor="w", pady=(2, 0))

    def _build_right(self, body):
        f = self.app.fonts
        right = tk.Frame(body, bg=T.BG)
        right.grid(row=0, column=1, sticky="nsew")

        head = tk.Frame(right, bg=T.BG)
        head.pack(fill="x")
        tk.Label(head, text="  main.py  ", font=f.small_bold, fg=T.CODE_TEXT, bg=T.EDITOR_BG, pady=5,
                 highlightthickness=3, highlightbackground=T.OUTLINE).pack(side="left")
        tk.Label(head, text="Ctrl/⌘ + Enter to run", font=f.small, fg=T.CREAM_SOFT, bg=T.BG).pack(side="right")
        self.editor = CodeEditor(right, f, on_run=self.run_code, height=10)
        self.editor.pack(fill="x")

        buttons = tk.Frame(right, bg=T.BG)
        buttons.pack(fill="x", pady=10)
        self.run_button = PixelButton(buttons, "▶ Run", self.run_code, T.GREEN, fonts=f, width=140)
        self.run_button.pack(side="left")
        self.hint_button = PixelButton(buttons, "Hint", self.show_hint, T.STAR, fonts=f, width=130,
                                       text_color=T.INK)
        self.hint_button.pack(side="left", padx=12)
        PixelButton(buttons, "↺ Reset", self.reset_code, T.WOOD, fonts=f, width=118).pack(side="left")
        self.stars_label = tk.Label(buttons, font=f.h2, fg=T.STAR, bg=T.BG)
        self.stars_label.pack(side="right")
        tk.Label(buttons, text="Playing for", font=f.small, fg=T.CREAM_SOFT, bg=T.BG).pack(side="right", padx=8)
        self._update_stars()

        tk.Label(right, text="CONSOLE", font=f.label, fg=T.CREAM_SOFT, bg=T.BG).pack(anchor="w", pady=(0, 4))
        self.console = tk.Text(right, font=f.code_small, bg=T.CONSOLE_BG, fg=T.CODE_TEXT, bd=0, height=6,
                               highlightthickness=3, highlightbackground=T.OUTLINE, padx=14, pady=10,
                               wrap="word", state="disabled", cursor="arrow", spacing1=1, spacing3=1)
        self.console.pack(fill="both", expand=True)
        for tag, color in (("out", T.CODE_TEXT), ("muted", T.GUTTER), ("err", T.ERR), ("ok", T.OK),
                           ("warn", T.WARN), ("hint", T.HINT)):
            self.console.tag_configure(tag, foreground=color)
        self._write([("Ready. Your program's output will appear here.\n", "muted")])

    # actions --------------------------------------------------------------
    def _update_stars(self):
        stars = stars_for(self.hints_used)
        self.stars_label.configure(text="★" * stars + "☆" * (3 - stars))
        left = len(self.level.hints) - self.hints_used
        self.hint_button.configure_button(text=f"Hint ({left})" if left else "No hints", enabled=left > 0)

    def _write(self, parts, clear=True):
        self.console.configure(state="normal")
        if clear:
            self.console.delete("1.0", "end")
        for text, tag in parts:
            self.console.insert("end", text, tag)
        self.console.configure(state="disabled")
        self.console.see("end")

    def run_code(self):
        if self.solved:
            return
        code = self.editor.get()
        self.app.progress.set_draft(self.level.id, code)
        result = check(self.level, code)

        parts = [("▶ Running main.py\n", "muted")]
        parts.append((result.output.rstrip("\n") + "\n", "out") if result.output else ("(no output)\n", "muted"))
        if result.error:
            line = f" (line {result.error_line})" if result.error_line else ""
            parts.append((f"\n{result.error}{line}\n", "err"))
        parts.append((f"\n{result.headline}  ", "ok" if result.passed else "warn"))
        parts.append((result.detail + "\n", "out" if result.passed else "warn"))
        self._write(parts)

        if result.passed:
            self.solved = True
            self.run_button.configure_button(enabled=False)
            self.mascot.say(f"{result.headline} {result.detail}", "happy", hold=200)
            first_time = not self.app.progress.is_done(self.level.id)
            stars = stars_for(self.hints_used)
            new_best = self.app.progress.record(self.level.id, stars)
            self.app.progress.save()
            if not self.giver.job:
                self._announce_gate(first_time)
            self.later(1600, lambda: self.app.show_victory(self.level, stars, new_best))
        else:
            self.editor.mark_error(result.error_line)
            mood = "sad" if result.error else "think"
            short = result.detail.split("\n")[0]
            self.mascot.say(f"{result.headline} {short}", mood, hold=70)

    def _announce_gate(self, first_time):
        """Finishing a whole world for the first time opens the gate to the next one."""
        world_no = WORLDS.index(self.level.world)
        p = self.app.progress
        if first_time and world_no + 1 < len(WORLDS) and all(p.is_complete(i) for i in world_indices(self.level.world)):
            self.app.pending_message = f"The gate to {WORLDS[world_no + 1].name} is open!"

    def show_hint(self):
        if self.hints_used >= len(self.level.hints):
            return
        hint = self.level.hints[self.hints_used]
        self.hints_used += 1
        self._update_stars()
        label = "Answer" if self.hints_used == len(self.level.hints) else f"Hint {self.hints_used}"
        self._write([(f"✦ {label}:\n", "hint"), (hint + "\n", "hint")], clear=False)
        if "\n" in hint:
            self.mascot.say("Here's the whole answer - it's in the console. Type it in yourself!", "think")
        else:
            self.mascot.say(hint, "think")

    def reset_code(self):
        self.editor.set(self.level.starter)
        self.editor.focus()
        self.mascot.say("Fresh start! You've got this.", "idle")

    def save_draft(self):
        self.app.progress.set_draft(self.level.id, self.editor.get())
        self.app.progress.save()

    def leave(self):
        self.app.show_world()


# =========================================================================== victory


class VictoryScreen(Ticker, tk.Canvas):
    def __init__(self, app, level, stars, new_best):
        super().__init__(app, width=W, height=H, bg=T.BG, highlightthickness=0)
        self.app, self.level, self.stars, self.t = app, level, stars, 0
        self.giver = Giver(app, level)
        self.final = not self.giver.job and all(app.progress.is_complete(i) for i in range(len(LEVELS)))
        wood_background(self, W, H)
        self.confetti = Confetti(self, W, H, count=200 if self.final else 120)
        self._draw_card(new_best)
        self.start_ticking(30)

    def _draw_card(self, new_best):
        f, world, p = self.app.fonts, self.level.world, self.app.progress
        x1, y1, x2, y2 = W / 2 - 360, 110, W / 2 + 360, 660
        self.card = (x1, y1, x2, y2)
        frame_box(self, x1, y1, x2, y2)

        if self.giver.job:
            heading, where = "Odd job done!", "ODD JOB"
        else:
            heading = "Valley saved!" if self.final else "Challenge complete!"
            where = level_code(LEVELS.index(self.level))
        self.create_text(W / 2, y1 + 50, text=f"{world.name.upper()}  •  {where}", font=f.label,
                         fill=world.color)
        outlined_text(self, W / 2, y1 + 100, heading, f.h1, width=3)
        self.create_text(W / 2, y1 + 146, text=self.level.title, font=f.h3, fill=T.INK_SOFT)
        self.star_center_y = y1 + 222

        if self.giver.job:
            quote = f"{self.level.praise}\nYou earned {self.stars * GOLD_PER_STAR} gold!"
        else:
            quote = f"“Thank you so much!” says {self.giver.name}.\n{self.level.praise}"
        if self.final:
            quote = "You helped every villager in Python Valley. You are a true PYTHON HERO!"
        self.create_text(W / 2, y1 + 316, text=quote, font=f.body_bold, fill=T.INK, width=430, justify="center")

        note = "New best score saved!" if new_best else f"Your best is still {p.best(self.level.id)} stars."
        if self.stars < 3:
            note += "  Solve it without hints for ★★★"
        self.create_text(W / 2, y1 + 384, text=note, font=f.small_bold, fill=T.INK_SOFT)
        if self.app.pending_message:
            self.create_text(W / 2, y1 + 410, text=self.app.pending_message, font=f.small_bold, fill=T.LEAF)

        self.create_image(x2 - 30, y2 - 24, image=self.giver.big, anchor="se")
        self._robot = self.create_image(x1 + 36, y2 - 24, anchor="sw")

        buttons = [("Back to the valley ▶", self.app.show_world, T.GREEN, 280),
                   ("Replay", lambda: self.app.show_level(self.level), T.WOOD, 130)]
        x = W / 2 - (sum(b[3] for b in buttons) + 16) / 2
        for label, command, color, width in buttons:
            button = PixelButton(self, label, command, color, fonts=f, width=width, height=50, bg=T.PAPER)
            self.create_window(x, y2 - 70, window=button, anchor="w")
            x += width + 16
        self.create_text(W / 2, H - 40, text=f"★ {p.total_stars}/{MAX_STARS}     {p.rank()}     {p.gold} gold",
                         font=f.h3, fill=T.STAR)

    def tick(self):
        self.t += 1
        self.confetti.step()
        self.delete("bigstars")
        for s in range(3):
            appear = self.t - 12 - s * 10
            if appear < 0:
                scale = 0.0
            else:
                scale = min(1.0, appear / 6) + max(0.0, 0.25 * math.sin(min(appear, 12) / 12 * math.pi))
            cx, cy = W / 2 + (s - 1) * 110, self.star_center_y - (12 if s == 1 else 0)
            self.create_polygon(star_points(cx, cy, 46), fill=T.PAPER_DARK, outline=T.PAPER_EDGE, width=3,
                                tags="bigstars")
            if s < self.stars and scale > 0:
                self.create_polygon(star_points(cx, cy, 46 * scale), fill=T.STAR, outline=T.OUTLINE, width=3,
                                    tags="bigstars")
        x1, _y1, _x2, y2 = self.card
        hop = 3 * round(abs(math.sin(self.t * 0.18)) * 6)
        self.itemconfigure(self._robot, image=self.app.art.robot("happy"))
        self.coords(self._robot, x1 + 36, y2 - 24 - hop)
        self.tag_raise("confetti")
