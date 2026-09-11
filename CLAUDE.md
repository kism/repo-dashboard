# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Python 3.14, managed with uv. Needs the `gh` cli (logged in) to actually run.

```bash
uv sync --all-extras                     # dev tooling (ty, ruff, pytest, coverage)
.venv/bin/repo-dashboard -vv             # writes site/index.html for the logged-in gh user
.venv/bin/repo-dashboard --user someone --output out/index.html

scripts/run-ci-local.sh                  # ty check, ruff format, ruff check --fix, pytest
.venv/bin/pytest tests/test_dashboard.py::test_gh_returns_stdout   # single test
scripts/run-coverage.sh                  # coverage run + html + report
```

CI (`.github/workflows/`) runs ruff, `ty check .`, `uv build`, and pytest under coverage. `pages.yml` builds the page
with `GH_TOKEN` and deploys `site/` to GitHub Pages on push to main and daily.

## Architecture

Nearly all logic is in `src/repo_dashboard/dashboard.py`; `__main__.py` is just argparse + logging setup.

- All GitHub data comes from shelling out to `gh api` via `_gh()` / `_gh_json()` (`--jq` emitting one JSON object per
  line). A failed `gh` call returns `""`, which means "skip this repo", not an error. There is no token handling.
- `build()` lists the user's repos, drops forks/archived, then runs `build_repo()` per repo in a `ThreadPoolExecutor`.
  A repo is only included if it has active workflows under `.github/workflows/`.
- Badges: the last-push shields.io badge (coloured by `STALE`/`GETTING_STALE`) always comes first, followed by badges
  scraped from the README (images whose URL matches `BADGE_URL_HINTS`), falling back to GitHub workflow status badges.
- Description: the GitHub description, falling back to the README's first prose line before any `##` heading.
  Descriptions are HTML-escaped, then a small subset of inline markdown (links, code) is rendered by the `markdown`
  Jinja filter.
- Output is a single self-contained HTML file: `templates/page.html.j2` with `static/style.css` inlined.
- Tunables (badge cap, description length, worker count, badge host hints) are module constants at the top of
  `dashboard.py`.

## Conventions

- Tests never hit the network: they monkeypatch `subprocess.run` or `dashboard._gh`.
- `tests/test__meta.py` asserts the version in `pyproject.toml`, `uv.lock` and the installed package match, so bump
  the version with `uv version` (or re-run `uv sync`) rather than editing only pyproject.
- Ruff runs with `select = ["ALL"]` plus preview rules. Suppress inline with `# ruff: ignore[rule-name]` and a reason,
  matching existing code.
- `# ponytail:` comments mark deliberate simplifications; keep them when editing nearby code.
