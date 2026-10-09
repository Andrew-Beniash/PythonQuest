"""Python Valley on screen: the walkable overworld and the title screen that pans across it."""

import bisect
import math
import tkinter as tk
from collections import deque

from . import theme as T
from .jobs import GOLD_PER_STAR, JOBS, MAX_GOLD, jobs_in
from .levels import LEVELS, MAX_STARS, WORLDS
from .pixelart import SCALE, TILE_PX
from .widgets import PixelButton, Ticker, frame_box, notched, outlined_text, star_points
from .worldmap import COLS, GATES, PLAYER_LOOK, ROWS, START, ZONES, open_gates

W, H = T.WIDTH, T.HEIGHT
MAP_W, MAP_H = COLS * TILE_PX, ROWS * TILE_PX
GRASSY = ("grass", "grass_dark")
FLAT_PROPS = {"crop0", "crop1", "crop2", "crop3", "lily", "lily_flower"}
SPRITE_H = 26 * SCALE           # outlined character height on screen
MOVE_KEYS = {"left": "left", "a": "left", "right": "right", "d": "right",
             "up": "up", "w": "up", "down": "down", "s": "down"}
ACTION_KEYS = {"e", "space", "return", "kp_enter"}
WALK_SPEED = 5.0                # screen pixels per tick
REACH = 1.45 * TILE_PX          # how close you must be to talk to someone


def lighter(color):
    return T.mix(color, "#ffffff", 0.45)


