# Contributing

## Local Setup

```bash
python3 -m py_compile wordle-golf.py tests/test_wordle_golf.py
python3 -m unittest discover -s tests -v
```

## Expectations

- Keep dependencies minimal. Pillow is included because PNG scorecard rendering is part of the daily workflow.
- Update `README.md` and `USAGE.md` whenever CLI behavior changes.
- Add or extend tests for every bug fix and user-visible CLI change.
- Keep generated Python cache and virtualenv files out of version control.
- Keep `data/` and `scorecards/` in version control on purpose.
- Treat daily runs as repo mutations: adding a score writes JSON, SQLite, text, and PNG artifacts that are expected to be reviewed and committed.
- Be careful with sample data. Do not replace real score history with throwaway verification output.

## CI

GitHub Actions runs the same compile and unit-test checks on pushes to `master` and on pull requests.
