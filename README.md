# repo-dashboard

Builds a static landing page listing every one of your public GitHub repos that has CI, with its description
and its CI badges. Badges and descriptions come from each repo's README.md where it has them, otherwise they
are generated from the repo's workflows and its GitHub description.

[![Check](https://github.com/kism/repo-dashboard/actions/workflows/check.yml/badge.svg)](https://github.com/kism/repo-dashboard/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/repo-dashboard/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/repo-dashboard/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/repo-dashboard/actions/workflows/test.yml/badge.svg)](https://github.com/kism/repo-dashboard/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/repo-dashboard/graph/badge.svg?token=FPGDA0ODT7)](https://codecov.io/gh/kism/repo-dashboard)

Repo data comes from the [`gh` cli](https://cli.github.com), so it uses whatever you are already logged in as,
there is no token to configure. Forks and archived repos are left off the page.

```bash
repo-dashboard                          # writes site/index.html for the logged in user
repo-dashboard --user someone --output out/index.html
```

## Publishing to GitHub Pages

'.github/workflows/pages.yml' builds the page and deploys it on push to main, daily, and on demand. Enable it
with Settings -> Pages -> Source -> GitHub Actions. The badges are live images, so the page only needs
rebuilding when you add or rename a repo, not when CI runs.

## Prerequisites

Install uv and uvx with the installer script <https://docs.astral.sh/uv/getting-started/installation/>

## Run

### Setup

```bash
uv venv
source .venv/bin/activate
uv sync --all-extras # Omit --all-extras for prod
```

### Running the app

```bash
python -m repo_dashboard
```

## Check/Test

### Checking

Run `ruff check` or get the vscode ruff extension, the rules are defined in pyproject.toml.

### Type Checking

Run `ty`

### Testing

Run `pytest`, It will get its config from pyproject.toml

Of course when you start writing your app many of the tests will break. With the comments it serves as a somewhat tutorial on using `pytest`, that being said I am not an expert.

### Workflows

The '.github' folder has both a Check and Test workflow.

To get the workflow passing badges on your repo, have a look at <https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/adding-a-workflow-status-badge>

Or if you are not using GitHub you can check out workflow badges from your Git hosting service, or use <https://shields.io/> which pretty much covers everything.

### Test Coverage

#### Locally

To get code coverage locally, the config is set in 'pyproject.toml', or run with `pytest`

```bash
python -m http.server -b 127.0.0.1 8000 -d htmlcov
```

Open the link in your browser and browse into the 'htmlcov' directory.

#### Codecov

The template repo uses codecov to get a badge on the README.md, look at their guides on config that up since it's stripped out of this repo.

## Config

Defaults are defined in config.py, and config loading and validation are handled in there too.
