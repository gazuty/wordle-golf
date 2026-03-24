# Contributing

## Local Setup

```bash
python3 -m py_compile wordle-golf.py tests/test_wordle_golf.py
python3 -m unittest discover -s tests -v
```

## Expectations

- Keep the CLI dependency-free unless there is a clear operational need.
- Update `README.md` and `USAGE.md` whenever CLI behavior changes.
- Add or extend tests for every bug fix and user-visible CLI change.
- Keep generated local artifacts out of version control.

## CI

GitHub Actions runs the same compile and unit-test checks on pushes to `master` and on pull requests.
