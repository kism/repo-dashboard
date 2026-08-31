"""Build a static landing page listing GitHub repos that have CI."""

import html
import json
import re
import subprocess  # ruff: ignore[suspicious-subprocess-import] we shell out to the `gh` cli rather than reimplement its auth
import textwrap
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from .constants import OUR_TIMEZONE, PROGRAM_REPO_URL
from .utils.logger import get_logger

logger = get_logger(__name__)

WORKFLOW_DIR = ".github/workflows/"
MAX_BADGES = 8
MAX_DESCRIPTION_LEN = 200
API_WORKERS = 8

# ponytail: a badge is an image from a known badge host, everything else in a README is a screenshot or a logo.
BADGE_URL_HINTS = ("badge", "shields.io", "codecov")

# Matches `![alt](image)` and `[![alt](image)](link)`, ignoring any markdown title after the url.
BADGE_RE = re.compile(r"\[?!\[([^\]]*)\]\(([^)\s]+)[^)]*\)(?:\]\(([^)\s]+)[^)]*\))?")

# Lines that start with these are markup, not prose, so they can't be a fallback description.
MARKUP_PREFIXES = ("#", "!", "[", "<", ">", "|", "-", "*", "`", "=", "_", "+")


@dataclass
class Badge:
    """A CI status badge; `link` is empty for an image that wasn't wrapped in a link."""

    alt: str
    image: str
    link: str = ""


@dataclass
class Repo:
    """A repo with CI, as rendered onto the page."""

    name: str
    url: str
    description: str = ""
    badges: list[Badge] = field(default_factory=list)


def _gh(*args: str) -> str:
    """Run the `gh` cli, returning stdout, or an empty string if the call failed."""
    try:
        result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)  # ruff: ignore[subprocess-without-shell-equals-true, start-process-with-partial-path]
    except FileNotFoundError:
        logger.exception("The `gh` cli is not installed, see https://cli.github.com")
        raise SystemExit(1) from None

    if result.returncode != 0:
        logger.debug("gh %s failed: %s", " ".join(args), result.stderr.strip())
        return ""

    return result.stdout


def _gh_json(*args: str) -> list[dict]:
    """Run a `gh api --jq` call that emits one json object per line."""
    return [json.loads(line) for line in _gh(*args).splitlines() if line.strip()]


def current_user() -> str:
    """The login of the authenticated `gh` user."""
    return _gh("api", "/user", "--jq", ".login").strip()


def list_repos(user: str) -> list[dict]:
    """Every public repo owned by a user, most recently pushed first."""
    return _gh_json(
        "api", "--paginate", "--jq", ".[]", f"/users/{quote(user)}/repos?per_page=100&type=owner&sort=pushed"
    )


def ci_workflows(full_name: str) -> list[dict]:
    """Active workflows defined in the repo, minus GitHub's own dynamic pseudo-workflows."""
    workflows = _gh_json("api", f"/repos/{full_name}/actions/workflows", "--jq", ".workflows[]")
    return [w for w in workflows if w["state"] == "active" and w["path"].startswith(WORKFLOW_DIR)]


def fetch_readme(full_name: str) -> str:
    """The raw README of a repo, or an empty string if it hasn't got one."""
    return _gh("api", f"/repos/{full_name}/readme", "-H", "Accept: application/vnd.github.raw")


def extract_badges(markdown: str) -> list[Badge]:
    """Pull the badges out of a README, in the order they appear."""
    badges: list[Badge] = []
    seen: set[str] = set()

    for alt, image, link in BADGE_RE.findall(markdown):
        # Relative image paths can't be resolved without knowing the branch and they're never badges anyway.
        if not image.startswith("http") or image in seen:
            continue
        if not any(hint in image.lower() for hint in BADGE_URL_HINTS):
            continue
        seen.add(image)
        badges.append(Badge(alt, image, link))

    return badges[:MAX_BADGES]


def workflow_badges(full_name: str, default_branch: str, workflows: list[dict]) -> list[Badge]:
    """GitHub's own status badges, for repos whose README hasn't got any."""
    branch = quote(default_branch)
    badges = []

    for workflow in workflows:
        file_name = quote(Path(workflow["path"]).name)
        url = f"https://github.com/{full_name}/actions/workflows/{file_name}"
        badges.append(Badge(workflow["name"], f"{url}/badge.svg?branch={branch}", f"{url}?query=branch%3A{branch}"))

    return badges[:MAX_BADGES]


