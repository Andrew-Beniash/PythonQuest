"""Custom-drawn widgets: wooden pixel buttons, framed panels, a code editor, and Pixel the robot."""

import builtins
import keyword
import math
import random
import re
import tkinter as tk

from . import theme as T

# --------------------------------------------------------------------------- helpers


class Ticker:
    """Mixin: a cancellable animation loop plus one-shot timers, cleaned up on destroy."""

    def start_ticking(self, interval=33):
        self._tick_ms = interval
        self._tick_job = self.after(interval, self._run_tick)

    def _run_tick(self):
        self.tick()
        self._tick_job = self.after(self._tick_ms, self._run_tick)

    def tick(self):
        pass

    def later(self, ms, fn):
        jobs = self.__dict__.setdefault("_jobs", [])
        jobs.append(self.after(ms, fn))

    def destroy(self):
        for job in [getattr(self, "_tick_job", None), *getattr(self, "_jobs", [])]:
            if job:
                self.after_cancel(job)
        super().destroy()


def notched(canvas, x1, y1, x2, y2, n=4, **kw):
    """A rectangle with clipped corners - the classic pixel-art box shape."""
    points = [x1 + n, y1, x2 - n, y1, x2, y1 + n, x2, y2 - n, x2 - n, y2, x1 + n, y2, x1, y2 - n, x1, y1 + n]
    return canvas.create_polygon(points, **kw)


def frame_box(canvas, x1, y1, x2, y2, inner=T.PAPER, tags=()):
    """A wooden frame around a parchment panel, like an RPG menu box."""
    notched(canvas, x1, y1, x2, y2, 8, fill=T.OUTLINE, outline="", tags=tags)
    notched(canvas, x1 + 3, y1 + 3, x2 - 3, y2 - 3, 6, fill=T.WOOD, outline="", tags=tags)
    canvas.create_line(x1 + 9, y1 + 5, x2 - 9, y1 + 5, fill=T.WOOD_LIGHT, width=2, tags=tags)
    canvas.create_line(x1 + 9, y2 - 5, x2 - 9, y2 - 5, fill=T.WOOD_DARK, width=2, tags=tags)
    notched(canvas, x1 + 10, y1 + 10, x2 - 10, y2 - 10, 4, fill=T.OUTLINE, outline="", tags=tags)
    notched(canvas, x1 + 12, y1 + 12, x2 - 12, y2 - 12, 3, fill=inner, outline="", tags=tags)
    canvas.create_line(x1 + 14, y1 + 14, x2 - 14, y1 + 14, fill=T.shade(inner, 0.92), width=2, tags=tags)


def outlined_text(canvas, x, y, text, font, fill=T.STAR, outline=T.OUTLINE, width=3, shadow=T.WOOD_DARK,
                  anchor="center", tags=()):
    """Chunky game-logo text: a thick dark outline, a drop shadow, then the bright face."""
    if shadow:
        for dx in range(-width, width + 1, width):
            canvas.create_text(x + dx, y + width * 2 + 2, text=text, font=font, fill=outline, anchor=anchor,
                               tags=tags)
        canvas.create_text(x, y + width + 2, text=text, font=font, fill=shadow, anchor=anchor, tags=tags)
    for dx in (-width, 0, width):
        for dy in (-width, 0, width):
            if dx or dy:
                canvas.create_text(x + dx, y + dy, text=text, font=font, fill=outline, anchor=anchor, tags=tags)
    return canvas.create_text(x, y, text=text, font=font, fill=fill, anchor=anchor, tags=tags)


def star_points(cx, cy, outer, inner=None, rotation=-90):
    inner = inner or outer * 0.45
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = math.radians(rotation + i * 36)
        points += [cx + radius * math.cos(angle), cy + radius * math.sin(angle)]
    return points


def wood_background(canvas, width, height, tags="bg"):
    """Horizontal planks with seams and knots."""
    rng = random.Random("planks")
    plank = 46
    for i, y in enumerate(range(0, height, plank)):
        tone = T.shade(T.BG, 1.0 + (0.05 if i % 2 else 0))
        canvas.create_rectangle(0, y, width, y + plank, fill=tone, outline="", tags=tags)
        canvas.create_line(0, y, width, y, fill=T.BG_DEEP, width=3, tags=tags)
        canvas.create_line(0, y + 3, width, y + 3, fill=T.shade(T.BG, 1.18), tags=tags)
        x = rng.randrange(-200, 0)
        while x < width:
            x += rng.randrange(220, 420)
            canvas.create_line(x, y, x, y + plank, fill=T.BG_DEEP, width=3, tags=tags)
            if rng.random() < 0.4:
                kx, ky = x - rng.randrange(40, 160), y + plank / 2
                canvas.create_oval(kx - 7, ky - 4, kx + 7, ky + 4, outline=T.BG_DEEP, width=2, tags=tags)


