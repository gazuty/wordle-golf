#!/usr/bin/env python3
"""
Wordle Golf scoring system.

Daily Wordle performance tracked as an 18-hole golf round.
"""

import argparse
from contextlib import closing
import json
import random
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

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
DB_FILE = DATA_DIR / "scores.db"

IMAGE_WIDTH = 1600
IMAGE_HEIGHT = 900
RECENT_HOLES_TO_SHOW = 4


def ensure_storage_dirs() -> None:
    """Create storage directories on demand."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCORECARDS_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Open the local score database, creating schema on first use."""
    ensure_storage_dirs()
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS holes (
            date TEXT PRIMARY KEY,
            hole_number INTEGER NOT NULL,
            round_start_date TEXT NOT NULL,
            commentary TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS player_scores (
            date TEXT NOT NULL,
            player TEXT NOT NULL,
            attempts INTEGER NOT NULL,
            daily_score INTEGER NOT NULL,
            total_score INTEGER NOT NULL,
            PRIMARY KEY (date, player),
            FOREIGN KEY (date) REFERENCES holes(date) ON DELETE CASCADE
        )
        """
    )
    return connection


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


def scorecard_image_path_for(date: str) -> Path:
    """Return the path for a PNG scorecard."""
    return SCORECARDS_DIR / f"{date}.png"


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


def save_score_to_database(
    date: str,
    hole_number: int,
    round_start_date: str,
    attempts: Mapping[str, int],
    golf_scores: Mapping[str, int],
    totals: Mapping[str, int],
    commentary: str,
) -> None:
    """Persist one daily score entry to SQLite."""
    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO holes (date, hole_number, round_start_date, commentary)
            VALUES (?, ?, ?, ?)
            """,
            (date, hole_number, round_start_date, commentary),
        )
        connection.executemany(
            """
            INSERT INTO player_scores (date, player, attempts, daily_score, total_score)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (date, player, attempts[player], golf_scores[player], totals[player])
                for player in PLAYERS
            ],
        )
        connection.commit()


def load_recent_holes(limit: int = RECENT_HOLES_TO_SHOW) -> List[Dict[str, object]]:
    """Return the most recent holes for leaderboard context."""
    with closing(get_connection()) as connection:
        hole_rows = connection.execute(
            """
            SELECT date, hole_number
            FROM holes
            ORDER BY date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        recent_holes = []
        for hole_row in hole_rows:
            score_rows = connection.execute(
                """
                SELECT player, attempts, daily_score
                FROM player_scores
                WHERE date = ?
                ORDER BY player
                """,
                (hole_row["date"],),
            ).fetchall()
            recent_holes.append({
                "date": hole_row["date"],
                "hole": hole_row["hole_number"],
                "scores": {
                    row["player"]: {
                        "attempts": row["attempts"],
                        "daily_score": row["daily_score"],
                    }
                    for row in score_rows
                },
            })

    recent_holes.reverse()
    return recent_holes


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

    commentary = generate_commentary(golf_scores)
    save_score_to_database(
        normalized_date,
        int(current["holes_played"]),
        str(current["start_date"]),
        normalized_scores,
        golf_scores,
        current["scores"],
        commentary,
    )

    card = generate_scorecard(
        normalized_date,
        normalized_scores,
        golf_scores,
        current,
        commentary,
    )
    render_scorecard_png(
        normalized_date,
        normalized_scores,
        golf_scores,
        current,
        commentary,
        load_recent_holes(),
    )

    if current["holes_played"] == 18:
        finalize_round(current)

    return card


def generate_scorecard(
    date: str,
    attempts: Mapping[str, int],
    golf_scores: Mapping[str, int],
    current: Mapping[str, object],
    commentary: str,
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

    lines.extend(["", commentary])
    card = "\n".join(lines) + "\n"

    ensure_storage_dirs()
    with scorecard_path_for(date).open("w", encoding="utf-8") as handle:
        handle.write(card)

    print(card, end="")
    return card


def find_font(candidates: Sequence[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load the first available font from a short candidate list."""
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def get_fonts() -> Dict[str, ImageFont.ImageFont]:
    """Return a consistent font set for rendering scorecards."""
    sans_regular = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    sans_bold = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/SFNSRounded.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    emoji = [
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/System/Library/Fonts/Apple Color Emoji.ttc",
    ]
    return {
        "title": find_font(sans_bold, 52),
        "subtitle": find_font(sans_regular, 26),
        "header": find_font(sans_bold, 24),
        "body": find_font(sans_regular, 24),
        "small": find_font(sans_regular, 18),
        "emoji": find_font(emoji + sans_regular, 54),
    }


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    anchor: Tuple[int, int],
    fill: str,
) -> None:
    """Draw text with a single fallback path for color emoji capable fonts."""
    try:
        draw.text(anchor, text, font=font, fill=fill, embedded_color=True)
    except TypeError:
        draw.text(anchor, text, font=font, fill=fill)


def draw_green_icon(draw: ImageDraw.ImageDraw, origin: Tuple[int, int], fonts: Mapping[str, ImageFont.ImageFont]) -> None:
    """Draw a small putting-green mark for the image header."""
    x, y = origin
    draw.ellipse((x, y + 40, x + 160, y + 120), fill="#3FAE49", outline="#146C2E", width=4)
    draw.ellipse((x + 45, y + 58, x + 115, y + 93), fill="#8ADE78", outline="#2F8C3E", width=2)
    draw.line((x + 92, y + 6, x + 92, y + 78), fill="#FFF4CC", width=5)
    draw.polygon([(x + 92, y + 8), (x + 145, y + 28), (x + 92, y + 48)], fill="#F44336")
    fit_text(draw, "⛳", fonts["emoji"], (x + 10, y - 4), "#FFFFFF")


def score_to_color(score: int) -> str:
    """Return a color keyed to golf scoring."""
    if score <= -2:
        return "#0E9F6E"
    if score == -1:
        return "#2A7E4F"
    if score == 0:
        return "#D5C8A7"
    if score == 1:
        return "#D98841"
    return "#C0392B"


def draw_round_table(
    draw: ImageDraw.ImageDraw,
    fonts: Mapping[str, ImageFont.ImageFont],
    attempts: Mapping[str, int],
    golf_scores: Mapping[str, int],
    current: Mapping[str, object],
) -> None:
    """Draw the main leaderboard block."""
    table_left = 90
    table_top = 220
    row_height = 90
    col_x = [table_left, 440, 700, 1050, 1320]

    draw.rounded_rectangle((70, 190, 1530, 610), radius=24, fill="#103B25", outline="#D6B25E", width=3)
    headers = ["Player", "Attempts", "Today", "Golf", "Total"]
    for index, header in enumerate(headers):
        draw.text((col_x[index], table_top), header, font=fonts["header"], fill="#F7E7B4")

    draw.line((90, table_top + 42, 1490, table_top + 42), fill="#D6B25E", width=2)

    for row, player in enumerate(PLAYERS):
        y = table_top + 70 + row * row_height
        attempt_value = attempts[player]
        daily_score = golf_scores[player]
        total_score = int(current["scores"][player])
        cell_color = score_to_color(daily_score)

        draw.text((col_x[0], y), player, font=fonts["body"], fill="#FFFFFF")
        draw.text((col_x[1], y), str(attempt_value), font=fonts["body"], fill="#FFFFFF")
        draw.text((col_x[2], y), score_name(attempt_value), font=fonts["body"], fill=cell_color)
        draw.text((col_x[3], y), format_relative_score(daily_score, "0"), font=fonts["body"], fill=cell_color)
        draw.text((col_x[4], y), format_relative_score(total_score), font=fonts["body"], fill="#FFFFFF")

        if row < len(PLAYERS) - 1:
            draw.line((90, y + 52, 1490, y + 52), fill="#27563D", width=1)


def draw_recent_holes_panel(
    draw: ImageDraw.ImageDraw,
    fonts: Mapping[str, ImageFont.ImageFont],
    recent_holes: Sequence[Mapping[str, object]],
) -> None:
    """Draw a compact panel with recent hole scoring."""
    panel = (70, 650, 1530, 840)
    draw.rounded_rectangle(panel, radius=24, fill="#F4EBD5", outline="#D6B25E", width=3)
    draw.text((95, 675), "Recent Holes", font=fonts["header"], fill="#103B25")

    if not recent_holes:
        draw.text((95, 725), "No history recorded yet.", font=fonts["body"], fill="#103B25")
        return

    start_x = 340
    col_width = 270
    for index, hole in enumerate(recent_holes):
        x = start_x + index * col_width
        label = f"H{hole['hole']}  {hole['date']}"
        draw.text((x, 680), label, font=fonts["small"], fill="#6B5A32")

        for row, player in enumerate(PLAYERS):
            player_data = hole["scores"][player]
            daily_score = int(player_data["daily_score"])
            y = 720 + row * 28
            draw.text((x, y), player, font=fonts["small"], fill="#103B25")
            summary = f"{player_data['attempts']} / {format_relative_score(daily_score, '0')}"
            draw.text((x + 120, y), summary, font=fonts["small"], fill=score_to_color(daily_score))


def render_scorecard_png(
    date: str,
    attempts: Mapping[str, int],
    golf_scores: Mapping[str, int],
    current: Mapping[str, object],
    commentary: str,
    recent_holes: Sequence[Mapping[str, object]],
) -> Path:
    """Render a social-shareable PNG scorecard."""
    ensure_storage_dirs()
    fonts = get_fonts()
    image = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), "#0B281A")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, IMAGE_WIDTH, IMAGE_HEIGHT), fill="#0B281A")
    draw.rounded_rectangle((25, 25, IMAGE_WIDTH - 25, IMAGE_HEIGHT - 25), radius=36, outline="#D6B25E", width=4)
    draw.ellipse((-220, -260, 520, 280), fill="#17472F")
    draw.ellipse((1120, 640, 1820, 1160), fill="#17472F")
    draw.rectangle((0, 150, IMAGE_WIDTH, 190), fill="#0F3321")

    draw_green_icon(draw, (110, 40), fonts)
    draw.text((300, 55), "The Degen Masters", font=fonts["title"], fill="#F7E7B4")
    draw.text(
        (304, 120),
        f"Hole {current['holes_played']}/18  |  {date}  |  Leaderboard to Par",
        font=fonts["subtitle"],
        fill="#E9DFC5",
    )
    draw.text((90, 160), commentary, font=fonts["body"], fill="#F7E7B4")

    draw_round_table(draw, fonts, attempts, golf_scores, current)
    draw_recent_holes_panel(draw, fonts, recent_holes)

    path = scorecard_image_path_for(date)
    image.save(path, format="PNG")
    return path


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