def first_paragraph(markdown: str) -> str:
    """The README's intro line, as a fallback for a repo with no description.

    Only the intro counts, prose under a subheading is install instructions, not a description of the repo.
    """
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("##"):
            break
        if line and not line.startswith(MARKUP_PREFIXES):
            return textwrap.shorten(line, MAX_DESCRIPTION_LEN, placeholder="…")

    return ""


def build_repo(repo: dict) -> Repo | None:
    """Gather everything the page needs for one repo, or None if it hasn't got CI."""
    full_name = repo["full_name"]
    workflows = ci_workflows(full_name)
    if not workflows:
        logger.debug("Skipping %s, no workflows", full_name)
        return None

    readme = fetch_readme(full_name)
    logger.info("Including %s", full_name)

    return Repo(
        name=repo["name"],
        url=repo["html_url"],
        description=repo["description"] or first_paragraph(readme),
        badges=extract_badges(readme) or workflow_badges(full_name, repo["default_branch"], workflows),
    )


CSS = """
:root { color-scheme: light dark; --bg: #f6f7f9; --card: #fff; --fg: #1c2024; --muted: #5b6570; --line: #dfe3e8; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #14161a; --card: #1c1f24; --fg: #e6e9ed; --muted: #98a2ae; --line: #2c3138; }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2rem 1rem; background: var(--bg); color: var(--fg);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
}
header, footer { max-width: 60rem; margin: 0 auto; }
header h1 { margin: 0 0 .25rem; font-size: 1.6rem; }
header p, footer { color: var(--muted); font-size: .85rem; }
footer { margin-top: 2rem; }
a { color: inherit; }
main {
  max-width: 60rem; margin: 1.5rem auto 0; display: grid; gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr));
}
article { background: var(--card); border: 1px solid var(--line); border-radius: .6rem; padding: 1rem; }
article h2 { margin: 0; font-size: 1.05rem; }
article h2 a { text-decoration: none; }
article h2 a:hover { text-decoration: underline; }
article p { margin: .4rem 0 0; color: var(--muted); font-size: .9rem; }
.badges { margin-top: .75rem; display: flex; flex-wrap: wrap; gap: .3rem; }
.badges img { height: 20px; display: block; }
"""


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _render_badge(badge: Badge) -> str:
    img = f'<img src="{_esc(badge.image)}" alt="{_esc(badge.alt)}" loading="lazy">'
    return f'<a href="{_esc(badge.link)}">{img}</a>' if badge.link else img


def _render_repo(repo: Repo) -> str:
    badges = "".join(_render_badge(badge) for badge in repo.badges)
    description = f"<p>{_esc(repo.description)}</p>" if repo.description else ""
    return (
        f'<article><h2><a href="{_esc(repo.url)}">{_esc(repo.name)}</a></h2>'
        f'{description}<div class="badges">{badges}</div></article>'
    )


def render(repos: list[Repo], user: str) -> str:
    """Render the whole page."""
    generated = datetime.now(tz=OUR_TIMEZONE).strftime("%Y-%m-%d %H:%M %Z")
    title = f"{user}'s repos"

    return "\n".join(
        [
            '<!DOCTYPE html>\n<html lang="en">\n<head>',
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_esc(title)}</title>",
            f"<style>{CSS}</style>",
            "</head>\n<body>",
            f"<header><h1>{_esc(title)}</h1><p>{len(repos)} repos with CI, updated {_esc(generated)}</p></header>",
            "<main>",
            *[_render_repo(repo) for repo in repos],
            "</main>",
            f'<footer>Generated by <a href="{PROGRAM_REPO_URL}">repo-dashboard</a></footer>',
            "</body>\n</html>",
        ]
    )


def build(user: str, output: Path) -> int:
    """Write the landing page for a user's repos, returning how many repos made it onto the page."""
    # ponytail: forks and archived repos have CI runs but nobody wants them on a landing page.
    candidates = [r for r in list_repos(user) if not r["fork"] and not r["archived"]]
    logger.info("Checking %d repos for CI", len(candidates))

    with ThreadPoolExecutor(max_workers=API_WORKERS) as pool:
        repos = [repo for repo in pool.map(build_repo, candidates) if repo]

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(repos, user), encoding="utf-8")

    return len(repos)