class WorldView(Ticker, tk.Canvas):
    """Draws the whole valley once; subclasses move the camera around it."""

    def __init__(self, app):
        super().__init__(app, width=W, height=H, bg="#3d6b2a", highlightthickness=0, bd=0,
                         scrollregion=(0, 0, MAP_W, MAP_H))
        self.app, self.art, self.map = app, app.art, app.world
        self.t = 0
        self.cam = (0, 0)
        self.gates_open = open_gates(app.progress)
        self._water = []
        self._water_frame = 0
        self._depth = []
        self._depth_keys = []
        self.villager_items = {}
        self.villager_facing = {}
        self.markers = {}
        self._draw_ground()
        self._draw_things()

    # building -------------------------------------------------------------
    def _mask(self, x, y, matches):
        mask = 0
        for bit, (dx, dy) in ((1, (0, -1)), (2, (1, 0)), (4, (0, 1)), (8, (-1, 0))):
            nx, ny = x + dx, y + dy
            if self.map.in_bounds(nx, ny) and matches(self.map.ground[ny][nx]):
                mask |= bit
        return mask

    def _draw_ground(self):
        m, art = self.map, self.art
        for y in range(ROWS):
            for x in range(COLS):
                kind, variant = m.ground[y][x], m.variant[y][x]
                if kind in GRASSY:
                    image = art.grass(kind, variant)
                elif kind == "water":
                    mask = self._mask(x, y, lambda k: k != "water")
                    image = art.water(mask, 0, variant)
                else:
                    mask = self._mask(x, y, lambda k: k in GRASSY)
                    image = art.ground(kind, mask, m.grass_kind(x, y), variant)
                item = self.create_image(x * TILE_PX, y * TILE_PX, image=image, anchor="nw", tags="ground")
                if kind == "water":
                    self._water.append((item, mask, variant))

    def _draw_things(self):
        """Everything that stands up is created in order of its base line, so nearer things overlap."""
        things = []
        for prop in self.map.props:
            w, h = prop.size
            cx, base = (prop.x + w / 2) * TILE_PX, (prop.y + h) * TILE_PX
            if prop.kind in FLAT_PROPS:
                self.create_image(cx, base - TILE_PX / 2, image=self.art.prop(prop.kind), tags="flat")
            else:
                things.append((base, cx, self.art.prop(prop.kind), None))
        for sign in self.map.signs:
            things.append(((sign.y + 1) * TILE_PX, (sign.x + 0.5) * TILE_PX, self.art.prop("sign"), None))
        for world, tiles in GATES.items():
            if world not in self.gates_open:
                for gx, gy in tiles:
                    things.append(((gy + 1) * TILE_PX, (gx + 0.5) * TILE_PX, self.art.prop("gate"), None))
        for v in self.map.villagers:
            feet = (v.y + 0.85) * TILE_PX
            image = self.art.character(v.name, v.look, "down", 0)
            things.append((feet, (v.x + 0.5) * TILE_PX, image, v))

        for base, cx, image, villager in sorted(things, key=lambda t: (t[0], t[1])):
            item = self.create_image(cx, base + SCALE, image=image, anchor="s")
            self._depth.append((base, item))
            if villager:
                self.villager_items[villager.level_id] = item
                self.villager_facing[villager.level_id] = "down"
        self._depth_keys = [base for base, _ in self._depth]
        self._draw_markers()

    def _draw_markers(self):
        p = self.app.progress
        for v in self.map.villagers:
            index = v.level_index
            kind = "star" if p.is_complete(index) else "exclaim" if p.is_unlocked(index) else "dots"
            x, top = (v.x + 0.5) * TILE_PX, (v.y + 0.85) * TILE_PX + SCALE - SPRITE_H
            item = self.create_image(x, top - 2, image=self.art.bubble(kind), anchor="s", tags="marker")
            self.markers[v.level_id] = (item, kind, x, top - 2)
        self.job_tops = {}
        for job in JOBS:
            prop = self.map.prop_at(job.x, job.y)
            w, h = prop.size
            x = (prop.x + w / 2) * TILE_PX
            top = (prop.y + h) * TILE_PX + SCALE - self.art.prop(prop.kind).height()
            self.job_tops[job.id] = (x, top)
            if p.is_done(job.id):
                kind = "star"
            elif p.is_done(job.requires):
                kind = "coin"
            else:
                continue
            item = self.create_image(x, top - 2, image=self.art.bubble(kind), anchor="s", tags="marker")
            self.markers[job.id] = (item, kind, x, top - 2)

    # per-frame helpers ----------------------------------------------------
    def set_camera(self, x, y):
        x = int(max(0, min(MAP_W - W, x)))
        y = int(max(0, min(MAP_H - H, y)))
        dx, dy = x - self.cam[0], y - self.cam[1]
        if dx or dy:
            self.xview_moveto(x / MAP_W)
            self.yview_moveto(y / MAP_H)
            self.move("hud", dx, dy)
            self.cam = (x, y)

    def animate_world(self):
        if self.t % 18 == 0:
            self._water_frame ^= 1
            for item, mask, variant in self._water:
                self.itemconfigure(item, image=self.art.water(mask, self._water_frame, variant))
        for item, kind, x, y in self.markers.values():
            if kind in ("exclaim", "coin"):
                hop = 3 * round(abs(math.sin(self.t * 0.15)) * 3)
                self.coords(item, x, y - hop)

    def place_movers(self, movers):
        """Slot moving sprites into the right depth among the static things."""
        prev_slot = prev_item = None
        for base, item in sorted(movers):
            slot = bisect.bisect_right(self._depth_keys, base)
            if slot == prev_slot:
                self.tag_raise(item, prev_item)
            elif slot < len(self._depth):
                self.tag_lower(item, self._depth[slot][1])
            else:
                self.tag_raise(item, self._depth[-1][1])
            prev_slot, prev_item = slot, item

    def hud_xy(self, x, y):
        return self.cam[0] + x, self.cam[1] + y


# =========================================================================== dialog box


