"""Odd jobs: bonus coding tasks found by interacting with things around Python Valley.

Each job is a normal `Level` (same tests, rules and checker as the villager challenges)
attached to a prop on the map. A job unlocks once a certain villager has been helped,
and pays gold instead of counting towards the main stars.
"""

from dataclasses import dataclass

from .levels import FUNCS, GIVEN_STARTER, LISTS, LOGIC, LOOPS, PRINT, VARS, Level

GOLD_PER_STAR = 10
F_STRING = ("regex", r"(?<![A-Za-z0-9_])[fF][rR]?[\"']", "Use an f-string: put f right before the quotes.")


@dataclass(frozen=True)
class Job:
    level: Level
    name: str        # what the thing is called, e.g. "Mailbox"
    prop: str        # sprite used for its portrait
    x: int           # the map tile you interact with
    y: int
    requires: str    # level id that must be complete first
    intro: str       # what you read when you inspect it
    idle: str        # what you read before the job is ready

    @property
    def id(self):
        return self.level.id


JOBS = [
    # ---------------------------------------------------------------- Print Plains
    Job(
        Level(
            id="job_mailbox", world=PRINT, title="Letters for You", skill="\\n new lines",
            story="The mailbox is stuffed with letters! The post office wants a welcome note printed, "
                  "but the printer only has ink for ONE print().",
            concept='Inside a string, \\n means "start a new line". One print() can show many lines!',
            example='print("Roses are red\\nViolets are blue")',
            task="Use just ONE print() to show two lines:  Dear Farmer,  and then  Welcome to the valley!",
            solution='print("Dear Farmer,\\nWelcome to the valley!")',
            hints=("Put \\n where the new line should start.",
                   'Everything goes inside one pair of quotes:  "Dear Farmer,\\nWelcome..."',
                   'print("Dear Farmer,\\nWelcome to the valley!")'),
            tests=({"output": "Dear Farmer,\nWelcome to the valley!"},),
            must_use=(("text", "\\n", "Use \\n inside the string to start a new line."),),
            must_not_use=(("regex", r"print.*print", "Only ONE print() allowed - the ink is running out!"),),
            praise="The post office sends a thank-you note. Mail delivered!",
        ),
        "Mailbox", "mailbox", 7, 7, "hello",
        "The mailbox is so full the flag won't stay down. There's a request from the post office inside.",
        "The mailbox is empty for now.",
    ),
    Job(
        Level(
            id="job_scarecrow", world=PRINT, title="Crow Count", skill="// and %",
            story="Crows keep landing in the field! The scarecrow can only scare them away in groups of 3.",
            concept="// divides and throws away the remainder (7 // 2 is 3). "
                    "% gives just the remainder (7 % 2 is 1).",
            example="print(7 // 2)\nprint(7 % 2)",
            task="Print how many full groups of 3 fit in crows. Then, on the next line, print how many "
                 "crows are left over.",
            starter=GIVEN_STARTER, given={"crows": 17},
            solution="print(crows // 3)\nprint(crows % 3)",
            hints=("crows // 3 counts the full groups.", "crows % 3 counts the ones left over.",
                   "print(crows // 3)\nprint(crows % 3)"),
            tests=({"output": "5\n2"}, {"given": {"crows": 9}, "output": "3\n0"},
                   {"given": {"crows": 2}, "output": "0\n2"}),
            praise="CAW! The crows flap away in neat little groups of three.",
        ),
        "Scarecrow", "scarecrow", 12, 4, "calculator",
        "The scarecrow's button eyes look worried. There are crows everywhere!",
        "The scarecrow stands guard over the crops.",
    ),
    # ------------------------------------------------------------- Variable Valley
    Job(
        Level(
            id="job_well", world=VARS, title="Wishing Well", skill=".upper() & .lower()",
            story="Shout into the wishing well and it echoes back... in CAPITALS! Then it whispers in lowercase.",
            concept="Strings have built-in abilities called methods. word.upper() makes it SHOUTY, "
                    "word.lower() makes it quiet.",
            example='pet = "Rex"\nprint(pet.upper())',
            task="Print wish in all capitals, then print it again in all lowercase.",
            starter=GIVEN_STARTER, given={"wish": "More Cake"},
            solution="print(wish.upper())\nprint(wish.lower())",
            hints=("wish.upper() gives the shouty version.", "wish.lower() gives the whisper.",
                   "print(wish.upper())\nprint(wish.lower())"),
            tests=({"output": "MORE CAKE\nmore cake"}, {"given": {"wish": "A Pony"}, "output": "A PONY\na pony"}),
            must_use=(("name", "upper", "Use .upper() for the shout."),
                      ("name", "lower", "Use .lower() for the whisper.")),
            praise="The well gurgles happily. Your wish is on its way!",
        ),
        "Wishing Well", "well", 23, 11, "name_tag",
        "Coins glitter at the bottom of the old well. Someone has tied a wish to the bucket.",
        "The water at the bottom of the well is very still.",
    ),
    Job(
        Level(
            id="job_lamp", world=VARS, title="Light the Lamps", skill="f-strings+",
            story="Night is coming to the village square. Each lamp needs a little sign saying where it is.",
            concept="An f-string can hold as many variables as you like - each one inside its own { }.",
            example='x = 3\ny = 7\nprint(f"Point {x}, {y}")',
            task="Print  Lamp <number> on <street> Street is lit!   With the GIVEN values that is:  "
                 "Lamp 4 on Maple Street is lit!",
            starter=GIVEN_STARTER, given={"number": 4, "street": "Maple"},
            solution='print(f"Lamp {number} on {street} Street is lit!")',
            hints=('Start with  print(f"Lamp {number} ...', "Put {street} where the street name goes.",
                   'print(f"Lamp {number} on {street} Street is lit!")'),
            tests=({"output": "Lamp 4 on Maple Street is lit!"},
                   {"given": {"number": 12, "street": "Oak"}, "output": "Lamp 12 on Oak Street is lit!"}),
            must_use=(F_STRING,),
            praise="Click! A warm glow spreads across the square.",
        ),
        "Street Lamp", "lamp", 18, 7, "badge",
        "This lamp is dark, and its little name sign is blank.",
        "An old iron street lamp.",
    ),
    # ---------------------------------------------------------------- Logic Lagoon
    Job(
        Level(
            id="job_tackle", world=LOGIC, title="Catch of the Day", skill="or",
            story="The old fisher's tackle box has a note: 'Fish only bite when it's rainy OR foggy.'",
            concept="or is True when at least one side is True. It's only False when BOTH sides are False.",
            example='if tired or hungry:\n    print("Nap time!")',
            task='If weather is "rainy" or "foggy", print  Fish are biting!   otherwise print  Too sunny for fish.',
            starter=GIVEN_STARTER, given={"weather": "rainy"},
            solution='if weather == "rainy" or weather == "foggy":\n    print("Fish are biting!")\n'
                     'else:\n    print("Too sunny for fish.")',
            hints=("Use or between two checks.",
                   'Each side needs its own check:  weather == "rainy" or weather == "foggy"',
                   'if weather == "rainy" or weather == "foggy":\n    print("Fish are biting!")\n'
                   'else:\n    print("Too sunny for fish.")'),
            tests=({"output": "Fish are biting!"}, {"given": {"weather": "foggy"}, "output": "Fish are biting!"},
                   {"given": {"weather": "sunny"}, "output": "Too sunny for fish."},
                   {"given": {"weather": "windy"}, "output": "Too sunny for fish."}),
            must_use=(("name", "or", "Use or to check both kinds of weather."),),
            praise="Splash! A shiny trout jumps straight into the bucket.",
        ),
        "Tackle Box", "crate", 36, 7, "ticket",
        "A tackle box full of hooks and floats, with a note stuck to the lid.",
        "A tackle box. Its owner must be out on the lake.",
    ),
    Job(
        Level(
            id="job_berries", world=LOGIC, title="Berry Picking", skill="not",
            story="This bush is covered in juicy berries. Keep picking until the basket is full!",
            concept="not flips True to False and False to True.  if not full:  means 'if it is NOT full'.",
            example='if not raining:\n    print("Go outside!")',
            task="If basket_full is NOT True, print  Pick more berries!   otherwise print  Basket is full!",
            starter=GIVEN_STARTER, given={"basket_full": False},
            solution='if not basket_full:\n    print("Pick more berries!")\nelse:\n    print("Basket is full!")',
            hints=("Start with  if not basket_full:", "Use else: for the full basket.",
                   'if not basket_full:\n    print("Pick more berries!")\nelse:\n    print("Basket is full!")'),
            tests=({"output": "Pick more berries!"}, {"given": {"basket_full": True}, "output": "Basket is full!"}),
            must_use=(("name", "not", "Use not to flip basket_full."),),
            praise="Mmm, berries! Pixel's screen turns a little bit purple.",
        ),
        "Berry Bush", "bush", 37, 11, "hot_or_not",
        "The bush is heavy with berries, and there's an empty basket beside it.",
        "A bush with tiny green berries. They're not ripe yet.",
    ),
    # --------------------------------------------------------------- Loop Mountain
    Job(
        Level(
            id="job_boulder", world=LOOPS, title="Rock Smash", skill="counting loops",
            story="A huge boulder is blocking the mountain trail. Every hit cracks it a little more!",
            concept="range(1, n + 1) counts 1, 2, 3... up to n. Use the loop variable inside an f-string "
                    "to number things.",
            example='for i in range(1, 4):\n    print(f"Step {i}")',
            task="Print  Hit 1!  Hit 2!  ... up to  Hit <hits>!  (one per line), then  The boulder crumbles!",
            starter=GIVEN_STARTER, given={"hits": 3},
            solution='for i in range(1, hits + 1):\n    print(f"Hit {i}!")\nprint("The boulder crumbles!")',
            hints=("range(1, hits + 1) counts from 1 up to hits.", 'Inside the loop:  print(f"Hit {i}!")',
                   'for i in range(1, hits + 1):\n    print(f"Hit {i}!")\nprint("The boulder crumbles!")'),
            tests=({"output": "Hit 1!\nHit 2!\nHit 3!\nThe boulder crumbles!"},
                   {"given": {"hits": 1}, "output": "Hit 1!\nThe boulder crumbles!"},
                   {"given": {"hits": 5}, "output": "Hit 1!\nHit 2!\nHit 3!\nHit 4!\nHit 5!\nThe boulder crumbles!"}),
            must_use=(("name", "for|while", "Use a loop to count the hits."),),
            praise="CRACK! The boulder breaks into a pile of pebbles.",
        ),
        "Boulder", "boulder", 33, 19, "hop",
        "A big cracked boulder. It looks like it would break if you hit it enough times...",
        "A big, heavy boulder.",
    ),
    Job(
        Level(
            id="job_pinecones", world=LOOPS, title="Pine Cone Pyramid", skill="patterns",
            story="The mountain squirrels want their pine cones stacked in a neat triangle.",
            concept='A loop can build a pattern: "*" * i makes a row that gets longer each time round.',
            example='for i in range(1, 3):\n    print("o" * i)',
            task="Print a triangle of * that is height rows tall: 1 star on the first row, 2 on the second... "
                 "up to height.",
            starter=GIVEN_STARTER, given={"height": 3},
            solution='for i in range(1, height + 1):\n    print("*" * i)',
            hints=("Loop with  for i in range(1, height + 1):", 'Each row is  "*" * i',
                   'for i in range(1, height + 1):\n    print("*" * i)'),
            tests=({"output": "*\n**\n***"}, {"given": {"height": 5}, "output": "*\n**\n***\n****\n*****"},
                   {"given": {"height": 1}, "output": "*"}),
            must_use=(("name", "for|while", "Use a loop to build the rows."),),
            praise="The squirrels applaud with their tiny paws.",
        ),
        "Pine Tree", "pine", 35, 22, "treasure_sum",
        "Pine cones are scattered everywhere, and a squirrel is glaring at you.",
        "A tall, sticky pine tree.",
    ),
    # ------------------------------------------------------------------- List Labs
    Job(
        Level(
            id="job_fruit_stand", world=LISTS, title="Fruit Stand", skill="sum()",
            story="The fruit seller has lost her calculator. What do all the prices add up to?",
            concept="sum(my_list) adds up every number in a list.  len(my_list) counts the items.",
            example="scores = [3, 4, 5]\nprint(sum(scores))",
            task="Print the total of prices. Then, on the next line, print how many prices there are.",
            starter=GIVEN_STARTER, given={"prices": [3, 5, 2]},
            solution="print(sum(prices))\nprint(len(prices))",
            hints=("sum(prices) adds them up.", "len(prices) counts them.", "print(sum(prices))\nprint(len(prices))"),
            tests=({"output": "10\n3"}, {"given": {"prices": [7]}, "output": "7\n1"},
                   {"given": {"prices": [1, 1, 1, 1]}, "output": "4\n4"}),
            must_use=(("name", "sum", "Try sum() this time - it's built in!"),),
            praise="Sold! The fruit seller gives Pixel a free apple.",
        ),
        "Fruit Stand", "stall", 19, 19, "snacks",
        "The fruit stand is piled high, but the price tags are a muddle.",
        "A fruit stand. The seller is still setting up.",
    ),
    Job(
        Level(
            id="job_apple_crate", world=LISTS, title="Apple Crate", skill="counting things",
            story="This crate is a jumble of fruit. How many apples are hiding inside?",
            concept="my_list.count(x) tells you how many times x appears. "
                    "You could also loop through the list and add 1 each time you spot one!",
            example="dice = [6, 2, 6]\nprint(dice.count(6))",
            task='Print how many times "apple" appears in crate.',
            starter=GIVEN_STARTER, given={"crate": ["apple", "pear", "apple", "plum", "apple"]},
            solution='print(crate.count("apple"))',
            hints=('crate.count("apple") does the counting.', "Wrap it in print( ).", 'print(crate.count("apple"))'),
            tests=({"output": "3"}, {"given": {"crate": ["pear"]}, "output": "0"},
                   {"given": {"crate": ["apple", "apple"]}, "output": "2"}),
            praise="Three apples! Pixel tries to juggle them (badly).",
        ),
        "Apple Crate", "crate", 29, 18, "roll_call",
        "A wooden crate full of mixed-up fruit, labelled APPLES?",
        "A sealed wooden crate.",
    ),
    # -------------------------------------------------------------- Function Forge
    Job(
        Level(
            id="job_anvil", world=FUNCS, title="Sword Smith", skill="two parameters",
            story="The blacksmith's anvil hums with magic. Forge a naming spell for shiny new swords!",
            concept="A function can take more than one parameter - separate them with commas:  def f(a, b):",
            example="def add(a, b):\n    return a + b",
            task='Write forge(metal, power) that returns  "<metal> sword +<power>".  So forge("Iron", 2) '
                 'gives "Iron sword +2"',
            starter="def forge(metal, power):\n    ",
            solution='def forge(metal, power):\n    return f"{metal} sword +{power}"',
            hints=("Use return with an f-string.", 'f"{metal} sword +{power}"',
                   'def forge(metal, power):\n    return f"{metal} sword +{power}"'),
            tests=({"calls": [("forge", ("Iron", 2), "Iron sword +2"), ("forge", ("Gold", 5), "Gold sword +5")]},),
            praise="CLANG! A gleaming sword rests on the anvil.",
        ),
        "Anvil", "anvil", 9, 26, "double",
        "A sturdy anvil, still warm. A hammer lies next to an empty sword mould.",
        "A cold iron anvil.",
    ),
    Job(
        Level(
            id="job_furnace", world=FUNCS, title="Smelting Recipes", skill="dictionaries",
            story="The furnace has a recipe book: each ore takes a different number of minutes to smelt.",
            concept='A dictionary stores pairs:  {"key": value}.  Look a value up with  book["key"].',
            example='ages = {"Rex": 3, "Tom": 5}\nprint(ages["Tom"])',
            task='Write smelt_time(ore) that returns recipes[ore] (recipes is GIVEN). '
                 'So smelt_time("iron") gives 10.',
            starter=GIVEN_STARTER + "def smelt_time(ore):\n    ",
            given={"recipes": {"copper": 5, "iron": 10, "gold": 20}},
            solution="def smelt_time(ore):\n    return recipes[ore]",
            hints=("Look the ore up in the dictionary.", "recipes[ore] gives the minutes.",
                   "def smelt_time(ore):\n    return recipes[ore]"),
            tests=({"calls": [("smelt_time", ("copper",), 5), ("smelt_time", ("iron",), 10),
                              ("smelt_time", ("gold",), 20)]},),
            praise="Whoosh! Three shiny metal bars slide out of the furnace.",
        ),
        "Furnace", "furnace", 11, 26, "even",
        "The furnace roars. A recipe book sits on top, open to a page of numbers.",
        "The furnace is cold. Nobody has lit it in a while.",
    ),
    Job(
        Level(
            id="job_mine", world=FUNCS, title="Secret Gem Mine", skill="nested loops",
            story="Deep inside the old mine, the walls sparkle. Count every gem (*) on the cave map!",
            concept="A loop inside a loop can visit every character of every row. "
                    "(A string's .count() works too!)",
            example='for row in ["ab", "cd"]:\n    for ch in row:\n        print(ch)',
            task='Write count_gems(rows) that returns how many "*" there are in rows, a list of strings.',
            starter="def count_gems(rows):\n    ",
            solution=('def count_gems(rows):\n    total = 0\n    for row in rows:\n        for ch in row:\n'
                      '            if ch == "*":\n                total = total + 1\n    return total'),
            hints=("Start with total = 0, and loop over each row.",
                   'Loop over each ch in the row and add 1 when ch == "*".',
                   'def count_gems(rows):\n    total = 0\n    for row in rows:\n        for ch in row:\n'
                   '            if ch == "*":\n                total = total + 1\n    return total'),
            tests=({"calls": [("count_gems", (["*.*", "..*"],), 3), ("count_gems", ([],), 0),
                              ("count_gems", (["***"],), 3), ("count_gems", ([".", "*.*.*", "**"],), 5)]},),
            praise="The whole mine glitters. You found Python Valley's secret treasure!",
        ),
        "Old Mine", "mine", 4, 28, "fizzbuzz",
        "Cold air drifts out of the mine. Something deep inside is sparkling...",
        "The mine entrance is dark. A sign says: HEROES ONLY.",
    ),
]

JOBS_BY_ID = {job.id: job for job in JOBS}
MAX_GOLD = 3 * GOLD_PER_STAR * len(JOBS)


def jobs_in(world):
    return [job for job in JOBS if job.level.world is world]
