# repo-dashboard

Builds a static landing page listing every one of your public GitHub repos that has CI, with its description and
its CI badges, led by a badge showing the last push to its default branch (orange over six months old, red over
two years). Other badges and descriptions come from each repo's README.md where it has them, otherwise they are
generated from the repo's workflows and its GitHub description. Forks and archived repos are left off.

[![Check](https://github.com/kism/repo-dashboard/actions/workflows/check.yml/badge.svg)](https://github.com/kism/repo-dashboard/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/repo-dashboard/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/repo-dashboard/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/repo-dashboard/actions/workflows/test.yml/badge.svg)](https://github.com/kism/repo-dashboard/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/repo-dashboard/graph/badge.svg?token=FPGDA0ODT7)](https://codecov.io/gh/kism/repo-dashboard)

Repo data comes from the [`gh` cli](https://cli.github.com), so it uses whatever you are already logged in as,
there is no token to configure.

```bash
uv sync                                 # or `uv sync --all-extras` for the dev tooling
repo-dashboard                          # writes site/index.html for the logged in user
repo-dashboard --user someone --output out/index.html
repo-dashboard -vv                      # -v per level of verbosity
```

## Publishing to GitHub Pages

'.github/workflows/pages.yml' builds the page and deploys it on push to main, daily, and on demand. Enable it
with Settings -> Pages -> Source -> GitHub Actions. The CI badges are live images, so the page only needs
rebuilding when you add or rename a repo, not when CI runs; the daily run keeps the last-push badges current.

## Development

Needs [uv](https://docs.astral.sh/uv/getting-started/installation/) and `gh`. `ruff check`, `ty` and `pytest`
all take their config from pyproject.toml. Tunables (badge cap, description length, badge host hints) are
constants at the top of 'dashboard.py'.