# --------------------------------------------------------------------------- buttons


class PixelButton(tk.Canvas):
    """A chunky pixel-art button with a 3D lip, hover highlight and press animation."""

    def __init__(self, master, text, command, color=T.GREEN, *, fonts, width=150, height=44,
                 text_color=T.CREAM, bg=None, font=None):
        self._depth = 5
        super().__init__(master, width=width, height=height + self._depth, highlightthickness=0, bd=0,
                         bg=bg or master.cget("bg"), cursor="hand2")
        self._width, self._height = width, height
        self._text, self._command, self._color, self._text_color = text, command, color, text_color
        self._font = font or fonts.button
        self._hover = self._pressed = False
        self._enabled = True
        self.bind("<Enter>", lambda e: self._set(hover=True))
        self.bind("<Leave>", lambda e: self._set(hover=False, pressed=False))
        self.bind("<ButtonPress-1>", lambda e: self._set(pressed=True))
        self.bind("<ButtonRelease-1>", self._release)
        self._draw()

    def _set(self, hover=None, pressed=None):
        if hover is not None:
            self._hover = hover
        if pressed is not None:
            self._pressed = pressed
        self._draw()

    def _release(self, event):
        was_pressed = self._pressed
        self._set(pressed=False)
        inside = 0 <= event.x <= self._width and 0 <= event.y <= self._height + self._depth
        if was_pressed and inside and self._enabled and self._command:
            self._command()

    def configure_button(self, text=None, enabled=None, color=None):
        if text is not None:
            self._text = text
        if color is not None:
            self._color = color
        if enabled is not None:
            self._enabled = enabled
            self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h, d = self._width, self._height, self._depth
        if self._enabled:
            face = T.shade(self._color, 1.15) if self._hover else self._color
            label = self._text_color
        else:
            face, label = "#8a7a68", "#cbbca8"
        offset = d - 1 if (self._pressed and self._enabled) else 0
        notched(self, 0, d, w, h + d, 5, fill=T.OUTLINE, outline="")
        notched(self, 2, d, w - 2, h + d - 2, 4, fill=T.shade(face, 0.62), outline="")
        notched(self, 0, offset, w, h + offset, 5, fill=T.OUTLINE, outline="")
        notched(self, 2, offset + 2, w - 2, h + offset - 2, 4, fill=face, outline="")
        self.create_line(6, offset + 5, w - 6, offset + 5, fill=T.shade(face, 1.3), width=2)
        self.create_text(w / 2 + 1, h / 2 + offset + 2, text=self._text, font=self._font, fill=T.shade(face, 0.5))
        self.create_text(w / 2, h / 2 + offset, text=self._text, font=self._font, fill=label)


# --------------------------------------------------------------------------- syntax highlighting

_TOKEN_RE = re.compile(
    r"(?P<comment>#[^\n]*)"
    r"|(?P<string>[rRbBuUfF]{0,2}(?:\"\"\"[\s\S]*?(?:\"\"\"|$)|'''[\s\S]*?(?:'''|$)|\"[^\"\n]*\"?|'[^'\n]*'?))"
    r"|(?P<number>\b\d+(?:\.\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_]\w*)"
)
_CONSTS = {"True", "False", "None"}
_KEYWORDS = set(keyword.kwlist) - _CONSTS
_BUILTINS = {name for name in dir(builtins) if not name.startswith("_")}


def setup_code_tags(widget):
    for tag, color in T.SYNTAX.items():
        widget.tag_configure(tag, foreground=color)


def highlight(widget):
    code = widget.get("1.0", "end-1c")
    for tag in T.SYNTAX:
        widget.tag_remove(tag, "1.0", "end")
    previous = None
    for match in _TOKEN_RE.finditer(code):
        kind, tag = match.lastgroup, None
        if kind == "word":
            word = match.group()
            if previous in ("def", "class"):
                tag = "defname"
            elif word in _CONSTS:
                tag = "const"
            elif word in _KEYWORDS:
                tag = "kw"
            elif word in _BUILTINS:
                tag = "builtin"
            previous = word
        else:
            tag, previous = kind, None
        if tag:
            widget.tag_add(tag, f"1.0+{match.start()}c", f"1.0+{match.end()}c")


def code_view(master, code, font, bg=T.EDITOR_BG, width=40):
    """A small read-only, highlighted code snippet."""
    lines = code.split("\n")
    view = tk.Text(master, height=len(lines), width=width, font=font, bg=bg, fg=T.CODE_TEXT, bd=0,
                   highlightthickness=2, highlightbackground=T.OUTLINE, padx=12, pady=6, wrap="none",
                   cursor="arrow", takefocus=0)
    setup_code_tags(view)
    view.insert("1.0", code)
    highlight(view)
    view.configure(state="disabled")
    return view


