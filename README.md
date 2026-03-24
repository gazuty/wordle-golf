# ⛳ Wordle Golf

[![CI](https://github.com/gazuty/wordle-golf/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/gazuty/wordle-golf/actions/workflows/ci.yml)

Track four daily Wordle results as an 18-hole golf round.

The CLI stores each day as a hole, keeps a running leaderboard, writes a text scorecard, and resets the active round after hole 18.

## Scoring

| Attempts | Golf Term | Relative Score |
|----------|-----------|----------------|
| 1 | Ace | -3 |
| 2 | Eagle | -2 |
| 3 | Birdie | -1 |
| 4 | Par | 0 |
| 5 | Bogey | +1 |
| 6 | Double Bogey | +2 |
| X or 7 | Failed hole | +3 |

## Requirements

- Python 3
- No external dependencies

## Install

```bash
pip install -r requirements.txt
```

## Common Commands

Record a day's scores:

```bash
python3 wordle-golf.py --date 2026-03-24 \
  --gazuty 4 --ewan 3 --ab 5 --cl X
```

Interactive entry:

```bash
python3 wordle-golf.py
```

Show the active leaderboard:

```bash
python3 wordle-golf.py --leaderboard
```

`--show` is kept as an alias for `--leaderboard`.

Print a saved scorecard:

```bash
python3 wordle-golf.py --scorecard 2026-03-24
```

## Operational Guardrails

- A date can only be entered once. Duplicate entries are rejected instead of silently advancing the round twice.
- CLI score entry requires all four players. Partial score flags return an error instead of dropping into interactive mode.
- Interactive entry accepts `X` as well as `7`.
- Saved scorecards live at `scorecards/YYYY-MM-DD.txt`.

## Testing

```bash
python3 -m py_compile wordle-golf.py tests/test_wordle_golf.py
python3 -m unittest discover -s tests -v
```

CI runs the same checks on pushes to `master` and pull requests.

## Project Structure

```text
wordle-golf/
├── wordle-golf.py            # CLI, scoring rules, persistence, scorecard output
├── README.md
├── USAGE.md
├── CONTRIBUTING.md
├── requirements.txt
├── .github/workflows/ci.yml   # GitHub Actions health checks
├── tests/
│   └── test_wordle_golf.py   # Regression coverage for validation and file output
├── data/
│   ├── scores.json           # Historical hole-by-hole entries
│   └── current.json          # Active round state
└── scorecards/               # Generated text scorecards
```

## Notes

- `data/` and `scorecards/` are git-ignored local state.
- `data/scores.json` stores one entry per day or hole, not one nested object per 18-hole round.
- Commentary is intentionally random, so scorecard flavor text will vary between runs.
