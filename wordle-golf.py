#!/usr/bin/env python3
"""
Wordle Golf Scoring System
Daily Wordle performance tracked as 18-hole golf
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Players
PLAYERS = ["Gazuty", "Ewan", "AB", "CL"]

# Scoring (attempts -> score relative to par)
SCORING = {
    1: -3,  # Hole in one
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

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
SCORECARDS_DIR.mkdir(exist_ok=True)


def load_scores() -> Dict:
    """Load historical scores from JSON."""
    if SCORES_FILE.exists():
        with open(SCORES_FILE) as f:
            return json.load(f)
    return {"rounds": []}


def save_scores(data: Dict):
    """Save scores to JSON."""
    with open(SCORES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_current_round() -> Dict:
    """Load current 18-hole round state."""
    if CURRENT_FILE.exists():
        with open(CURRENT_FILE) as f:
            return json.load(f)
    return {
        "start_date": None,
        "holes_played": 0,
        "scores": {player: 0 for player in PLAYERS}
    }


def save_current_round(data: Dict):
    """Save current round state."""
    with open(CURRENT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def calculate_score(attempts: int) -> int:
    """Convert Wordle attempts to golf score."""
    return SCORING.get(attempts, 3)  # Default to +3 for 7+ (X)


def score_name(attempts: int) -> str:
    """Get golf term for attempt count."""
    names = {
        1: "ACE!",
        2: "Eagle",
        3: "Birdie",
        4: "Par",
        5: "Bogey",
        6: "Double Bogey",
        7: "X"
    }
    return names.get(attempts, "X")


def add_daily_score(date: str, scores: Dict[str, int]):
    """
    Add a day's Wordle results.
    
    Args:
        date: YYYY-MM-DD format
        scores: {player: attempts} mapping
    """
    data = load_scores()
    current = load_current_round()
    
    # Initialize round if needed
    if current["start_date"] is None:
        current["start_date"] = date
    
    # Calculate golf scores
    golf_scores = {player: calculate_score(attempts) for player, attempts in scores.items()}
    
    # Record in history
    data["rounds"].append({
        "date": date,
        "hole": current["holes_played"] + 1,
        "attempts": scores,
        "scores": golf_scores
    })
    
    # Update current round
    current["holes_played"] += 1
    for player, score in golf_scores.items():
        current["scores"][player] += score
    
    save_scores(data)
    save_current_round(current)
    
    # Generate scorecard
    generate_scorecard(date, scores, golf_scores, current)
    
    # Check if round complete
    if current["holes_played"] == 18:
        finalize_round(current)


def generate_scorecard(date: str, attempts: Dict[str, int], golf_scores: Dict[str, int], current: Dict):
    """Generate daily scorecard with witty commentary."""
    hole = current["holes_played"]
    
    # Build scorecard
    card = f"""
🏌️ WORDLE GOLF - Hole {hole}/18
📅 {date}

