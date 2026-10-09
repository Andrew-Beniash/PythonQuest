"""Decides whether a learner's code solves a level, and explains why not."""

import io
import random
import re
import textwrap
import tokenize
from dataclasses import dataclass

from .runner import Sandbox

CHEERS = ["Awesome!", "Nailed it!", "Brilliant!", "You did it!", "Beep-tastic!", "Super coder!"]


@dataclass
class CheckResult:
    passed: bool
    headline: str
    detail: str
    output: str = ""
    error: str = ""
    error_line: int = None


def _norm(text):
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip("\n")


def _block(text):
    return textwrap.indent(text, "   ") if text else "   (nothing)"


def _same(actual, expected):
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected
    numbers = (int, float)
    if isinstance(actual, numbers) and isinstance(expected, numbers):
        return actual == expected
    return type(actual) is type(expected) and actual == expected


def _code_parts(code):
    """Return (python words used, code without comments or whitespace)."""
    names, pieces = set(), []
    skip = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type == tokenize.NAME:
                names.add(tok.string)
            if tok.type not in skip:
                pieces.append(tok.string)
        return names, re.sub(r"\s+", "", "".join(pieces))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        plain = re.sub(r"#[^\n]*", "", code)
        return set(re.findall(r"[A-Za-z_]\w*", plain)), re.sub(r"\s+", "", plain)


def _rule_hit(kind, value, names, flat):
    if kind == "name":
        return any(word in names for word in value.split("|"))
    if kind == "text":
        return re.sub(r"\s+", "", value) in flat
    if kind == "regex":
        return re.search(value, flat) is not None
    raise ValueError(f"unknown rule kind {kind!r}")


def check_rules(level, code):
    names, flat = _code_parts(code)
    for kind, value, message in level.must_use:
        if not _rule_hit(kind, value, names, flat):
            return message
    for kind, value, message in level.must_not_use:
        if _rule_hit(kind, value, names, flat):
            return message
    return None


def _describe(given):
    return ", ".join(f"{name} = {value!r}" for name, value in given.items())


def _output_problem(expected, got):
    exp, out = _norm(expected), _norm(got)
    if exp == out:
        return None
    if exp.lower() == out.lower():
        tip = "So close! Check your capital letters."
    elif re.sub(r"[^\w\s]", "", exp) == re.sub(r"[^\w\s]", "", out):
        tip = "So close! Check your punctuation - things like ! , ' and ."
    elif exp.replace(" ", "") == out.replace(" ", ""):
        tip = "So close! Check the spaces."
    elif out and exp.startswith(out):
        tip = "Good start - but something is missing at the end."
    else:
        tip = "The printed result doesn't match yet."
    return f"{tip}\n\nPixel expected:\n{_block(exp)}\n\nYour code printed:\n{_block(out)}"


def _value_problem(label, actual, expected):
    if _same(actual, expected):
        return None
    message = f"{label} should be {expected!r}, but it's {actual!r}."
    if str(actual) == str(expected):
        message += (f"\nThey look alike, but one is {type(expected).__name__} and the other is "
                    f"{type(actual).__name__} - check your quotes!")
    return message


def _test_problem(test, run, box):
    """Return (message, line) for the first thing wrong with one test run."""
    if "output" in test:
        problem = _output_problem(test["output"], run.output)
        if problem:
            return problem, None
    for name, expected in test.get("vars", {}).items():
        if name not in box.namespace:
            return f"I can't find a variable called '{name}'. Check the spelling!", None
        problem = _value_problem(f"'{name}'", box.namespace[name], expected)
        if problem:
            return problem, None
    for fname, args, expected in test.get("calls", ()):
        if not callable(box.namespace.get(fname)):
            return f"I can't find a function called {fname}. Did you write  def {fname}(...):  ?", None
        call_text = f"{fname}({', '.join(repr(a) for a in args)})"
        value, failure = box.call(fname, args)
        if failure:
            return f"{call_text} crashed.\n{failure.friendly}", failure.line
        if value is None and expected is not None:
            return f"{call_text} gave back None. Did you forget to return the answer? (print only shows it)", None
        problem = _value_problem(call_text, value, expected)
        if problem:
            return problem, None
    return None, None


def check(level, code):
    if not code.strip() or code.strip() == level.starter.strip():
        return CheckResult(False, "Your turn!", "Type some Python in the editor, then press Run.")

    first = None
    for index, test in enumerate(level.tests):
        overrides = test.get("given", {})
        box = Sandbox({**level.given, **overrides})
        run = box.run(code)
        if first is None:
            first = run
        when = f"\n\n(This happened when {_describe(overrides)}.)" if index and overrides else ""

        if run.error:
            return CheckResult(False, "Oops - an error!", run.friendly + when,
                               output=first.output, error=run.error, error_line=run.line)

        if index == 0:
            rule = check_rules(level, code)
            if rule:
                return CheckResult(False, "Almost!", rule, output=first.output)

        problem, line = _test_problem(test, run, box)
        if problem:
            headline = "Not quite yet!" if not when else "Pixel tried another value..."
            return CheckResult(False, headline, problem + when, output=first.output, error_line=line)

    return CheckResult(True, random.choice(CHEERS), level.praise, output=first.output)
