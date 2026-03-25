#!/usr/bin/env python3
"""
Wordle Golf scoring system.

Daily Wordle performance tracked as an 18-hole golf round.
"""

import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Mapping, Optional

# Players
PLAYERS = ("Gazuty", "Ewan", "AB", "CL")

# Scoring (attempts -> score relative to par)
SCORING = {
    1: -3,  # Ace
    2: -2,  # Eagle
    3: -1,  # Birdie
    4: 0,   # Par
    5: 1,   # Bogey
    6: 2,   # Double bogey
    7: 3,   # Failed (X)
}

# Data paths
DATA_DIR = Path(__file__).parent / "data"
SCORECARDS_DIR = Path(__file__).parent / "scorecards"
SCORES_FILE = DATA_DIR / "scores.json"
CURRENT_FILE = DATA_DIR / "current.json"


def ensure_storage_dirs() -> None:
    """Create storage directories on demand."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCORECARDS_DIR.mkdir(parents=True, exist_ok=True)


def default_round_state() -> Dict[str, object]:
    """Return an empty round state."""
    return {
        "start_date": None,
        "holes_played": 0,
        "scores": {player: 0 for player in PLAYERS},
    }


def today_string() -> str:
    """Return today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def parse_date(value: str) -> str:
    """Validate and normalize a date string."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Date must use YYYY-MM-DD format.") from exc


def parse_date_arg(value: str) -> str:
    """argparse wrapper for parse_date."""
    try:
        return parse_date(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def parse_attempt_value(raw_value: object) -> int:
    """Convert CLI or interactive input into a validated attempt count."""
    token = str(raw_value).strip()
    if token.lower() == "x":
        return 7

    try:
        attempts = int(token)
    except ValueError as exc:
        raise ValueError("Attempts must be 1-7 or X.") from exc

    if not 1 <= attempts <= 7:
        raise ValueError("Attempts must be 1-7 or X.")

    return attempts


def parse_attempt_arg(value: str) -> int:
    """argparse wrapper for parse_attempt_value."""
    try:
        return parse_attempt_value(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def load_scores() -> Dict[str, object]:
    """Load historical scores from JSON."""
    ensure_storage_dirs()
    if not SCORES_FILE.exists():
        return {"rounds": []}

    try:
        with SCORES_FILE.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{SCORES_FILE} is not valid JSON.") from exc

    rounds = data.get("rounds", [])
    if not isinstance(rounds, list):
        raise ValueError(f"{SCORES_FILE} must contain a 'rounds' list.")

    return {"rounds": rounds}


def save_scores(data: Mapping[str, object]) -> None:
    """Save scores to JSON."""
    ensure_storage_dirs()
    with SCORES_FILE.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def load_current_round() -> Dict[str, object]:
    """Load current 18-hole round state."""
    ensure_storage_dirs()
    if not CURRENT_FILE.exists():
        return default_round_state()

    try:
        with CURRENT_FILE.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{CURRENT_FILE} is not valid JSON.") from exc

    scores = data.get("scores", {})
    if not isinstance(scores, dict):
        raise ValueError(f"{CURRENT_FILE} must contain a 'scores' object.")

    return {
        "start_date": data.get("start_date"),
        "holes_played": int(data.get("holes_played", 0)),
        "scores": {player: int(scores.get(player, 0)) for player in PLAYERS},
    }


def save_current_round(data: Mapping[str, object]) -> None:
    """Save current round state."""
    ensure_storage_dirs()
    with CURRENT_FILE.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def calculate_score(attempts: int) -> int:
    """Convert Wordle attempts to golf score."""
    return SCORING.get(attempts, 3)


def score_name(attempts: int) -> str:
    """Get golf term for attempt count."""
    names = {
        1: "Ace",
        2: "Eagle",
        3: "Birdie",
        4: "Par",
        5: "Bogey",
        6: "Double Bogey",
        7: "X",
    }
    return names.get(attempts, "X")


def format_relative_score(score: int, even_label: str = "E") -> str:
    """Format a score relative to par."""
    if score == 0:
        return even_label
    return f"{score:+d}"


def sort_scores(scores: Mapping[str, int]):
    """Sort player scores by score, then name for deterministic tie handling."""
    return sorted(scores.items(), key=lambda item: (item[1], item[0]))


def normalize_scores(scores: Mapping[str, object]) -> Dict[str, int]:
    """Validate that all configured players have a score entry."""
    missing_players = [player for player in PLAYERS if player not in scores]
    extra_players = sorted(set(scores) - set(PLAYERS))

    if missing_players:
        missing = ", ".join(missing_players)
        raise ValueError(f"Missing scores for: {missing}.")
    if extra_players:
        extras = ", ".join(extra_players)
        raise ValueError(f"Unexpected players supplied: {extras}.")

    return {
        player: parse_attempt_value(scores[player])
        for player in PLAYERS
    }


def scorecard_path_for(date: str) -> Path:
    """Return the path for a scorecard."""
    return SCORECARDS_DIR / f"{date}.txt"


def add_daily_score(date: str, scores: Mapping[str, object]) -> str:
    """
    Add a day's Wordle results.

    Args:
        date: YYYY-MM-DD format
        scores: {player: attempts} mapping
    """
    normalized_date = parse_date(date)
    normalized_scores = normalize_scores(scores)
    data = load_scores()
    current = load_current_round()

    if any(entry.get("date") == normalized_date for entry in data["rounds"]):
        raise ValueError(f"Scores for {normalized_date} already exist.")
    if current["holes_played"] >= 18:
        raise ValueError("The current round is already complete. Reset current.json to recover.")

    if current["start_date"] is None:
        current["start_date"] = normalized_date

    golf_scores = {
        player: calculate_score(attempts)
        for player, attempts in normalized_scores.items()
    }

    data["rounds"].append({
        "date": normalized_date,
        "hole": current["holes_played"] + 1,
        "attempts": normalized_scores,
        "scores": golf_scores,
    })

    current["holes_played"] += 1
    for player, score in golf_scores.items():
        current["scores"][player] += score

    save_scores(data)
    save_current_round(current)

    card = generate_scorecard(normalized_date, normalized_scores, golf_scores, current)

    if current["holes_played"] == 18:
        finalize_round(current)

    return card


def generate_scorecard(
    date: str,
    attempts: Mapping[str, int],
    golf_scores: Mapping[str, int],
    current: Mapping[str, object],
) -> str:
    """Generate daily scorecard with witty commentary."""
    hole = current["holes_played"]
    lines = [
        f"🏌️ THE DEGEN MASTERS - Hole {hole}/18",
        f"📅 {date}",
        "",
        f"{'Player':<10} | Attempts | Score           | Total",
        "-" * 49,
    ]

    for player in PLAYERS:
        attempt_value = attempts[player]
        score = golf_scores[player]
        total = current["scores"][player]
        score_label = score_name(attempt_value)
        score_text = f"{format_relative_score(score, '0')} ({score_label})"
        lines.append(
            f"{player:<10} | {attempt_value:^8} | "
            f"{score_text:<15} | "
            f"{format_relative_score(total):>3}"
        )

    lines.extend(["", generate_commentary(golf_scores)])
    card = "\n".join(lines) + "\n"

    ensure_storage_dirs()
    with scorecard_path_for(date).open("w", encoding="utf-8") as handle:
        handle.write(card)

    print(card, end="")
    return card


def generate_commentary(scores: Mapping[str, int]) -> str:
    """Generate witty daily commentary."""
    best_player = min(scores, key=scores.get)
    worst_player = max(scores, key=scores.get)
    best_score = scores[best_player]
    worst_score = scores[worst_player]

    eagles = sum(1 for score in scores.values() if score == -2)
    bogeys = sum(1 for score in scores.values() if score >= 1)

    if best_score <= -2:
        comments = [
            f"🦅 {best_player} with the eagle! Someone's been practicing.",
            f"🎯 {best_player} absolutely crushed it. Two-attempt magic.",
            f"⭐ {best_player} making it look easy out there.",
        ]
    elif worst_score >= 2:
        comments = [
            f"😬 Tough day for {worst_player}. We've all been there.",
            f"🙈 {worst_player} might want to hit the practice range.",
            f"💀 {worst_player} taking the scenic route today.",
        ]
    elif eagles > 1:
        comments = [
            f"🦅🦅 {eagles} eagles today! The course is playing soft.",
            "🔥 Eagles flying everywhere. Is this still difficult mode?",
        ]
    elif bogeys == len(PLAYERS):
        comments = [
            "📉 Full bogey round. Tough words today.",
            "🤷 Everyone struggling. Must be a tricky one.",
        ]
    else:
        comments = [
            f"⛳ Solid round. {best_player} leads the way.",
            f"🎯 {best_player} edges ahead, but it's tight.",
            "📊 Competitive round. Anyone's game!",
        ]

    return f"💬 {random.choice(comments)}"


def finalize_round(current: Mapping[str, object]) -> None:
    """Complete an 18-hole round and declare the winner."""
    print("\n🏆 18-HOLE ROUND COMPLETE! 🏆\n")
    print("Final Standings:")
    print("-" * 30)

    sorted_players = sort_scores(current["scores"])
    for index, (player, score) in enumerate(sorted_players, start=1):
        emoji = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else "  "
        print(f"{emoji} {index}. {player:<10} {format_relative_score(score)}")

    winner = sorted_players[0][0]
    print(f"\n🎉 {winner} wins the round!\n")
    save_current_round(default_round_state())


def show_leaderboard() -> None:
    """Display current tournament standings."""
    current = load_current_round()

    if current["holes_played"] == 0:
        print("No active round.")
        return

    print(f"\n⛳ CURRENT STANDINGS - Hole {current['holes_played']}/18\n")
    print(f"{'Player':<10} | Score")
    print("-" * 25)

    for player, score in sort_scores(current["scores"]):
        print(f"{player:<10} | {format_relative_score(score)}")

    print()


def show_scorecard(date: str) -> None:
    """Print a saved scorecard."""
    normalized_date = parse_date(date)
    path = scorecard_path_for(normalized_date)
    if not path.exists():
        raise FileNotFoundError(f"No saved scorecard exists for {normalized_date}.")

    print(path.read_text(encoding="utf-8"), end="")


def interactive_entry(default_date: Optional[str] = None) -> None:
    """Interactive score entry."""
    print("🏌️ Wordle Golf - Daily Score Entry\n")

    date_hint = default_date or "today"
    while True:
        date = input(f"Date (YYYY-MM-DD) [{date_hint}]: ").strip()
        if not date:
            date = default_date or today_string()

        try:
            date = parse_date(date)
            break
        except ValueError as exc:
            print(exc)

    scores = {}
    for player in PLAYERS:
        while True:
            raw_attempts = input(f"{player}'s attempts (1-7 or X): ").strip()
            try:
                scores[player] = parse_attempt_value(raw_attempts)
                break
            except ValueError as exc:
                print(exc)

    add_daily_score(date, scores)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Wordle Golf scoring")
    parser.add_argument("--date", type=parse_date_arg, help="Date in YYYY-MM-DD format")
    parser.add_argument("--gazuty", type=parse_attempt_arg, help="Gazuty's attempts (1-7 or X)")
    parser.add_argument("--ewan", type=parse_attempt_arg, help="Ewan's attempts (1-7 or X)")
    parser.add_argument("--ab", type=parse_attempt_arg, help="AB's attempts (1-7 or X)")
    parser.add_argument("--cl", type=parse_attempt_arg, help="CL's attempts (1-7 or X)")
    parser.add_argument(
        "--show",
        "--leaderboard",
        dest="leaderboard",
        action="store_true",
        help="Show the current leaderboard",
    )
    parser.add_argument("--scorecard", type=parse_date_arg, help="Print a saved scorecard for a date")

    args = parser.parse_args()
    score_values = [args.gazuty, args.ewan, args.ab, args.cl]
    provided_scores = [value is not None for value in score_values]

    if args.leaderboard:
        if any(provided_scores) or args.date or args.scorecard:
            parser.error("--leaderboard cannot be combined with score entry or scorecard options.")
        show_leaderboard()
        return 0

    if args.scorecard:
        if any(provided_scores):
            parser.error("--scorecard cannot be combined with score entry options.")
        show_scorecard(args.scorecard)
        return 0

    if any(provided_scores) and not all(provided_scores):
        parser.error("Provide scores for all players or omit them all for interactive mode.")

    if all(provided_scores):
        date = args.date or today_string()
        scores = {
            "Gazuty": args.gazuty,
            "Ewan": args.ewan,
            "AB": args.ab,
            "CL": args.cl,
        }
        add_daily_score(date, scores)
        return 0

    interactive_entry(default_date=args.date)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