class Dialog:
    """A Stardew-style text box: typewriter text, a portrait, and choices."""

    TAGS = ("hud", "dialog")

    def __init__(self, view, text, options, portrait=None, name=None):
        self.view, self.full, self.options = view, text, options
        self.shown, self.selected = 0, 0
        f = view.app.fonts
        ox, oy = view.cam
        x1, y1, x2, y2 = ox + 110, oy + H - 262, ox + W - 110, oy + H - 24
        frame_box(view, x1, y1, x2, y2, tags=self.TAGS)
        text_right = x2 - 36
        if portrait:
            px2, py1 = x2 - 30, y1 + 26
            px1, py2 = px2 - 156, py1 + 138
            notched(view, px1, py1, px2, py2, 6, fill=T.PAPER_DARK, outline=T.OUTLINE, width=3, tags=self.TAGS)
            view.create_image((px1 + px2) / 2, py2 - 4, image=portrait, anchor="s", tags=self.TAGS)
            notched(view, px1, py2 + 8, px2, y2 - 26, 5, fill=T.WOOD, outline=T.OUTLINE, width=3, tags=self.TAGS)
            view.create_text((px1 + px2) / 2, (py2 + y2 - 18) / 2, text=name, font=f.h3, fill=T.CREAM,
                             tags=self.TAGS)
            text_right = px1 - 24
        self.text_item = view.create_text(x1 + 36, y1 + 32, anchor="nw", width=text_right - x1 - 36,
                                          font=f.dialog, fill=T.INK, tags=self.TAGS)
        self.option_items = []
        x = x1 + 36
        for i, (label, _callback) in enumerate(options):
            tag = f"option{i}"
            item = view.create_text(x, y2 - 50, anchor="w", text=f"▶ {label}", font=f.h3, fill=T.INK,
                                    tags=(*self.TAGS, tag))
            view.tag_bind(tag, "<Button-1>", lambda e, i=i: self.choose(i))
            view.tag_bind(tag, "<Enter>", lambda e, i=i: self._select(i))
            self.option_items.append(item)
            x = view.bbox(item)[2] + 46
        self._render()

    @property
    def done_typing(self):
        return self.shown >= len(self.full)

    def tick(self):
        if not self.done_typing:
            self.shown = min(len(self.full), self.shown + 2)
            self._render()

    def _render(self):
        self.view.itemconfigure(self.text_item, text=self.full[:self.shown])
        for i, item in enumerate(self.option_items):
            label = self.options[i][0]
            chosen = i == self.selected
            self.view.itemconfigure(item, state="normal" if self.done_typing else "hidden",
                                    text=("▶ " if chosen else "   ") + label,
                                    fill=T.RED if chosen else T.INK_SOFT)

    def _select(self, index):
        self.selected = index
        self._render()

    def move(self, step):
        self._select((self.selected + step) % len(self.options))

    def confirm(self):
        if not self.done_typing:
            self.shown = len(self.full)
            self._render()
        else:
            self.choose(self.selected)

    def cancel(self):
        self.choose(len(self.options) - 1)

    def choose(self, index):
        callback = self.options[index][1]
        self.view.close_dialog()
        if callback:
            callback()


# =========================================================================== the playable valley


