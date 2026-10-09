"""All worlds and levels of Python Quest.

Each level teaches one idea, then checks the learner's code by *running it*
against one or more tests:

    {"given":  {...},              # override starting variables for this test
     "output": "...",              # what the code must print
     "vars":   {"name": value},    # variables that must exist afterwards
     "calls":  [(func, args, expected_return), ...]}

Rules are (kind, value, message) tuples where kind is:
    "name"  - a Python word must (not) appear, e.g. "for" or "for|while"
    "text"  - a piece of code must (not) appear (spaces and comments ignored)
    "regex" - a regular expression over that same code
"""

from dataclasses import dataclass, field

from . import theme


@dataclass(frozen=True)
class World:
    key: str
    name: str
    tagline: str
    color: str
    badge: str


@dataclass(frozen=True)
class Level:
    id: str
    world: World
    title: str
    skill: str
    story: str
    concept: str
    example: str
    task: str
    solution: str
    hints: tuple
    tests: tuple
    starter: str = "# Write your code below\n"
    given: dict = field(default_factory=dict)
    must_use: tuple = ()
    must_not_use: tuple = ()
    praise: str = "Pixel does a happy little spin!"


PRINT = World("print", "Print Plains", "Make Pixel talk", theme.SKY, "print")
VARS = World("vars", "Variable Valley", "Store things in boxes", theme.ROSE, "x=1")
LOGIC = World("logic", "Logic Lagoon", "Teach Pixel to decide", theme.GOLD, "if")
LOOPS = World("loops", "Loop Mountain", "Repeat without the boring", theme.LEAF, "for")
LISTS = World("lists", "List Labs", "Keep many things together", theme.PUMPKIN, "[ ]")
FUNCS = World("funcs", "Function Forge", "Craft your own commands", theme.PLUM, "def")

WORLDS = [PRINT, VARS, LOGIC, LOOPS, LISTS, FUNCS]

GIVEN_STARTER = "# Some variables already exist - look at GIVEN\n"

