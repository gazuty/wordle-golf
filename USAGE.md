# Wordle Golf Usage Guide

## Quick Start

Fastest path:

```bash
python3 wordle-golf.py --gazuty 4 --ewan 3 --ab 5 --cl X
```

That uses today's date automatically.

Specify an explicit date:

```bash
python3 wordle-golf.py --date 2026-03-24 \
  --gazuty 4 --ewan 3 --ab 5 --cl 2
```

Interactive mode:

```bash
python3 wordle-golf.py
```

You can also prefill the interactive date prompt:

```bash
python3 wordle-golf.py --date 2026-03-24
```

## Accepted Input

- Attempts must be `1` through `7`, or `X`.
- `X` and `7` both score as a failed hole worth `+3`.
- CLI score entry must include all four players.
- Dates must use `YYYY-MM-DD`.

## Viewing Results

Current leaderboard:

```bash
python3 wordle-golf.py --leaderboard
```

Backward-compatible alias:

```bash
python3 wordle-golf.py --show
```

Print a saved scorecard:

```bash
python3 wordle-golf.py --scorecard 2026-03-24
```

Daily scorecards are also written to `scorecards/YYYY-MM-DD.txt` and `scorecards/YYYY-MM-DD.png`.

## Tournament Flow

1. The first saved day starts a new 18-hole round.
2. Each valid day increments the hole count by one.
3. After hole 18, the script prints final standings and resets `data/current.json`.
4. Historical hole-by-hole entries remain in `data/scores.json` and `data/scores.db`.

## Safety Checks

- Duplicate dates are rejected to prevent accidental double-entry.
- Partial CLI score input fails fast instead of switching into interactive mode.
- Missing scorecards return a clear error message.
- Invalid JSON in `data/current.json` or `data/scores.json` stops execution with an explicit error.

## Data Storage

- `data/current.json`: active round start date, holes played, and cumulative scores
- `data/scores.json`: append-only JSON history of saved hole entries
- `data/scores.db`: SQLite history used for recent-hole panels and queryable reporting
- `scorecards/`: generated text and PNG scorecards by date

These files are intentionally committed to Git. A normal scoring run changes tracked repository state, so avoid using fake dates or test scores in the main checkout unless you intend to commit them.

## Testing

Run the regression suite:

```bash
python3 -m unittest discover -s tests -v
```

## Known Limitations

- Player names are hard-coded in `wordle-golf.py`.
- History is stored as a flat sequence of hole entries rather than grouped round summaries.
- There is no import or OCR flow yet; all score entry is manual.
