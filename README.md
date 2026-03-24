# ⛳ Wordle Golf

Daily Wordle performance tracking with golf scoring and witty commentary.

## The Game

Four players compete in Wordle as if playing 18-hole golf, with each hole being par 4:

- **Par (4 attempts)**: Even
- **Birdie (3 attempts)**: -1
- **Eagle (2 attempts)**: -2  
- **Ace (1 attempt)**: -3 *(rare!)*
- **Bogey (5 attempts)**: +1
- **Double Bogey (6 attempts)**: +2
- **X (failed)**: +3

## Players

- **Gazuty**
- **Ewan**
- **AB**
- **CL**

## Usage

### Daily Score Entry

```bash
python wordle-golf.py --date 2026-03-24 \
  --gazuty 4 --ewan 3 --ab 5 --cl 2
```

Or interactive mode:

```bash
python wordle-golf.py
```

### View Scorecards

```bash
# Today's scorecard
python wordle-golf.py --show

# Full tournament standings
python wordle-golf.py --leaderboard
```

## Project Structure

```
wordle-golf/
├── wordle-golf.py       # Main scoring engine
├── data/
│   ├── scores.json      # Historical scores
│   └── current.json     # Current 18-hole round state
├── scorecards/          # Generated daily scorecards
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Future Features

- Screenshot OCR ingestion
- Web dashboard
- Twitter/Slack integration for auto-posting
- Historical analysis and stats