{'Player':<10} | Attempts | Score | Total
{'-'*45}
"""
    
    for player in PLAYERS:
        att = attempts[player]
        score = golf_scores[player]
        total = current["scores"][player]
        score_label = score_name(att)
        sign = "+" if score > 0 else ""
        
        card += f"{player:<10} | {att:^8} | {sign}{score:^5} ({score_label}) | {total:+d}\n"
    
    # Generate witty commentary
    commentary = generate_commentary(attempts, golf_scores, hole)
    
    card += f"\n{commentary}\n"
    
    # Save scorecard
    scorecard_path = SCORECARDS_DIR / f"{date}.txt"
    with open(scorecard_path, "w") as f:
        f.write(card)
    
    print(card)
    return card


def generate_commentary(attempts: Dict[str, int], scores: Dict[str, int], hole: int) -> str:
    """Generate witty daily commentary."""
    import random
    
    # Find best/worst performers
    best_player = min(scores, key=scores.get)
    worst_player = max(scores, key=scores.get)
    best_score = scores[best_player]
    worst_score = scores[worst_player]
    
    # Count eagles, birdies, bogeys
    eagles = sum(1 for s in scores.values() if s == -2)
    birdies = sum(1 for s in scores.values() if s == -1)
    bogeys = sum(1 for s in scores.values() if s >= 1)
    
    # Commentary templates
    if best_score <= -2:
        comments = [
            f"🦅 {best_player} with the eagle! Someone's been practicing.",
            f"🎯 {best_player} absolutely crushed it. Two-attempt magic.",
            f"⭐ {best_player} making it look easy out there."
        ]
    elif worst_score >= 2:
        comments = [
            f"😬 Tough day for {worst_player}. We've all been there.",
            f"🙈 {worst_player} might want to hit the practice range.",
            f"💀 {worst_player} taking the scenic route today."
        ]
    elif eagles > 1:
        comments = [
            f"🦅🦅 {eagles} eagles today! The course is playing soft.",
            "🔥 Eagles flying everywhere. Is this still difficult mode?",
        ]
    elif bogeys == 4:
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


def finalize_round(current: Dict):
    """Complete 18-hole round and declare winner."""
    print(f"\n🏆 18-HOLE ROUND COMPLETE! 🏆\n")
    print("Final Standings:")
    print("-" * 30)
    
    sorted_players = sorted(current["scores"].items(), key=lambda x: x[1])
    
    for i, (player, score) in enumerate(sorted_players, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "   "
        print(f"{emoji} {i}. {player:<10} {score:+d}")
    
    winner = sorted_players[0][0]
    print(f"\n🎉 {winner} wins the round!\n")
    
    # Reset for new round
    save_current_round({
        "start_date": None,
        "holes_played": 0,
        "scores": {player: 0 for player in PLAYERS}
    })


def show_leaderboard():
    """Display current tournament standings."""
    current = load_current_round()
    
    if current["holes_played"] == 0:
        print("No active round.")
        return
    
    print(f"\n⛳ CURRENT STANDINGS - Hole {current['holes_played']}/18\n")
    print(f"{'Player':<10} | Score")
    print("-" * 25)
    
    sorted_players = sorted(current["scores"].items(), key=lambda x: x[1])
    for player, score in sorted_players:
        print(f"{player:<10} | {score:+d}")
    
    print()


def interactive_entry():
    """Interactive score entry."""
    print("🏌️ Wordle Golf - Daily Score Entry\n")
    
    date = input("Date (YYYY-MM-DD) [today]: ").strip()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    scores = {}
    for player in PLAYERS:
        while True:
            try:
                attempts = int(input(f"{player}'s attempts (1-7, X=7): "))
                if 1 <= attempts <= 7:
                    scores[player] = attempts
                    break
                else:
                    print("Enter 1-7")
            except ValueError:
                print("Enter a number")
    
    add_daily_score(date, scores)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Wordle Golf Scoring")
    parser.add_argument("--date", help="Date (YYYY-MM-DD)")
    parser.add_argument("--gazuty", type=int, help="Gazuty's attempts")
    parser.add_argument("--ewan", type=int, help="Ewan's attempts")
    parser.add_argument("--ab", type=int, help="AB's attempts")
    parser.add_argument("--cl", type=int, help="CL's attempts")
    parser.add_argument("--show", action="store_true", help="Show current standings")
    parser.add_argument("--leaderboard", action="store_true", help="Show leaderboard")
    
    args = parser.parse_args()
    
    if args.show or args.leaderboard:
        show_leaderboard()
    elif args.gazuty and args.ewan and args.ab and args.cl:
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        scores = {
            "Gazuty": args.gazuty,
            "Ewan": args.ewan,
            "AB": args.ab,
            "CL": args.cl
        }
        add_daily_score(date, scores)
    else:
        interactive_entry()


if __name__ == "__main__":
    main()
