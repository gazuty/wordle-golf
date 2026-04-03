#!/usr/bin/env python3
"""Run the standard daily Wordle Golf process."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
MAIN_SCRIPT = REPO_ROOT / "wordle-golf.py"
SCORECARD_DIR = REPO_ROOT / "scorecards"
PLAYERS = ("gazuty", "ewan", "ab", "cl")
PLAYER_DISPLAY = {
    "gazuty": "Gazuty",
    "ewan": "Ewan",
    "ab": "AB",
    "cl": "CL",
}


def yesterday_string() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def run_command(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=capture,
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the standard Wordle Golf daily process")
    parser.add_argument("--date", default=yesterday_string(), help="Score date in YYYY-MM-DD format (default: yesterday)")
    parser.add_argument("--gazuty", required=True, help="Gazuty attempts (1-7 or X)")
    parser.add_argument("--ewan", required=True, help="Ewan attempts (1-7 or X)")
    parser.add_argument("--ab", required=True, help="AB attempts (1-7 or X)")
    parser.add_argument("--cl", required=True, help="CL attempts (1-7 or X)")
    parser.add_argument("--skip-tests", action="store_true", help="Skip compile and unit test verification")
    parser.add_argument("--skip-commit", action="store_true", help="Do not create a git commit")
    parser.add_argument("--skip-push", action="store_true", help="Do not push after commit")
    parser.add_argument("--skip-photos", action="store_true", help="Do not import the scorecard into Apple Photos")
    return parser.parse_args()


def add_scores(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        str(MAIN_SCRIPT),
        "--date",
        args.date,
    ]
    for player in PLAYERS:
        command.extend([f"--{player}", str(getattr(args, player))])
    run_command(command)


def run_verification(args: argparse.Namespace) -> None:
    run_command([sys.executable, str(MAIN_SCRIPT), "--leaderboard"])
    if args.skip_tests:
        return
    run_command([sys.executable, "-m", "py_compile", str(MAIN_SCRIPT), "tests/test_wordle_golf.py"])
    run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])


def commit_changes(date_value: str) -> None:
    scorecard_png = SCORECARD_DIR / f"{date_value}.png"
    scorecard_txt = SCORECARD_DIR / f"{date_value}.txt"
    run_command([
        "git",
        "add",
        "data/current.json",
        "data/scores.json",
        "data/scores.db",
        str(scorecard_txt.relative_to(REPO_ROOT)),
        str(scorecard_png.relative_to(REPO_ROOT)),
    ])
    run_command(["git", "commit", "-m", f"Add Wordle Golf results for {date_value}"])


def push_changes() -> None:
    run_command(["git", "push"])


def import_to_photos(date_value: str) -> None:
    scorecard_png = SCORECARD_DIR / f"{date_value}.png"
    applescript = f'''
set theFile to POSIX file "{scorecard_png}"
tell application "Photos"
    activate
    import {{theFile}} skip check duplicates no
end tell
'''
    run_command(["osascript", "-e", applescript])


def main() -> int:
    args = parse_args()

    try:
        add_scores(args)
        run_verification(args)
        if not args.skip_commit:
            commit_changes(args.date)
            if not args.skip_push:
                push_changes()
        if not args.skip_photos:
            import_to_photos(args.date)
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout, end="", file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, end="", file=sys.stderr)
        return exc.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
