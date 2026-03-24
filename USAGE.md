# Wordle Golf Usage Guide

## Quick Start

### Option 1: Command Line (Fastest)

```bash
python wordle-golf.py --gazuty 4 --ewan 3 --ab 5 --cl 2
```

This automatically uses today's date.

### Option 2: Specify Date

```bash
python wordle-golf.py --date 2026-03-24 \
  --gazuty 4 --ewan 3 --ab 5 --cl 2
```

### Option 3: Interactive Mode

```bash
python wordle-golf.py
```

Prompts you for each player's score.

## Viewing Results

### Current Standings

```bash
python wordle-golf.py --leaderboard
```

Shows cumulative scores for the current 18-hole round.

### Individual Scorecards

Daily scorecards are saved in `scorecards/YYYY-MM-DD.txt` and printed to console when entering scores.

## Scoring Reference

| Attempts | Golf Term | Score |
|----------|-----------|-------|
| 1 | Ace! | -3 |
| 2 | Eagle | -2 |
| 3 | Birdie | -1 |
| 4 | Par | 0 |
| 5 | Bogey | +1 |
| 6 | Double Bogey | +2 |
| 7+ / X | Failed | +3 |

## Tournament Flow

1. **Round starts**: First score entry initializes a new 18-hole round
2. **Daily play**: Enter scores for 18 consecutive days (or holes)
3. **Round completes**: After hole 18, winner is declared and standings reset
4. **New round**: Next score entry starts fresh

## Data Storage

- **`data/scores.json`**: Complete historical record of all rounds
- **`data/current.json`**: Active round state (cumulative scores)
- **`scorecards/`**: Daily scorecard text files

## Tips

- Keep screenshots or records of your actual Wordle results for accurate entry
- Commentary is randomly selected — you'll get different quips for similar performances
- All data is stored locally in the repo (git-ignored to avoid bloat)
- The system assumes you play consecutively — gaps in dates are fine but won't affect hole numbering

## Future Enhancements

When you're ready, we can add:

- **OCR screenshot parsing**: Drop images, auto-extract scores
- **Web interface**: Visual scorecards and charts
- **Export formats**: PDF, HTML, or social media graphics
- **Statistical analysis**: Trends, averages, best/worst performances
- **Multi-round history**: Track multiple 18-hole tournaments over time
