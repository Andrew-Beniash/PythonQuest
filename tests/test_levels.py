import os
import tempfile
import unittest

from pyquest.checker import check
from pyquest.jobs import JOBS
from pyquest.levels import LEVELS, WORLDS, level_code
from pyquest.progress import Progress, stars_for
from pyquest.runner import run_code

ALL_TASKS = LEVELS + [job.level for job in JOBS]


def level(level_id):
    return next(lv for lv in LEVELS if lv.id == level_id)


class LevelDataTests(unittest.TestCase):
    def test_ids_are_unique(self):
        ids = [lv.id for lv in ALL_TASKS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_world_has_four_levels(self):
        for world in WORLDS:
            self.assertEqual(sum(lv.world is world for lv in LEVELS), 4, world.name)

    def test_each_level_has_three_hints_and_a_test(self):
        for lv in ALL_TASKS:
            self.assertEqual(len(lv.hints), 3, lv.id)
            self.assertTrue(lv.tests, lv.id)

    def test_level_codes(self):
        self.assertEqual(level_code(0), "1-1")
        self.assertEqual(level_code(5), "2-2")
        self.assertEqual(level_code(len(LEVELS) - 1), "6-4")


class SolutionTests(unittest.TestCase):
    def test_every_solution_passes(self):
        for lv in ALL_TASKS:
            with self.subTest(level=lv.id):
                result = check(lv, lv.solution)
                self.assertTrue(result.passed, f"{lv.id}: {result.headline} {result.detail}")

    def test_final_hint_is_a_working_answer(self):
        for lv in ALL_TASKS:
            with self.subTest(level=lv.id):
                self.assertTrue(check(lv, lv.hints[-1]).passed, lv.id)

    def test_untouched_starter_fails(self):
        for lv in ALL_TASKS:
            with self.subTest(level=lv.id):
                self.assertFalse(check(lv, lv.starter).passed)


class CheatingAndMistakeTests(unittest.TestCase):
    def test_typing_the_answer_is_caught(self):
        self.assertFalse(check(level("calculator"), "print(42)").passed)
        self.assertFalse(check(level("echo"), 'print("HaHaHa")').passed)

    def test_hardcoding_given_values_fails_hidden_tests(self):
        result = check(level("coins"), "coins = 8\nprint(coins)")
        self.assertFalse(result.passed)
        self.assertIn("coins = 10", result.detail)

    def test_capital_letter_tip(self):
        result = check(level("hello"), 'print("hello, python!")')
        self.assertIn("capital", result.detail)

    def test_print_instead_of_return(self):
        result = check(level("greet"), 'def greet(name):\n    print("Hello, " + name + "!")')
        self.assertIn("return", result.detail)

    def test_bool_must_be_real_bool(self):
        result = check(level("even"), "def is_even(n):\n    return 1 - n % 2")
        self.assertFalse(result.passed)

    def test_rule_words_in_comments_do_not_count(self):
        result = check(level("hop"), '# for\nprint("Hop!")\nprint("Hop!")\nprint("Hop!")')
        self.assertFalse(result.passed)

    def test_error_reports_line(self):
        result = check(level("hello"), 'x = 1\nprint(frend)')
        self.assertFalse(result.passed)
        self.assertEqual(result.error_line, 2)
        self.assertIn("frend", result.detail)


class SandboxTests(unittest.TestCase):
    def test_infinite_loop_is_stopped(self):
        result = run_code("while True:\n    pass")
        self.assertIn("too long", result.friendly)

    def test_except_cannot_swallow_the_step_limit(self):
        result = run_code("try:\n    while True:\n        pass\nexcept Exception:\n    pass")
        self.assertFalse(result.ok)

    def test_imports_are_blocked(self):
        self.assertIn("Imports", run_code("import os").friendly)

    def test_input_is_explained(self):
        self.assertIn("input()", run_code("x = input()").friendly)

    def test_huge_output_is_capped(self):
        self.assertFalse(run_code("for i in range(100000):\n    print('spam')").ok)

    def test_syntax_error_line(self):
        result = run_code('print("hi")\nprint("oops)')
        self.assertEqual(result.line, 2)
        self.assertIn("quote", result.friendly)

    def test_given_values_are_copied(self):
        given = {"bag": ["rope"]}
        run_code("bag.append('map')", given)
        self.assertEqual(given["bag"], ["rope"])


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "save.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_stars_from_hints(self):
        self.assertEqual([stars_for(n) for n in range(4)], [3, 2, 1, 1])

    def test_unlocking_and_saving(self):
        progress = Progress(self.path)
        self.assertTrue(progress.is_unlocked(0))
        self.assertFalse(progress.is_unlocked(1))
        self.assertTrue(progress.record(LEVELS[0].id, 2))
        self.assertFalse(progress.record(LEVELS[0].id, 1))
        progress.set_draft(LEVELS[1].id, "print(1)")
        progress.save()

        again = Progress(self.path)
        self.assertTrue(again.is_unlocked(1))
        self.assertEqual(again.total_stars, 2)
        self.assertEqual(again.next_index(), 1)
        self.assertEqual(again.drafts[LEVELS[1].id], "print(1)")

    def test_odd_jobs_pay_gold_not_stars(self):
        progress = Progress(self.path)
        progress.record(JOBS[0].id, 2)
        self.assertEqual(progress.gold, 20)
        self.assertEqual(progress.total_stars, 0)
        self.assertFalse(progress.is_unlocked(1))

    def test_corrupt_save_is_ignored(self):
        with open(self.path, "w") as fh:
            fh.write("{not json")
        self.assertEqual(Progress(self.path).total_stars, 0)


if __name__ == "__main__":
    unittest.main()