class CodeEditor(tk.Frame):
    """Text editor with line numbers, live highlighting and Python-friendly indenting."""

    def __init__(self, master, fonts, on_run=None, height=12):
        super().__init__(master, bg=T.EDITOR_BG, highlightthickness=3, highlightbackground=T.OUTLINE,
                         highlightcolor=T.WOOD_LIGHT)
        self._on_run = on_run
        self._pending = None
        common = dict(font=fonts.code, bd=0, highlightthickness=0, pady=12, spacing1=3, spacing3=3,
                      wrap="none", height=height)
        self.gutter = tk.Text(self, width=3, bg=T.shade(T.EDITOR_BG, 0.85), fg=T.GUTTER, padx=10, takefocus=0,
                              cursor="arrow", **common)
        self.gutter.tag_configure("right", justify="right")
        self.gutter.tag_configure("err", foreground=T.ERR)
        self.text = tk.Text(self, bg=T.EDITOR_BG, fg=T.CODE_TEXT, insertbackground=T.CURSOR, insertwidth=3,
                            selectbackground=T.SELECTION, selectforeground=T.CODE_TEXT, padx=8, undo=True,
                            maxundo=-1, autoseparators=True, **common)
        self.gutter.pack(side="left", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        setup_code_tags(self.text)
        self.text.tag_configure("errline", background="#5a2a22")
        self.text.tag_raise("sel")
        self.text.configure(yscrollcommand=lambda first, _last: self.gutter.yview_moveto(first))

        self.text.bind("<<Modified>>", self._modified)
        self.text.bind("<Tab>", self._tab)
        self.text.bind("<Shift-Tab>", self._dedent)
        self.text.bind("<Return>", self._newline)
        self.text.bind("<BackSpace>", self._backspace)
        for sequence in ("<Control-Return>", "<Command-Return>", "<Shift-Return>"):
            try:
                self.text.bind(sequence, self._run_shortcut)
            except tk.TclError:
                pass  # "Command" only exists on macOS
        self.gutter.bind("<MouseWheel>", lambda e: self.text.event_generate("<MouseWheel>", delta=e.delta))
        self._refresh()

    # public ---------------------------------------------------------------
    def get(self):
        return self.text.get("1.0", "end-1c")

    def set(self, code):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", code)
        self.text.edit_reset()
        self.text.mark_set("insert", "end-1c")
        self._refresh()

    def focus(self):
        self.text.focus_set()

    def mark_error(self, line):
        self.clear_error()
        if not line:
            return
        self.text.tag_add("errline", f"{line}.0", f"{line}.0 lineend +1c")
        self.gutter.tag_add("err", f"{line}.0", f"{line}.0 lineend")
        self.text.see(f"{line}.0")

    def clear_error(self):
        self.text.tag_remove("errline", "1.0", "end")
        self.gutter.tag_remove("err", "1.0", "end")

    # internals ------------------------------------------------------------
    def _modified(self, _event=None):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self.clear_error()
            if self._pending is None:
                self._pending = self.after_idle(self._refresh)

    def _refresh(self):
        self._pending = None
        highlight(self.text)
        lines = int(self.text.index("end-1c").split(".")[0])
        self.gutter.configure(state="normal")
        self.gutter.delete("1.0", "end")
        self.gutter.insert("1.0", "\n".join(str(n) for n in range(1, lines + 1)), "right")
        self.gutter.configure(state="disabled")
        self.gutter.yview_moveto(self.text.yview()[0])

    def _run_shortcut(self, _event):
        if self._on_run:
            self._on_run()
        return "break"

    def _selected_lines(self):
        if self.text.tag_ranges("sel"):
            first = int(self.text.index("sel.first").split(".")[0])
            last = int(self.text.index("sel.last").split(".")[0])
            return range(first, last + 1)
        return None

    def _tab(self, _event):
        lines = self._selected_lines()
        if lines:
            for n in lines:
                self.text.insert(f"{n}.0", "    ")
        else:
            self.text.insert("insert", "    ")
        return "break"

    def _dedent(self, _event):
        line_no = int(self.text.index("insert").split(".")[0])
        for n in self._selected_lines() or [line_no]:
            start = self.text.get(f"{n}.0", f"{n}.4")
            remove = len(start) - len(start.lstrip(" "))
            if remove:
                self.text.delete(f"{n}.0", f"{n}.{remove}")
        return "break"

    def _newline(self, _event):
        line = self.text.get("insert linestart", "insert")
        indent = re.match(r"[ \t]*", line).group()
        stripped = line.strip()
        if stripped.endswith(":"):
            indent += "    "
        elif stripped in ("pass", "break", "continue") or stripped.startswith("return"):
            indent = indent[:-4]
        self.text.insert("insert", "\n" + indent)
        self.text.see("insert")
        return "break"

    def _backspace(self, _event):
        if self.text.tag_ranges("sel"):
            return None
        before = self.text.get("insert linestart", "insert")
        if before and before.strip() == "" and "\t" not in before:
            remove = (len(before) - 1) % 4 + 1
            self.text.delete(f"insert -{remove}c", "insert")
            return "break"
        return None


# --------------------------------------------------------------------------- Pixel the robot


class Mascot(Ticker, tk.Canvas):
    """Pixel (as pixel art) with a speech bubble. Call say(text, mood) to make it react."""

    def __init__(self, master, fonts, art, width=380, height=140, bg=T.PAPER):
        super().__init__(master, width=width, height=height, bg=bg, highlightthickness=0, bd=0)
        self.fonts, self.art = fonts, art
        self._width, self._height = width, height
        self.mood, self.message, self.t = "idle", "", 0
        self._mood_until = 0
        self._blink = 0
        self._robot = self.create_image(56, height - 8, anchor="s")
        self._bubble_tags = "bubble"
        self.start_ticking(40)

    def say(self, message, mood="idle", hold=60):
        self.message, self.mood = message, mood
        self._mood_until = self.t + hold if mood != "idle" else 0
        self._draw_bubble()
        self.tick()

    def tick(self):
        self.t += 1
        if self._mood_until and self.t > self._mood_until and self.mood in ("happy", "sad"):
            self.mood, self._mood_until = "idle", 0
            self._draw_bubble()
        if self._blink:
            self._blink -= 1
        elif random.random() < 0.02:
            self._blink = 3

        mood = "blink" if self._blink and self.mood in ("idle", "think") else self.mood
        x, y = 56, self._height - 8
        if self.mood == "happy":
            y -= round(abs(math.sin(self.t * 0.25)) * 4) * 3
        elif self.mood == "sad":
            remaining = max(0, self._mood_until - self.t)
            x += round(math.sin(self.t * 1.3) * min(2, remaining * 0.1)) * 3
        else:
            y -= 3 if (self.t // 12) % 2 else 0
        self.itemconfigure(self._robot, image=self.art.robot(mood))
        self.coords(self._robot, x, y)

    def _draw_bubble(self):
        self.delete(self._bubble_tags)
        if not self.message:
            return
        left, top, right = 124, 8, self._width - 4
        text = self.create_text(left + 16, top + 12, text=self.message, anchor="nw", width=right - left - 30,
                                font=self.fonts.small_bold, fill=T.INK, tags=self._bubble_tags)
        bottom = max(self.bbox(text)[3] + 12, top + 50)
        color = {"happy": "#e3f5c8", "sad": "#ffe0d6", "think": "#fff3c2"}.get(self.mood, "#fffaf0")
        box = notched(self, left, top, right, bottom, 6, fill=color, outline=T.OUTLINE, width=3,
                      tags=self._bubble_tags)
        tail_y = min(bottom - 16, top + 34)
        tail = self.create_polygon(left + 2, tail_y - 8, left - 12, tail_y + 4, left + 2, tail_y + 6,
                                   fill=color, outline=T.OUTLINE, width=3, tags=self._bubble_tags)
        cover = self.create_line(left + 2, tail_y - 6, left + 2, tail_y + 4, fill=color, width=4,
                                 tags=self._bubble_tags)
        self.tag_lower(cover, text)
        self.tag_lower(tail, cover)
        self.tag_lower(box, tail)


# --------------------------------------------------------------------------- confetti

CONFETTI_COLORS = [T.STAR, T.ROSE, T.SKY, T.GREEN, T.PUMPKIN, T.PLUM, T.CREAM]


class Confetti:
    def __init__(self, canvas, width, height, count=140):
        self.canvas, self.height = canvas, height
        self.bits = [
            {
                "x": random.uniform(0, width), "y": random.uniform(-height, -10),
                "vx": random.uniform(-1.2, 1.2), "vy": random.uniform(2.5, 6),
                "spin": random.uniform(0, 6.28), "rate": random.uniform(0.1, 0.3),
                "size": random.choice([6, 9, 12]), "color": random.choice(CONFETTI_COLORS),
            }
            for _ in range(count)
        ]

    def step(self):
        self.canvas.delete("confetti")
        for bit in self.bits:
            bit["x"] += bit["vx"] + math.sin(bit["spin"]) * 0.8
            bit["y"] += bit["vy"]
            bit["spin"] += bit["rate"]
            if bit["y"] > self.height + 20:
                continue
            w = 3 * max(1, round(bit["size"] * abs(math.cos(bit["spin"])) / 3))
            h = 6
            self.canvas.create_rectangle(bit["x"] - w / 2, bit["y"] - h / 2, bit["x"] + w / 2, bit["y"] + h / 2,
                                         fill=bit["color"], outline="", tags="confetti")
