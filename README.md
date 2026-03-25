# ⛳ Wordle Golf

[![CI](https://github.com/gazuty/wordle-golf/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/gazuty/wordle-golf/actions/workflows/ci.yml)

Track four daily Wordle results as an 18-hole golf round.

The CLI stores each day as a hole, keeps a running leaderboard, writes both a text and PNG scorecard, persists the history in SQLite, and resets the active round after hole 18.

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
- Pillow for PNG rendering

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
- Saved scorecards live at `scorecards/YYYY-MM-DD.txt` and `scorecards/YYYY-MM-DD.png`.
- `data/scores.db` stores daily hole entries and player totals for image generation and historical lookup.

## Versioned Data

`data/` and `scorecards/` are intentionally committed to the repository.

Why:
- the repo is small, so keeping the score history in Git is practical
- daily text and PNG scorecards are part of the product, not disposable build output
- the SQLite database gives the renderer and future reporting code a queryable history without needing external infrastructure

Warning:
- every normal scoring run changes tracked files in `data/` and `scorecards/`
- do not run sample commands against the main repo unless you want those artifacts in Git history
- review generated `.txt`, `.png`, `.json`, and `.db` changes before committing or pushing

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
│   ├── scores.db             # SQLite score history used for recent-hole lookups
│   └── current.json          # Active round state
└── scorecards/               # Generated text and PNG scorecards
```

## Notes

- `data/` and `scorecards/` are intentionally committed so the historical record lives with the repo.
- `data/scores.json` is still written for simple inspection and backward compatibility.
- `data/scores.db` is the authoritative queryable store for recent-hole and image rendering data.
- Commentary is intentionally random, so scorecard flavor text will vary between runs.
