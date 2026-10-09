# Python Quest

A cozy pixel-art farming-village adventure for learning Python. Walk your farmer around
**Python Valley** with Pixel the robot trotting behind you, find villagers who need help, and
solve their problems by writing real Python code.

## The valley

Six zones, each teaching one idea. Every zone has 4 villagers, and each villager gives you one challenge.

| Zone                | Where              | You learn                                             |
| ------------------- | ------------------ | ----------------------------------------------------- |
| 1 · Print Plains    | your farm          | `print()`, strings, math                              |
| 2 · Variable Valley | the village square | variables, updating values, f-strings, `int()`        |
| 3 · Logic Lagoon    | the lake and dock  | `if`, `else`, `elif`, `and`                           |
| 4 · Loop Mountain   | rocky hills        | `for`, `range()`, running totals, `while`             |
| 5 · List Labs       | the market         | lists, indexes, `append()`, `len()`, looping lists    |
| 6 · Function Forge  | the old mine       | `def`, `return`, `%`, booleans, and the FizzBuzz boss |

Zones are separated by hedges with locked wooden gates. A gate swings open once you've helped
everyone in the zone before it.

## Odd jobs

Besides the villagers, 13 things around the valley have bonus coding jobs. Walk up to one and press E
to inspect it. A **gold coin** bubble shows that a job is ready. Each job unlocks after you've helped
a particular villager, and it pays **gold** (up to 30 per job) instead of stars.

| Zone            | Odd jobs                          | Extra skills                                        |
| --------------- | --------------------------------- | --------------------------------------------------- |
| Print Plains    | Mailbox, Scarecrow                | `\n` new lines, `//` and `%`                        |
| Variable Valley | Wishing Well, Street Lamp         | `.upper()` / `.lower()`, f-strings with many values |
| Logic Lagoon    | Tackle Box, Berry Bush            | `or`, `not`                                         |
| Loop Mountain   | Boulder, Pine Tree                | counting loops, star patterns                       |
| List Labs       | Fruit Stand, Apple Crate          | `sum()`, `.count()`                                 |
| Function Forge  | Anvil, Furnace, Old Mine (secret) | two parameters, dictionaries, nested loops          |

## How to run

Only the Python standard library is needed (Python 3.10+ with tkinter):

```bash
python3 main.py
```

## Controls

| Key                | Action                                                                 |
| ------------------ | ---------------------------------------------------------------------- |
| WASD or arrow keys | walk                                                                   |
| E, Space or Enter  | talk to a villager, inspect things, read a sign, or choose in a dialog |
| J                  | open the journal (every challenge, odd job, star and gold coin)        |
| Esc                | close a dialog, or go back to the title screen                         |
| Ctrl/⌘ + Enter     | run your code in a challenge                                           |

Above each villager's head:

- a red **!** means they have a challenge for you now
- a **★** means you've already helped them
- **…** means they'll need you later
- a gold **coin** over an object means it has an odd job ready

## How a challenge works

1. Read the mission, the **New Skill** card and its example, then the **Task**.
2. Write code in the editor and press **Run**.
3. Your code really runs. Pixel checks the output, your variables and your functions, and also
   re-tests with other **GIVEN** values, so typing in the expected answer doesn't pass.
4. Errors are explained in kid-friendly language, and the line with the problem is highlighted.
5. Earn ★★★ by solving a challenge without hints. Each hint costs one star, and the third hint
   shows the full answer.

Progress and unfinished code are saved in `~/.python_quest/save.json`. Set the
`PYTHON_QUEST_SAVE` environment variable to use a different file.

## Project layout

```
main.py               start the game
pyquest/levels.py     all villager challenges: story, lesson, task, tests, hints
pyquest/jobs.py       odd jobs: bonus tasks attached to things on the map
pyquest/worldmap.py   the valley layout: zones, paths, props, gates, signs and villagers
pyquest/pixelart.py   every sprite and tile, drawn pixel by pixel in code (no image files)
pyquest/valley.py     the walkable overworld, dialogs, HUD, journal and title screen
pyquest/screens.py    the coding challenge and victory screens
pyquest/runner.py     sandbox that runs learner code (safe built-ins, loop and output limits)
pyquest/checker.py    grades code against a challenge's tests and writes friendly feedback
pyquest/progress.py   stars, unlocking, ranks and saved drafts
pyquest/widgets.py    pixel buttons, wooden frames, code editor, Pixel the robot, confetti
tests/                unit tests for challenges, sandbox, progress and the valley layout
```

## Adding a challenge

1. Add a `Level(...)` to `LEVELS` in `pyquest/levels.py`. The comment at the top of that file
   explains the test format.
2. Add a villager for it to `_VILLAGERS` in `pyquest/worldmap.py`: name, tile position and greeting.
3. Run the tests. They check that every challenge's solution passes and that every villager can
   be reached.

To add an odd job instead, add a `Job(...)` to `JOBS` in `pyquest/jobs.py`. Give it a `Level`, the map
tile of the object it belongs to, and the villager challenge that unlocks it. Then run the tests:

```bash
python3 -m unittest discover -s tests -t .
```