LEVELS = [
    # ---------------------------------------------------------------- Print Plains
    Level(
        id="hello",
        world=PRINT,
        title="Wake Up, Pixel!",
        skill="print()",
        story="Pixel the robot just powered on, but its voice box is silent. Give it its very first words!",
        concept="print() shows a message on the screen. Text (called a string) goes inside quotes.",
        example='print("Beep boop!")',
        task="Make Pixel say exactly:  Hello, Python!",
        solution='print("Hello, Python!")',
        hints=(
            "Use print( ) and put your message inside the brackets.",
            'Text needs quotes around it, "like this".',
            'Try:  print("Hello, Python!")',
        ),
        tests=({"output": "Hello, Python!"},),
        praise="Pixel's speakers crackle to life: HELLO, PYTHON!",
    ),
    Level(
        id="countdown_chant",
        world=PRINT,
        title="Ready, Set, Go!",
        skill="many prints",
        story="Pixel is about to race a snail. Every proper race needs a countdown.",
        concept="Python runs your code from top to bottom. Each print() starts a new line.",
        example='print("One")\nprint("Two")',
        task="Print three lines:  Ready  then  Set  then  Go!",
        starter="# One print() per line\n",
        solution='print("Ready")\nprint("Set")\nprint("Go!")',
        hints=(
            "You need three print() commands, one under the other.",
            "Watch the spelling and the ! after Go.",
            'print("Ready")\nprint("Set")\nprint("Go!")',
        ),
        tests=({"output": "Ready\nSet\nGo!"},),
        praise="The snail never stood a chance.",
    ),
    Level(
        id="calculator",
        world=PRINT,
        title="Calculator Core",
        skill="math",
        story="Pixel's brain has a built-in calculator. Time to switch it on!",
        concept="Numbers don't need quotes. Python does math with + - * and /  (the * means times).",
        example="print(2 + 3)\nprint(10 * 4)",
        task="Make Python work out 7 times 6 and print the answer. Don't type the answer yourself!",
        solution="print(7 * 6)",
        hints=(
            "You can put math right inside print( ).",
            "Times is written with a star:  *",
            "print(7 * 6)",
        ),
        tests=({"output": "42"},),
        must_use=(("text", "*", "Use * to multiply the two numbers."),),
        must_not_use=(("text", "42", "Let Python do the math - don't type 42 yourself!"),),
        praise="42! The answer to everything, apparently.",
    ),
    Level(
        id="echo",
        world=PRINT,
        title="Echo Cave",
        skill="string tricks",
        story="Pixel found a cave that echoes. Shout into it and hear it come back three times!",
        concept="Strings can be glued together with + and repeated with * and a number.",
        example='print("Hi" + "!")\nprint("Na" * 4)',
        task='Print  HaHaHa  by repeating "Ha" 3 times with *.',
        solution='print("Ha" * 3)',
        hints=(
            'Start with the string "Ha".',
            'A string times a number repeats it:  "Ha" * 3',
            'print("Ha" * 3)',
        ),
        tests=({"output": "HaHaHa"},),
        must_use=(("text", "*", "Use * to repeat the text."),),
        must_not_use=(("text", "HaHaHa", 'Let Python do the repeating - type "Ha" only once.'),),
        praise="HaHaHa... haHaHa... hahaha...",
    ),
    # ------------------------------------------------------------- Variable Valley
    Level(
        id="name_tag",
        world=VARS,
        title="Name Tag",
        skill="variables",
        story="Pixel made a new friend and never wants to forget her name.",
        concept="A variable is a labelled box that stores a value. The = sign puts a value into the box.",
        example='pet = "Rex"\nlives = 9',
        task='Create a variable called friend that stores the text "Mia".',
        solution='friend = "Mia"',
        hints=(
            "Write the variable name, then =, then the value.",
            "Mia is text, so it needs quotes.",
            'friend = "Mia"',
        ),
        tests=({"vars": {"friend": "Mia"}},),
        praise="Name saved to Pixel's memory chip forever.",
    ),
    Level(
        id="coins",
        world=VARS,
        title="Coin Collector",
        skill="updating variables",
        story="Pixel already has some coins in its pocket and just found 3 more shiny ones.",
        concept="A variable can change. To add to it, use its old value:  score = score + 1",
        example="lives = 3\nlives = lives - 1\nprint(lives)",
        task="Add 3 to coins, then print coins.",
        starter=GIVEN_STARTER,
        given={"coins": 5},
        solution="coins = coins + 3\nprint(coins)",
        hints=(
            "Pixel tests other coin amounts too, so don't just type 8 - use the variable.",
            "coins = coins + 3  makes the box hold 3 more.",
            "coins = coins + 3\nprint(coins)",
        ),
        tests=(
            {"vars": {"coins": 8}, "output": "8"},
            {"given": {"coins": 10}, "vars": {"coins": 13}, "output": "13"},
            {"given": {"coins": 0}, "vars": {"coins": 3}, "output": "3"},
        ),
        praise="Cha-ching! Pixel's pocket jingles.",
    ),
    Level(
        id="badge",
        world=VARS,
        title="Name Badge",
        skill="f-strings",
        story="Pixel is printing name badges for the big robot party.",
        concept="An f-string puts variables inside text. Write f before the quotes and the variable inside { }.",
        example='food = "pizza"\nprint(f"I love {food}!")',
        task='Print  Hi, <name>!  using an f-string.  For name = "Bolt" that is  Hi, Bolt!',
        starter=GIVEN_STARTER,
        given={"name": "Bolt"},
        solution='print(f"Hi, {name}!")',
        hints=(
            'Start with  print(f"...")',
            "Inside the quotes, write {name} where the name should go.",
            'print(f"Hi, {name}!")',
        ),
        tests=(
            {"output": "Hi, Bolt!"},
            {"given": {"name": "Zip"}, "output": "Hi, Zip!"},
            {"given": {"name": "Ada"}, "output": "Hi, Ada!"},
        ),
        must_use=(("regex", r"(?<![A-Za-z0-9_])[fF][rR]?[\"']", "Use an f-string: put f right before the quotes."),),
        praise="Every robot at the party gets a shiny badge.",
    ),
    Level(
        id="birthday",
        world=VARS,
        title="Birthday Bot",
        skill="int()",
        story="Pixel's card machine gave it an age as text. Text can't do math... yet!",
        concept='Text that looks like a number ("9") is still text. int() turns it into a real number.',
        example='text = "4"\nnumber = int(text)\nprint(number * 2)',
        task="Turn age_text into a number, add 1, and print next year's age.",
        starter=GIVEN_STARTER,
        given={"age_text": "9"},
        solution="age = int(age_text)\nprint(age + 1)",
        hints=(
            "int(age_text) gives you a real number.",
            "Store it in a variable, then print it plus 1.",
            "age = int(age_text)\nprint(age + 1)",
        ),
        tests=(
            {"output": "10"},
            {"given": {"age_text": "12"}, "output": "13"},
            {"given": {"age_text": "99"}, "output": "100"},
        ),
        must_use=(("name", "int", "Use int() to turn the text into a number."),),
        praise="Happy birthday! Pixel lights all its candles (safely).",
    ),
    # ---------------------------------------------------------------- Logic Lagoon
    Level(
        id="sunny",
        world=LOGIC,
        title="Sunny Day",
        skill="if",
        story="Pixel only goes outside to play when the sun is out.",
        concept="if runs code only when a condition is True. == checks if two things are equal. "
                "Code inside the if is indented with 4 spaces.",
        example='if mood == "happy":\n    print("Yay!")',
        task='If weather is "sunny", print  Let\'s play!   Otherwise print nothing.',
        starter=GIVEN_STARTER,
        given={"weather": "sunny"},
        solution='if weather == "sunny":\n    print("Let\'s play!")',
        hints=(
            'Start with:  if weather == "sunny":',
            "Don't forget the colon : and 4 spaces before print.",
            'if weather == "sunny":\n    print("Let\'s play!")',
        ),
        tests=(
            {"output": "Let's play!"},
            {"given": {"weather": "rainy"}, "output": ""},
            {"given": {"weather": "snowy"}, "output": ""},
        ),
        must_use=(("name", "if", "Use an if statement to check the weather."),),
        praise="Pixel rolls outside and soaks up the sunshine.",
    ),
    Level(
        id="hot_or_not",
        world=LOGIC,
        title="Hot or Not",
        skill="else",
        story="Pixel's thermometer wants to give helpful advice.",
        concept="else catches everything the if didn't. > means greater than, < means less than.",
        example='if speed > 100:\n    print("Too fast!")\nelse:\n    print("OK")',
        task="If temp is greater than 25, print  Hot!   otherwise print  Cool!",
        starter=GIVEN_STARTER,
        given={"temp": 30},
        solution='if temp > 25:\n    print("Hot!")\nelse:\n    print("Cool!")',
        hints=(
            "Check  temp > 25  with an if.",
            "else: goes at the same indent as the if, with a colon.",
            'if temp > 25:\n    print("Hot!")\nelse:\n    print("Cool!")',
        ),
        tests=(
            {"output": "Hot!"},
            {"given": {"temp": 10}, "output": "Cool!"},
            {"given": {"temp": 25}, "output": "Cool!"},
            {"given": {"temp": 26}, "output": "Hot!"},
        ),
        must_use=(
            ("name", "if", "Use an if to check the temperature."),
            ("name", "else", "Use else for the 'otherwise' part."),
        ),
        praise="Pixel puts on its tiny sunglasses.",
    ),
    Level(
        id="medals",
        world=LOGIC,
        title="Medal Machine",
        skill="elif",
        story="Pixel is handing out medals at the Robot Games.",
        concept="elif means 'else if' - it checks another condition. >= means greater than or equal to.",
        example='if age >= 13:\n    print("Teen")\nelif age >= 10:\n    print("Tween")',
        task="score 90 or more: print  Gold.   70 or more:  Silver.   Anything else:  Bronze",
        starter=GIVEN_STARTER,
        given={"score": 95},
        solution='if score >= 90:\n    print("Gold")\nelif score >= 70:\n    print("Silver")\nelse:\n    print("Bronze")',
        hints=(
            "Check the biggest score first: if score >= 90:",
            "Then elif score >= 70: and finally else:",
            'if score >= 90:\n    print("Gold")\nelif score >= 70:\n    print("Silver")\nelse:\n    print("Bronze")',
        ),
        tests=(
            {"output": "Gold"},
            {"given": {"score": 90}, "output": "Gold"},
            {"given": {"score": 89}, "output": "Silver"},
            {"given": {"score": 70}, "output": "Silver"},
            {"given": {"score": 69}, "output": "Bronze"},
            {"given": {"score": 12}, "output": "Bronze"},
        ),
        must_use=(("name", "elif", "Use elif for the middle check."),),
        praise="Gold, silver, bronze - everyone's a winner today.",
    ),
    Level(
        id="ticket",
        world=LOGIC,
        title="Ticket Gate",
        skill="and",
        story="The Roller Coaster of Doom has two rules: bring a ticket, AND be tall enough!",
        concept="and is True only when BOTH sides are True.  or is True when at least one side is.",
        example='if hungry and has_cake:\n    print("Eat!")',
        task="If has_ticket is True and height is at least 120, print  Welcome aboard!   otherwise  Sorry!",
        starter=GIVEN_STARTER,
        given={"has_ticket": True, "height": 130},
        solution='if has_ticket and height >= 120:\n    print("Welcome aboard!")\nelse:\n    print("Sorry!")',
        hints=(
            "Join two checks with and:  if has_ticket and ...",
            "'At least 120' is  height >= 120",
            'if has_ticket and height >= 120:\n    print("Welcome aboard!")\nelse:\n    print("Sorry!")',
        ),
        tests=(
            {"output": "Welcome aboard!"},
            {"given": {"has_ticket": False}, "output": "Sorry!"},
            {"given": {"height": 110}, "output": "Sorry!"},
            {"given": {"height": 120}, "output": "Welcome aboard!"},
            {"given": {"has_ticket": False, "height": 90}, "output": "Sorry!"},
        ),
        must_use=(("name", "and", "Use and to combine both rules."),),
        praise="Wheeee! Pixel screams the whole ride.",
    ),
    # --------------------------------------------------------------- Loop Mountain
    Level(
        id="hop",
        world=LOOPS,
        title="Hop Hop Hop",
        skill="for loops",
        story="Pixel learned to hop! Now it wants to hop again... and again... and again...",
        concept="A for loop repeats code. range(5) counts 0, 1, 2, 3, 4 - that's 5 times round.",
        example='for i in range(2):\n    print("Clap!")',
        task="Print  Hop!  exactly  times  times (times is given).",
        starter=GIVEN_STARTER,
        given={"times": 3},
        solution='for i in range(times):\n    print("Hop!")',
        hints=(
            "range(times) repeats the right number of times.",
            "for i in range(times):  then an indented print.",
            'for i in range(times):\n    print("Hop!")',
        ),
        tests=(
            {"output": "Hop!\nHop!\nHop!"},
            {"given": {"times": 5}, "output": "Hop!\nHop!\nHop!\nHop!\nHop!"},
            {"given": {"times": 1}, "output": "Hop!"},
        ),
        must_use=(("name", "for", "Use a for loop to repeat the hop."),),
        praise="Boing boing boing! Pixel is a hopping machine.",
    ),
    Level(
        id="liftoff",
        world=LOOPS,
        title="Liftoff!",
        skill="range()",
        story="Pixel built a rocket out of cardboard boxes. 5... 4... 3...",
        concept="range(start, stop, step) can count down: range(3, 0, -1) gives 3, 2, 1. "
                "The loop variable holds the current number.",
        example="for n in range(3, 0, -1):\n    print(n)",
        task="Count down from start to 1 (one number per line), then print  Liftoff!",
        starter=GIVEN_STARTER,
        given={"start": 5},
        solution='for n in range(start, 0, -1):\n    print(n)\nprint("Liftoff!")',
        hints=(
            "range(start, 0, -1) counts down and stops before 0.",
            "Print Liftoff! AFTER the loop - so it's not indented.",
            'for n in range(start, 0, -1):\n    print(n)\nprint("Liftoff!")',
        ),
        tests=(
            {"output": "5\n4\n3\n2\n1\nLiftoff!"},
            {"given": {"start": 3}, "output": "3\n2\n1\nLiftoff!"},
            {"given": {"start": 1}, "output": "1\nLiftoff!"},
        ),
        must_use=(("name", "for|while", "Use a loop to count down."),),
        praise="The cardboard rocket reaches the kitchen ceiling!",
    ),
    Level(
        id="treasure_sum",
        world=LOOPS,
        title="Treasure Stairs",
        skill="adding up",
        story="Pixel found treasure stairs: 1 coin on step 1, 2 coins on step 2... all the way up to step n.",
        concept="To add things up in a loop, start a total at 0 and add to it each time round.",
        example="total = 0\nfor x in range(1, 4):\n    total = total + x\nprint(total)",
        task="Add up every number from 1 to n with a loop, then print the total.",
        starter=GIVEN_STARTER,
        given={"n": 10},
        solution="total = 0\nfor x in range(1, n + 1):\n    total = total + x\nprint(total)",
        hints=(
            "Start with  total = 0  before the loop.",
            "range(1, n + 1) stops just before n + 1, so it includes n.",
            "total = 0\nfor x in range(1, n + 1):\n    total = total + x\nprint(total)",
        ),
        tests=(
            {"output": "55"},
            {"given": {"n": 4}, "output": "10"},
            {"given": {"n": 100}, "output": "5050"},
        ),
        must_use=(("name", "for|while", "Use a loop to add the numbers up."),),
        must_not_use=(("name", "sum", "Build the total yourself with a loop instead of sum()."),),
        praise="Pixel's treasure chest is overflowing!",
    ),
    Level(
        id="power_up",
        world=LOOPS,
        title="Power Up",
        skill="while loops",
        story="Pixel's battery doubles every second. It wants to watch every step of the charge!",
        concept="A while loop keeps going as long as its condition is True. "
                "Something must change inside, or it loops forever!",
        example="x = 1\nwhile x < 10:\n    print(x)\n    x = x + 3",
        task="While energy is less than 100: print energy, then double it.",
        starter=GIVEN_STARTER,
        given={"energy": 1},
        solution="while energy < 100:\n    print(energy)\n    energy = energy * 2",
        hints=(
            "while energy < 100:  starts the loop.",
            "Inside: print it, then  energy = energy * 2",
            "while energy < 100:\n    print(energy)\n    energy = energy * 2",
        ),
        tests=(
            {"output": "1\n2\n4\n8\n16\n32\n64"},
            {"given": {"energy": 5}, "output": "5\n10\n20\n40\n80"},
            {"given": {"energy": 60}, "output": "60"},
            {"given": {"energy": 100}, "output": ""},
        ),
        must_use=(("name", "while", "Use a while loop this time."),),
        praise="Battery at 100%! Pixel's eyes are extra glowy.",
    ),
    # ------------------------------------------------------------------- List Labs
    Level(
        id="snacks",
        world=LISTS,
        title="Snack Pack",
        skill="lists",
        story="Pixel is packing snacks for a road trip and wants them all in one place.",
        concept="A list holds many values inside [ ], separated by commas. "
                "Positions start at 0, so  my_list[0]  is the FIRST item!",
        example='colors = ["red", "blue"]\nprint(colors[0])',
        task='Make a list called snacks with "apple", "banana", "cherry" (in that order). Then print the second snack.',
        solution='snacks = ["apple", "banana", "cherry"]\nprint(snacks[1])',
        hints=(
            'Lists look like  ["apple", "banana", "cherry"]',
            "The second item is at position 1:  snacks[1]",
            'snacks = ["apple", "banana", "cherry"]\nprint(snacks[1])',
        ),
        tests=({"vars": {"snacks": ["apple", "banana", "cherry"]}, "output": "banana"},),
        must_use=(("text", "[1]", "Get the second item using its position:  snacks[1]"),),
        praise="Crunch. Pixel can't actually eat, but it appreciates the thought.",
    ),
    Level(
        id="backpack",
        world=LISTS,
        title="Backpack",
        skill="append() & len()",
        story="Pixel is packing for an adventure. It must not forget the map!",
        concept="my_list.append(x) adds x to the end of a list.  len(my_list) tells you how many items it has.",
        example='toys = ["ball"]\ntoys.append("kite")\nprint(len(toys))',
        task='Add "map" to the end of bag, then print how many items bag has.',
        starter=GIVEN_STARTER,
        given={"bag": ["rope", "torch"]},
        solution='bag.append("map")\nprint(len(bag))',
        hints=(
            'bag.append("map") adds the map.',
            "len(bag) counts the items - print it!",
            'bag.append("map")\nprint(len(bag))',
        ),
        tests=(
            {"vars": {"bag": ["rope", "torch", "map"]}, "output": "3"},
            {"given": {"bag": []}, "vars": {"bag": ["map"]}, "output": "1"},
            {"given": {"bag": ["a", "b", "c", "d"]}, "vars": {"bag": ["a", "b", "c", "d", "map"]}, "output": "5"},
        ),
        must_use=(
            ("name", "append", "Use append() to add the map."),
            ("name", "len", "Use len() to count the items."),
        ),
        praise="Map packed. Adventure: unlocked.",
    ),
    Level(
        id="roll_call",
        world=LISTS,
        title="Roll Call",
        skill="looping lists",
        story="Pixel's crew has arrived for the mission. Time to greet everyone!",
        concept="A for loop can walk through a list, giving you one item each time round.",
        example='for fruit in ["fig", "kiwi"]:\n    print(fruit)',
        task="Print  Hi, <name>!  for every name in crew, in order.",
        starter=GIVEN_STARTER,
        given={"crew": ["Ada", "Linus", "Grace"]},
        solution='for person in crew:\n    print(f"Hi, {person}!")',
        hints=(
            "for person in crew:  gives you each name.",
            'An f-string makes the greeting:  f"Hi, {person}!"',
            'for person in crew:\n    print(f"Hi, {person}!")',
        ),
        tests=(
            {"output": "Hi, Ada!\nHi, Linus!\nHi, Grace!"},
            {"given": {"crew": ["Guido"]}, "output": "Hi, Guido!"},
            {"given": {"crew": ["Zoe", "Max"]}, "output": "Hi, Zoe!\nHi, Max!"},
        ),
        must_use=(("name", "for", "Use a for loop to go through the crew."),),
        praise="The whole crew waves back!",
    ),
    Level(
        id="biggest_gem",
        world=LISTS,
        title="Biggest Gem",
        skill="best so far",
        story="Pixel dug up a pile of gems. Which one is the biggest?",
        concept="Keep track of the best so far: start with the first item, "
                "then check every item and swap it in if it's bigger.",
        example="best = 0\nfor x in [4, 9, 2]:\n    if x > best:\n        best = x",
        task="Find the biggest number in gems using a loop (no max()!) and print it.",
        starter=GIVEN_STARTER,
        given={"gems": [3, 17, 8]},
        solution="biggest = gems[0]\nfor gem in gems:\n    if gem > biggest:\n        biggest = gem\nprint(biggest)",
        hints=(
            "Watch out - gems can be negative! Start with  biggest = gems[0]",
            "Loop through gems and use if to swap in a bigger one.",
            "biggest = gems[0]\nfor gem in gems:\n    if gem > biggest:\n        biggest = gem\nprint(biggest)",
        ),
        tests=(
            {"output": "17"},
            {"given": {"gems": [42, 5]}, "output": "42"},
            {"given": {"gems": [-4, -2, -9]}, "output": "-2"},
            {"given": {"gems": [7]}, "output": "7"},
        ),
        must_use=(("name", "for", "Use a for loop to check every gem."),),
        must_not_use=(
            ("name", "max", "No max() allowed - find it yourself with a loop!"),
            ("name", "sorted|sort", "No sorting allowed - find it yourself with a loop!"),
        ),
        praise="A gem the size of Pixel's head. Sparkly!",
    ),
    # -------------------------------------------------------------- Function Forge
    Level(
        id="greet",
        world=FUNCS,
        title="Greeting Spell",
        skill="def & return",
        story="Pixel wants a reusable greeting spell it can cast on anyone.",
        concept="def creates your own function. return sends a value back to whoever called it.",
        example="def add_one(x):\n    return x + 1\n\nprint(add_one(4))",
        task='Write greet(name) that returns  "Hello, " + name + "!"   So greet("Mia") gives "Hello, Mia!"',
        starter="def greet(name):\n    # return the greeting here\n    ",
        solution='def greet(name):\n    return "Hello, " + name + "!"',
        hints=(
            "Inside the function, use return - not print.",
            'Glue three strings:  "Hello, " + name + "!"',
            'def greet(name):\n    return "Hello, " + name + "!"',
        ),
        tests=({"calls": [("greet", ("Mia",), "Hello, Mia!"), ("greet", ("Pixel",), "Hello, Pixel!")]},),
        praise="The greeting spell glows purple. Everyone feels welcome.",
    ),
    Level(
        id="double",
        world=FUNCS,
        title="Double Trouble",
        skill="parameters",
        story="Pixel discovered a cloning machine. Whatever goes in comes out doubled!",
        concept="Parameters are the inputs inside the ( ). A function can do math with them and return the result.",
        example="def triple(n):\n    return n * 3",
        task="Write double(n) that returns n times 2.",
        starter="def double(n):\n    ",
        solution="def double(n):\n    return n * 2",
        hints=(
            "Use return with some math.",
            "n * 2 is twice n.",
            "def double(n):\n    return n * 2",
        ),
        tests=({"calls": [("double", (4,), 8), ("double", (0,), 0), ("double", (-3,), -6), ("double", (21,), 42)]},),
        praise="Two Pixels! Twice the beeps.",
    ),
    Level(
        id="even",
        world=FUNCS,
        title="Even Steven",
        skill="% and True/False",
        story="Pixel's dance moves only work on even-numbered beats.",
        concept="% gives the remainder after dividing. Even numbers leave 0 when divided by 2. "
                "True and False are values too!",
        example="print(7 % 2)   # 1\nprint(8 % 2)   # 0",
        task="Write is_even(n) that returns True if n is even, otherwise False.",
        starter="def is_even(n):\n    ",
        solution="def is_even(n):\n    return n % 2 == 0",
        hints=(
            "n % 2 is 0 when n is even.",
            "n % 2 == 0 is already True or False - you can return it directly!",
            "def is_even(n):\n    return n % 2 == 0",
        ),
        tests=({"calls": [("is_even", (4,), True), ("is_even", (7,), False), ("is_even", (0,), True),
                          ("is_even", (13,), False), ("is_even", (100,), True)]},),
        praise="Step, step, spin, step. Perfectly on beat.",
    ),
    Level(
        id="fizzbuzz",
        world=FUNCS,
        title="Boss: FizzBuzz",
        skill="everything!",
        story="The FINAL BOSS! The Fizz Robot only lets true heroes pass its number game.",
        concept="Combine it all: a function, if / elif / else and %. "
                "Check the most specific case (divisible by both 3 and 5) first!",
        example='def size(n):\n    if n > 10:\n        return "big"\n    return "small"',
        task='Write fizzbuzz(n): return "FizzBuzz" if n divides by 3 and 5, "Fizz" if by 3, '
             '"Buzz" if by 5, otherwise str(n).',
        starter="def fizzbuzz(n):\n    ",
        solution=(
            "def fizzbuzz(n):\n"
            "    if n % 15 == 0:\n        return \"FizzBuzz\"\n"
            "    elif n % 3 == 0:\n        return \"Fizz\"\n"
            "    elif n % 5 == 0:\n        return \"Buzz\"\n"
            "    else:\n        return str(n)"
        ),
        hints=(
            "'Divides by 3' means  n % 3 == 0",
            "Check 3 AND 5 first, then 3, then 5, then else: return str(n)",
            'def fizzbuzz(n):\n    if n % 3 == 0 and n % 5 == 0:\n        return "FizzBuzz"\n'
            '    elif n % 3 == 0:\n        return "Fizz"\n    elif n % 5 == 0:\n'
            '        return "Buzz"\n    else:\n        return str(n)',
        ),
        tests=({"calls": [("fizzbuzz", (1,), "1"), ("fizzbuzz", (3,), "Fizz"), ("fizzbuzz", (5,), "Buzz"),
                          ("fizzbuzz", (15,), "FizzBuzz"), ("fizzbuzz", (9,), "Fizz"), ("fizzbuzz", (10,), "Buzz"),
                          ("fizzbuzz", (30,), "FizzBuzz"), ("fizzbuzz", (7,), "7")]},),
        praise="You defeated the Fizz Robot! Pixel declares you a PYTHON HERO!",
    ),
]

MAX_STARS = 3 * len(LEVELS)


def level_code(index):
    """'2-3' style label: world number and level number inside that world."""
    level = LEVELS[index]
    world_no = WORLDS.index(level.world) + 1
    inside = [lv for lv in LEVELS[:index + 1] if lv.world is level.world]
    return f"{world_no}-{len(inside)}"
