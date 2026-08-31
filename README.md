# repo_dashboard

## Using this template

Rename the app and repo references (replace `your_app` and `youruser/your-repo`):

```bash
NEW_MODULE=your_app                 # python module name, snake_case
NEW_DIST=your-app                   # package/dist name, kebab-case
NEW_REPO=youruser/your-repo         # github <user>/<repo>

git grep -lz -e repo_dashboard -e repo-dashboard -e kism/repo-dashboard | \
  xargs -0 sed -i "s|repo_dashboard|$NEW_MODULE|g; s|repo-dashboard|$NEW_DIST|g; s|kism/repo-dashboard|$NEW_REPO|g"
git mv src/repo_dashboard "src/$NEW_MODULE"
rm -f .github/workflows/dependabot_automerge.yml
rm -rf .venv *.egg-info && uv sync --all-extras

rm -rf .git && git init -q && git add -A && git commit -qm "Initial commit"
```

Then delete this section.

[![Check](https://github.com/kism/repo-dashboard/actions/workflows/check.yml/badge.svg)](https://github.com/kism/repo-dashboard/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/repo-dashboard/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/repo-dashboard/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/repo-dashboard/actions/workflows/test.yml/badge.svg)](https://github.com/kism/repo-dashboard/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/repo-dashboard/graph/badge.svg?token=FPGDA0ODT7)](https://codecov.io/gh/kism/repo-dashboard)

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
