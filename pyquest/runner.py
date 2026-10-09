"""Runs a learner's code in a small sandbox and explains errors kindly.

The sandbox only exposes a handful of safe built-ins, stops runaway loops
with a step limit, and caps how much can be printed.
"""

import builtins
import copy
import io
import sys
from dataclasses import dataclass, field

FILENAME = "<your code>"
MAX_STEPS = 200_000
MAX_OUTPUT = 10_000
MAX_RANGE = 1_000_000

_SAFE_NAMES = [
    "abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter", "float",
    "int", "isinstance", "len", "list", "map", "max", "min", "pow", "repr",
    "reversed", "round", "set", "sorted", "str", "sum", "tuple", "type", "zip",
    "Exception", "ValueError", "TypeError", "IndexError", "KeyError",
    "ZeroDivisionError", "NameError", "__build_class__",
]


class QuestError(Exception):
    """An error whose message is already written for the learner."""


class _StepLimit(BaseException):
    """Raised by the tracer; BaseException so `except Exception` can't swallow it."""


@dataclass
class RunResult:
    output: str = ""
    error: str = ""        # e.g. "NameError: name 'x' is not defined"
    friendly: str = ""     # a kid-friendly explanation
    line: int = None       # line in the learner's code, if known
    namespace: dict = field(default_factory=dict)

    @property
    def ok(self):
        return not self.error


def _safe_range(*args):
    numbers = range(*args)
    if len(numbers) > MAX_RANGE:
        raise QuestError(f"That range is enormous! Keep it under {MAX_RANGE:,} numbers.")
    return numbers


def _no_input(*_args):
    raise QuestError("input() is switched off in Python Quest. Use the GIVEN variables instead!")


def _user_line(exc):
    line = None
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == FILENAME:
            line = tb.tb_lineno
        tb = tb.tb_next
    return line


def explain(exc):
    """Turn an exception into a short, encouraging explanation."""
    if isinstance(exc, QuestError):
        return str(exc)
    if isinstance(exc, _StepLimit):
        return "Your code ran for too long! Is there a loop that never stops?"
    if isinstance(exc, IndentationError):
        if "expected an indented block" in exc.msg:
            return "Python expected some indented code here. Lines inside if, for, while and def need 4 spaces in front."
        return "The spaces at the start of this line look wrong. Code inside a block lines up with 4 spaces."
    if isinstance(exc, SyntaxError):
        msg = exc.msg or ""
        if "unterminated string" in msg or "EOL" in msg:
            return "A string is missing its closing quote. Every \" needs a partner!"
        if "was never closed" in msg:
            return "A bracket was opened but never closed. Count your ( and )!"
        if "expected ':'" in msg:
            return "Python expected a colon ':' at the end of this line."
        if "unmatched" in msg:
            return "There's an extra closing bracket on this line."
        if "invalid syntax. Perhaps you forgot a comma" in msg:
            return "Python got confused here. Missing quotes around text, or a missing comma?"
        if "'=' " in msg or "Maybe you meant '=='" in msg:
            return "To compare two things use ==. A single = puts a value into a variable."
        return "Python couldn't understand this line. Check quotes, brackets and colons."
    if isinstance(exc, NameError):
        name = getattr(exc, "name", None) or "that"
        return (f"Python doesn't know anything called '{name}'. Check the spelling - "
                f"or if you meant text, put it in quotes.")
    if isinstance(exc, ImportError):
        return "Imports are switched off in Python Quest - everything you need is already built in!"
    if isinstance(exc, ZeroDivisionError):
        return "You tried to divide by zero. Even robots can't do that!"
    if isinstance(exc, IndexError):
        return "You asked for a list position that doesn't exist. Remember: positions start at 0!"
    if isinstance(exc, KeyError):
        return f"That key ({exc}) isn't in the dictionary."
    if isinstance(exc, TypeError):
        text = str(exc)
        if "can only concatenate str" in text or "unsupported operand" in text:
            return "You mixed text and numbers. Use str() to turn a number into text, or int() for the other way."
        if "not callable" in text:
            return "You tried to call something that isn't a function. Maybe a stray ( ) ?"
        if "argument" in text:
            return "A function got the wrong number of inputs. Check what goes inside the ( )."
        return "Two kinds of values got mixed up here (like text and numbers)."
    if isinstance(exc, ValueError):
        return "A value had the wrong shape - for example int() can only read text that looks like a number."
    if isinstance(exc, AttributeError):
        return "That value doesn't have that ability. Check the spelling after the dot."
    if isinstance(exc, RecursionError):
        return "A function kept calling itself forever!"
    return "Something went wrong while running your code."


class Sandbox:
    """One fresh Python world: run code in it, then call its functions."""

    def __init__(self, given=None):
        self._out = io.StringIO()
        self._steps = 0
        safe = {name: getattr(builtins, name) for name in _SAFE_NAMES}
        safe.update(print=self._print, range=_safe_range, input=_no_input)
        self.namespace = {"__builtins__": safe, "__name__": "__main__"}
        self.namespace.update(copy.deepcopy(given or {}))

    @property
    def output(self):
        return self._out.getvalue()

    def _print(self, *args, sep=" ", end="\n", **_ignored):
        sep = " " if sep is None else str(sep)
        end = "\n" if end is None else str(end)
        text = sep.join(str(a) for a in args) + end
        if self._out.tell() + len(text) > MAX_OUTPUT:
            raise QuestError("Whoa, that's a LOT of printing! Is a loop running too many times?")
        self._out.write(text)

    def _tracer(self, frame, event, _arg):
        if frame.f_code.co_filename != FILENAME:
            return None
        if event == "line":
            self._steps += 1
            if self._steps > MAX_STEPS:
                raise _StepLimit()
        return self._tracer

    def _guarded(self, fn, *args):
        previous = sys.gettrace()
        sys.settrace(self._tracer)
        try:
            return fn(*args)
        finally:
            sys.settrace(previous)

    def _failure(self, exc, line):
        name = "TimeoutError" if isinstance(exc, _StepLimit) else type(exc).__name__
        detail = exc.msg if isinstance(exc, SyntaxError) else str(exc)
        return RunResult(
            output=self.output,
            error=f"{name}: {detail}" if detail else name,
            friendly=explain(exc),
            line=line,
            namespace=self.namespace,
        )

    def run(self, code):
        try:
            compiled = compile(code, FILENAME, "exec")
        except SyntaxError as exc:
            return self._failure(exc, exc.lineno)
        try:
            self._guarded(exec, compiled, self.namespace)
        except (KeyboardInterrupt, MemoryError):
            raise
        except BaseException as exc:  # learner code can raise anything, even SystemExit
            return self._failure(exc, _user_line(exc))
        return RunResult(output=self.output, namespace=self.namespace)

    def call(self, name, args):
        """Call a function the learner defined. Returns (value, error_result_or_None)."""
        try:
            return self._guarded(self.namespace[name], *copy.deepcopy(args)), None
        except (KeyboardInterrupt, MemoryError):
            raise
        except BaseException as exc:
            return None, self._failure(exc, _user_line(exc))


def run_code(code, given=None):
    return Sandbox(given).run(code)