class WorldScreen(WorldView):
    def __init__(self, app):
        super().__init__(app)
        state = app.world_state or {}
        start = ((START[0] + 0.5) * TILE_PX, (START[1] + 0.7) * TILE_PX)
        self.px, self.py = state.get("pos", start)
        self.facing = state.get("facing", "down")
        self.robot_x, self.robot_y = state.get("robot", (self.px - 44, self.py - 4))
        self.trail = deque()
        self.keys, self._held, self._release_jobs = set(), set(), {}
        self.walk_t, self.frame = 0, 0
        self.dialog = self.journal = None
        self.banner_until = 0
        self.zone = None
        self._sprite_key = None

        self.player = self.create_image(0, 0, anchor="s")
        self.robot = self.create_image(0, 0, anchor="s")
        self._update_player_sprite(force=True)
        self.set_camera(self.px - W / 2, self.py - H / 2)
        self._draw_hud()

        self.bind("<KeyPress>", self._key_down)
        self.bind("<KeyRelease>", self._key_up)
        self.bind("<Button-1>", lambda e: self.focus_set())
        self.after(60, self.focus_set)

        message = app.pending_message
        app.pending_message = None
        self.zone = self._current_zone()
        if message:
            self.show_banner(message, "Hooray!", T.GOLD, ticks=140)
        elif not state:
            self.show_banner(WORLDS[self.zone].name, "Welcome to Python Valley", WORLDS[self.zone].color)
        self.start_ticking(33)

    # ---------------------------------------------------------------- state
    def save_state(self):
        self.app.world_state = {"pos": (self.px, self.py), "facing": self.facing,
                                "robot": (self.robot_x, self.robot_y)}

    def _current_zone(self):
        zone = self.map.zone_at(int(self.px // TILE_PX), int(self.py // TILE_PX))
        return zone if zone is not None else self.zone

    # ---------------------------------------------------------------- input
    def _key_down(self, event):
        key = event.keysym.lower()
        if key in self._release_jobs:
            self.after_cancel(self._release_jobs.pop(key))
        repeat = key in self._held
        self._held.add(key)

        if self.dialog:
            if key in ("left", "up", "a", "w"):
                self.dialog.move(-1)
            elif key in ("right", "down", "d", "s"):
                self.dialog.move(1)
            elif key in ACTION_KEYS and not repeat:
                self.dialog.confirm()
            elif key == "escape":
                self.dialog.cancel()
            return
        if self.journal:
            if key in ("j", "escape", *ACTION_KEYS) and not repeat:
                self.close_journal()
            return
        if key in MOVE_KEYS:
            self.keys.add(MOVE_KEYS[key])
        elif key in ACTION_KEYS and not repeat:
            self.interact()
        elif key == "j" and not repeat:
            self.open_journal()
        elif key == "escape":
            self.save_state()
            self.app.show_title()

    def _key_up(self, event):
        key = event.keysym.lower()

        def release():
            self._release_jobs.pop(key, None)
            self._held.discard(key)
            if key in MOVE_KEYS:
                self.keys.discard(MOVE_KEYS[key])

        # a short delay hides the fake release/press pairs some systems send on key repeat
        self._release_jobs[key] = self.after(40, release)

    # ---------------------------------------------------------------- frame loop
    def tick(self):
        self.t += 1
        self.animate_world()
        if not (self.dialog or self.journal):
            self._walk()
        self._follow_robot()
        if self.t % 5 == 0:
            self._face_villagers()
        self._update_prompt()
        self.place_movers([(self.py, self.player), (self.robot_y, self.robot)])
        if self.dialog:
            self.dialog.tick()
        if self.banner_until and self.t > self.banner_until:
            self.delete("banner")
            self.banner_until = 0

    def _walk(self):
        dx = ("right" in self.keys) - ("left" in self.keys)
        dy = ("down" in self.keys) - ("up" in self.keys)
        if dx or dy:
            speed = WALK_SPEED / (1.414 if dx and dy else 1)
            wanted = {(1, 0): "right", (-1, 0): "left", (0, 1): "down", (0, -1): "up"}
            options = [wanted[(dx, 0)]] if dx else []
            options += [wanted[(0, dy)]] if dy else []
            if self.facing not in options:
                self.facing = options[0]
            moved = self._try_move(dx * speed, 0) | self._try_move(0, dy * speed)
            self.walk_t += 1
            self.frame = (1, 0, 2, 0)[(self.walk_t // 5) % 4]
            if moved:
                self.trail.append((self.px, self.py))
        else:
            self.walk_t, self.frame = 0, 0
        self._update_player_sprite()

        cx, cy = self.cam
        tx, ty = self.px - W / 2, self.py - H / 2 + 20
        self.set_camera(cx + (tx - cx) * 0.18, cy + (ty - cy) * 0.18)

        zone = self._current_zone()
        if zone != self.zone and zone is not None:
            self.zone = zone
            world = WORLDS[zone]
            self.show_banner(world.name, f"World {zone + 1}  •  {world.tagline}", world.color)
            self._draw_hud()

    def _collides(self, x, y):
        left, right, top, bottom = x - 13, x + 13, y - 10, y + 3
        for ty in range(int(top // TILE_PX), int((bottom - 1) // TILE_PX) + 1):
            for tx in range(int(left // TILE_PX), int((right - 1) // TILE_PX) + 1):
                if self.map.is_blocked(tx, ty, self.gates_open):
                    return True
        return False

    def _try_move(self, dx, dy):
        if not dx and not dy:
            return False
        if not self._collides(self.px + dx, self.py + dy):
            self.px += dx
            self.py += dy
            return True
        step_x, step_y = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
        moved = False
        for _ in range(int(max(abs(dx), abs(dy)))):   # slide right up to the obstacle
            if self._collides(self.px + step_x, self.py + step_y):
                break
            self.px += step_x
            self.py += step_y
            moved = True
        return moved

    def _update_player_sprite(self, force=False):
        key = (self.facing, self.frame)
        if force or key != self._sprite_key:
            self._sprite_key = key
            self.itemconfigure(self.player, image=self.art.character("player", PLAYER_LOOK, *key))
        self.coords(self.player, round(self.px), round(self.py) + SCALE)

    def _follow_robot(self):
        while len(self.trail) > 14:
            tx, ty = self.trail.popleft()
            self.robot_x += (tx - self.robot_x) * 0.5
            self.robot_y += (ty - self.robot_y) * 0.5
        bob = SCALE if (self.t // 10) % 2 else 0
        blink = 1 if self.t % 70 < 4 else 0
        self.itemconfigure(self.robot, image=self.art.mini_robot(blink))
        self.coords(self.robot, round(self.robot_x), round(self.robot_y) - bob + SCALE)

    def _face_villagers(self):
        for v in self.map.villagers:
            vx, vy = (v.x + 0.5) * TILE_PX, (v.y + 0.85) * TILE_PX
            dx, dy = self.px - vx, self.py - vy
            if math.hypot(dx, dy) < 3.2 * TILE_PX:
                facing = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) else ("down" if dy > 0 else "up")
            else:
                facing = "down"
            if facing != self.villager_facing[v.level_id]:
                self.villager_facing[v.level_id] = facing
                self.itemconfigure(self.villager_items[v.level_id],
                                   image=self.art.character(v.name, v.look, facing, 0))

    # ---------------------------------------------------------------- talking
    def _target(self):
        best, best_distance = None, REACH
        px, py = self.px, self.py - 12
        candidates = [("villager", v, v.x, v.y) for v in self.map.villagers]
        candidates += [("sign", s, s.x, s.y) for s in self.map.signs]
        candidates += [("job", job, job.x, job.y) for job in JOBS]
        candidates += [("gate", world, gx, gy) for world, tiles in GATES.items()
                       if world not in self.gates_open for gx, gy in tiles]
        for kind, thing, tx, ty in candidates:
            distance = math.hypot((tx + 0.5) * TILE_PX - px, (ty + 0.5) * TILE_PX - py)
            if distance < best_distance:
                best, best_distance = (kind, thing, tx, ty), distance
        return best

    def _update_prompt(self):
        self.delete("prompt")
        target = None if (self.dialog or self.journal) else self._target()
        if not target:
            return
        kind, thing, tx, ty = target
        x = (tx + 0.5) * TILE_PX
        if kind == "villager":
            y = (ty + 0.85) * TILE_PX - SPRITE_H - 50
        elif kind == "job":
            x, top = self.job_tops[thing.id]
            y = top - 54
        else:
            y = ty * TILE_PX - 26
        notched(self, x - 17, y - 17, x + 17, y + 17, 5, fill=T.CREAM, outline=T.OUTLINE, width=3, tags="prompt")
        self.create_text(x, y, text="E", font=self.app.fonts.h3, fill=T.INK, tags="prompt")

    def interact(self):
        target = self._target()
        if not target:
            return
        kind, thing = target[0], target[1]
        if kind == "villager":
            self._talk_to(thing)
        elif kind == "sign":
            self._read_sign(thing)
        elif kind == "job":
            self._inspect(thing)
        else:
            previous = WORLDS[thing - 1].name
            self.open_dialog(f"The gate is locked tight. Help everyone in {previous} and it will swing open!",
                             [("OK", None)])

    def _talk_to(self, villager):
        p, index = self.app.progress, villager.level_index
        level = LEVELS[index]
        start = (lambda: self._start(level))
        if p.is_complete(index):
            stars = p.best(level.id)
            more = "Want to go for three stars?" if stars < 3 else "Want to play it again?"
            earned = "★" * stars + "☆" * (3 - stars)
            text = f"Thanks again for helping me with “{level.title}”! You earned {earned}.  {more}"
            options = [("Play again", start), ("Bye!", None)]
        elif p.is_unlocked(index):
            text = f"{villager.greeting}\n\n✦ {level.title}  —  learn {level.skill}"
            options = [("Let's code!", start), ("Maybe later", None)]
        else:
            before = self.map.villager_for(LEVELS[index - 1].id)
            where = WORLDS[self.map.zone_at(before.x, before.y)].name
            text = (f"Oh, hello! I'll need your help soon. But first, {before.name} over in {where} "
                    f"is waiting for you.")
            options = [("OK!", None)]
        self.open_dialog(text, options, self.art.portrait(villager.name, villager.look), villager.name)

    def _read_sign(self, sign):
        if sign.world is None:
            text = ("WELCOME TO PYTHON VALLEY!\nWalk with WASD or the arrow keys. Villagers with a red ! need "
                    "your help - stand next to them and press E. Press J to open your journal.")
        else:
            world = WORLDS[sign.world]
            if sign.world in self.gates_open:
                status = "The gate is open - come on through!"
            else:
                status = f"The gate opens once everyone in {WORLDS[sign.world - 1].name} has been helped."
            text = f"→ {world.name.upper()}\n{world.tagline}.\n\n{status}"
        self.open_dialog(text, [("OK", None)])

    def _inspect(self, job):
        p, level = self.app.progress, job.level
        portrait = self.art.prop_icon(job.prop, 130)
        pay = 3 * GOLD_PER_STAR
        if p.is_done(job.id):
            gold = p.best(job.id) * GOLD_PER_STAR
            more = f" Do it again for the full {pay}g?" if gold < pay else " Want to do it again?"
            text = f"{job.intro}\n\nYou already did this odd job and earned {gold} gold.{more}"
            options = [("Again!", lambda: self._start(level)), ("Leave it", None)]
        elif p.is_done(job.requires):
            text = (f"{job.intro}\n\n\u25C6 Odd job: {level.title}  \u2014  learn {level.skill}"
                    f"  \u2022  pays up to {pay} gold")
            options = [("Let's do it!", lambda: self._start(level)), ("Not now", None)]
        else:
            helper = self.map.villager_for(job.requires)
            text = f"{job.idle}\n\n(Maybe something will happen here after you've helped {helper.name}.)"
            options = [("OK", None)]
        self.open_dialog(text, options, portrait, job.name)

    def _start(self, level):
        self.save_state()
        self.app.show_level(level)

    def open_dialog(self, text, options, portrait=None, name=None):
        self.keys.clear()
        self.walk_t, self.frame = 0, 0
        self._update_player_sprite()
        self.dialog = Dialog(self, text, options, portrait, name)

    def close_dialog(self):
        self.delete("dialog")
        self.dialog = None

    # ---------------------------------------------------------------- HUD
    def _draw_hud(self):
        self.delete("hudinfo")
        f, p = self.app.fonts, self.app.progress
        tags = ("hud", "hudinfo")
        ox, oy = self.cam

        x1, y1, x2, y2 = ox + 14, oy + 14, ox + 500, oy + 112
        frame_box(self, x1, y1, x2, y2, tags=tags)
        world = WORLDS[self.zone] if self.zone is not None else WORLDS[0]
        self.create_text(x1 + 28, y1 + 36, anchor="w", text=world.name, font=f.h2, fill=world.color, tags=tags)
        self.create_text(x1 + 28, y1 + 66, anchor="w", text=self._next_goal(), font=f.small_bold,
                         fill=T.INK_SOFT, tags=tags, width=x2 - x1 - 50)

        x1, x2 = ox + W - 270, ox + W - 14
        frame_box(self, x1, y1, x2, y2, tags=tags)
        self.create_polygon(star_points(x1 + 46, y1 + 40, 17), fill=T.STAR, outline=T.OUTLINE, width=3, tags=tags)
        self.create_text(x1 + 74, y1 + 40, anchor="w", text=f"{p.total_stars} / {MAX_STARS}", font=f.h2,
                         fill=T.INK, tags=tags)
        self.create_text(x1 + 28, y1 + 72, anchor="w", text=p.rank(), font=f.small_bold, fill=T.INK_SOFT,
                         tags=tags)
        self.create_oval(x2 - 104, y1 + 64, x2 - 88, y1 + 80, fill=T.STAR, outline=T.OUTLINE, width=2, tags=tags)
        self.create_text(x2 - 82, y1 + 72, anchor="w", text=f"{p.gold}g", font=f.small_bold, fill=T.GOLD,
                         tags=tags)

        keys = "WASD / arrows  walk      E  talk / inspect      J  journal      Esc  menu"
        notched(self, ox + 14, oy + H - 46, ox + 640, oy + H - 12, 5, fill=T.BG_DEEP, outline=T.OUTLINE, width=2,
                tags=tags)
        self.create_text(ox + 30, oy + H - 29, anchor="w", text=keys, font=f.small_bold, fill=T.CREAM_SOFT,
                         tags=tags)
        self.tag_raise("dialog")
        self.tag_raise("journal")

    def _next_goal(self):
        p = self.app.progress
        if all(p.is_complete(i) for i in range(len(LEVELS))):
            return "Everyone in the valley is happy. You're a Python Hero!"
        villager = self.map.villager_for(LEVELS[p.next_index()].id)
        where = WORLDS[self.map.zone_at(villager.x, villager.y)].name
        return f"Next: find {villager.name} (look for the red !) in {where}"

    def show_banner(self, title, subtitle, color, ticks=80):
        self.delete("banner")
        f = self.app.fonts
        ox, oy = self.cam
        tags = ("hud", "banner")
        x1, x2 = ox + W / 2 - 250, ox + W / 2 + 250
        frame_box(self, x1, oy + 130, x2, oy + 236, tags=tags)
        self.create_text(ox + W / 2, oy + 168, text=title, font=f.h1, fill=color, tags=tags)
        self.create_text(ox + W / 2, oy + 206, text=subtitle, font=f.small_bold, fill=T.INK_SOFT, tags=tags)
        self.banner_until = self.t + ticks
        self.tag_raise("dialog")

    # ---------------------------------------------------------------- journal
    def open_journal(self):
        self.keys.clear()
        f, p = self.app.fonts, self.app.progress
        ox, oy = self.cam
        tags = ("hud", "journal")
        x1, y1, x2, y2 = ox + 70, oy + 30, ox + W - 70, oy + H - 30
        frame_box(self, x1, y1, x2, y2, tags=tags)
        outlined_text(self, ox + W / 2, y1 + 46, "Journal", f.h1, width=2, shadow=None, tags=tags)
        self.create_text(x2 - 40, y1 + 46, anchor="e", text=f"Gold {p.gold} / {MAX_GOLD}", font=f.small_bold,
                         fill=T.GOLD, tags=tags)
        col_w, row_h = (x2 - x1 - 80) / 2, (y2 - y1 - 120) / 3
        for w_index, world in enumerate(WORLDS):
            cx = x1 + 40 + (w_index % 2) * col_w
            cy = y1 + 84 + (w_index // 2) * row_h
            indices = [i for i, lv in enumerate(LEVELS) if lv.world is world]
            known = p.is_unlocked(indices[0])
            self.create_text(cx, cy, anchor="nw", text=world.name if known else "???", font=f.h3,
                             fill=world.color if known else T.INK_SOFT, tags=tags)
            for row, index in enumerate(indices):
                level = LEVELS[index]
                villager = self.map.villager_for(level.id)
                y = cy + 28 + row * 22
                if p.is_complete(index):
                    best = p.best(level.id)
                    mark, color = "★" * best + "☆" * (3 - best), T.GOLD
                    line = f"{villager.name} — {level.title}"
                elif p.is_unlocked(index):
                    mark, color, line = "  !  ", T.RED, f"{villager.name} — {level.title}"
                else:
                    mark, color, line = "  •  ", T.PAPER_EDGE, "???"
                self.create_text(cx, y, anchor="nw", text=mark, font=f.small_bold, fill=color, tags=tags)
                self.create_text(cx + 64, y, anchor="nw", text=line, font=f.small_bold,
                                 fill=T.INK if line != "???" else T.PAPER_EDGE, tags=tags)
            for row, job in enumerate(jobs_in(world), start=len(indices)):
                y = cy + 28 + row * 22
                if p.is_done(job.id):
                    mark, color = f"{p.best(job.id) * GOLD_PER_STAR}g", T.GOLD
                    line = f"{job.name} \u2014 {job.level.title}"
                elif p.is_done(job.requires):
                    mark, color, line = "  \u25C6  ", T.GOLD, f"{job.name} \u2014 odd job"
                else:
                    mark, color, line = "  \u2022  ", T.PAPER_EDGE, "???"
                self.create_text(cx, y, anchor="nw", text=mark, font=f.small_bold, fill=color, tags=tags)
                self.create_text(cx + 64, y, anchor="nw", text=line, font=f.small,
                                 fill=T.INK_SOFT if line != "???" else T.PAPER_EDGE, tags=tags)
        self.create_text(ox + W / 2, y2 - 28, text="Press J or Esc to close", font=f.small_bold, fill=T.INK_SOFT,
                         tags=tags)
        self.journal = True

    def close_journal(self):
        self.delete("journal")
        self.journal = None


# =========================================================================== title


class TitleScreen(WorldView):
    """The valley drifts by in the background while the logo sits on top."""

    def __init__(self, app):
        super().__init__(app)
        self._confirm_reset = False
        self.set_camera(*self._camera_at(0))
        self._draw_overlay()
        self.start_ticking(40)

    @staticmethod
    def _camera_at(t):
        return ((MAP_W - W) / 2 + math.sin(t * 0.0045) * (MAP_W - W) / 2,
                (MAP_H - H) / 2 + math.sin(t * 0.0031 + 1) * (MAP_H - H) / 2)

    def _draw_overlay(self):
        f, p = self.app.fonts, self.app.progress
        ox, oy = self.cam
        tags = ("hud", "overlay")
        outlined_text(self, ox + W / 2, oy + 150, "Python Quest", f.logo, width=4, tags=tags)
        notched(self, ox + W / 2 - 230, oy + 222, ox + W / 2 + 230, oy + 266, 6, fill=T.WOOD, outline=T.OUTLINE,
                width=3, tags=tags)
        self.create_text(ox + W / 2, oy + 244, text="a cozy coding adventure in Python Valley", font=f.h3,
                         fill=T.CREAM, tags=tags)

        label = "Continue  ▶" if p.started else "Start  ▶"
        play = PixelButton(self, label, self.app.show_world, T.GREEN, fonts=self.app.fonts, width=220,
                           height=56, bg="#3d6b2a", font=f.h2)
        self.create_window(ox + W / 2, oy + 340, window=play, tags=tags)

        x1, y1 = ox + W / 2 - 200, oy + H - 120
        frame_box(self, x1, y1, x1 + 400, y1 + 92, tags=tags)
        self.create_polygon(star_points(x1 + 50, y1 + 46, 18), fill=T.STAR, outline=T.OUTLINE, width=3, tags=tags)
        self.create_text(x1 + 80, y1 + 34, anchor="w", text=f"{p.total_stars} / {MAX_STARS} stars", font=f.h3,
                         fill=T.INK, tags=tags)
        self.create_text(x1 + 80, y1 + 60, anchor="w", text=f"{p.rank()}   \u2022   {p.gold} gold",
                         font=f.small_bold, fill=T.INK_SOFT,
                         tags=tags)
        if p.started:
            self._reset_item = self.create_text(ox + 24, oy + H - 22, anchor="w", text="Reset progress",
                                                font=f.small_bold, fill=T.CREAM, tags=(*tags, "reset"))
            self.tag_bind("reset", "<Button-1>", lambda e: self._reset())
            self.tag_bind("reset", "<Enter>", lambda e: self.configure(cursor="hand2"))
            self.tag_bind("reset", "<Leave>", lambda e: self.configure(cursor=""))

    def _reset(self):
        if not self._confirm_reset:
            self._confirm_reset = True
            self.itemconfigure(self._reset_item, text="Click again to erase ALL progress", fill="#ffb3a6")
            return
        self.app.progress.reset()
        self.app.world_state = None
        self.app.show_title()

    def tick(self):
        self.t += 1
        self.animate_world()
        self.set_camera(*self._camera_at(self.t))
