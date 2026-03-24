import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "wordle-golf.py"


def load_module():
    spec = importlib.util.spec_from_file_location("wordle_golf", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WordleGolfTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        root = Path(self.temp_dir.name)
        self.module.DATA_DIR = root / "data"
        self.module.SCORECARDS_DIR = root / "scorecards"
        self.module.SCORES_FILE = self.module.DATA_DIR / "scores.json"
        self.module.CURRENT_FILE = self.module.DATA_DIR / "current.json"

    def test_parse_attempt_value_accepts_x_and_rejects_invalid_values(self):
        self.assertEqual(self.module.parse_attempt_value("X"), 7)
        self.assertEqual(self.module.parse_attempt_value("x"), 7)
        self.assertEqual(self.module.parse_attempt_value("6"), 6)

        with self.assertRaises(ValueError):
            self.module.parse_attempt_value("0")

        with self.assertRaises(ValueError):
            self.module.parse_attempt_value("8")

    def test_add_daily_score_writes_history_and_scorecard(self):
        scores = {
            "Gazuty": 4,
            "Ewan": 3,
            "AB": 5,
            "CL": "X",
        }

        with mock.patch.object(self.module.random, "choice", side_effect=lambda options: options[0]):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                card = self.module.add_daily_score("2026-03-24", scores)

        self.assertIn("Hole 1/18", card)
        self.assertIn("Birdie", card)
        self.assertIn("X", card)

        history = json.loads(self.module.SCORES_FILE.read_text(encoding="utf-8"))
        self.assertEqual(len(history["rounds"]), 1)
        self.assertEqual(history["rounds"][0]["attempts"]["CL"], 7)
        self.assertEqual(history["rounds"][0]["scores"]["CL"], 3)

        current = json.loads(self.module.CURRENT_FILE.read_text(encoding="utf-8"))
        self.assertEqual(current["holes_played"], 1)
        self.assertEqual(current["scores"]["Ewan"], -1)

        scorecard = self.module.scorecard_path_for("2026-03-24").read_text(encoding="utf-8")
        self.assertEqual(scorecard, card)
        self.assertIn("💬", stdout.getvalue())

    def test_duplicate_date_is_rejected(self):
        scores = {
            "Gazuty": 4,
            "Ewan": 4,
            "AB": 4,
            "CL": 4,
        }

        with contextlib.redirect_stdout(io.StringIO()):
            self.module.add_daily_score("2026-03-24", scores)

        with self.assertRaisesRegex(ValueError, "already exist"):
            with contextlib.redirect_stdout(io.StringIO()):
                self.module.add_daily_score("2026-03-24", scores)

    def test_invalid_date_is_rejected(self):
        scores = {
            "Gazuty": 4,
            "Ewan": 4,
            "AB": 4,
            "CL": 4,
        }

        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            with contextlib.redirect_stdout(io.StringIO()):
                self.module.add_daily_score("2026/03/24", scores)

    def test_show_scorecard_prints_saved_card(self):
        scores = {
            "Gazuty": 4,
            "Ewan": 3,
            "AB": 5,
            "CL": 7,
        }

        with contextlib.redirect_stdout(io.StringIO()):
            self.module.add_daily_score("2026-03-24", scores)

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.module.show_scorecard("2026-03-24")

        self.assertIn("Hole 1/18", stdout.getvalue())
        self.assertIn("Gazuty", stdout.getvalue())

    def test_main_rejects_partial_score_arguments(self):
        argv = ["wordle-golf.py", "--gazuty", "4"]
        stderr = io.StringIO()

        with mock.patch.object(sys, "argv", argv):
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc:
                    self.module.main()

        self.assertEqual(exc.exception.code, 2)
        self.assertIn("Provide scores for all players", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
