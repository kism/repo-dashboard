"""Tests for the page builder, the `gh` cli is faked so nothing hits the network."""

import re
import subprocess  # ruff: ignore[suspicious-subprocess-import] we fake the `gh` cli calls
from datetime import UTC, datetime, timedelta

import pytest

from repo_dashboard import dashboard

README = """# my-repo

[![Test](https://github.com/kism/my-repo/actions/workflows/test.yml/badge.svg)](https://github.com/kism/my-repo/actions/workflows/test.yml)
![codecov](https://codecov.io/gh/kism/my-repo/graph/badge.svg?token=abc)
![screenshot](https://example.com/screenshot.png)
![logo](docs/logo.png)

A cool thing that does cool stuff.
"""

WORKFLOWS = [
    {"name": "Test", "path": ".github/workflows/test.yml", "state": "active"},
    {"name": "Dependabot Updates", "path": "dynamic/dependabot/dependabot-updates", "state": "active"},
    {"name": "Old", "path": ".github/workflows/old.yml", "state": "disabled_manually"},
]


def fake_run(stdout: str = "", returncode: int = 0):
    """Stand in for subprocess.run, CompletedProcess is the stdlib's own result object."""
    return lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, returncode, stdout, "it broke")


def test_gh_returns_stdout(monkeypatch) -> None:
    monkeypatch.setattr(subprocess, "run", fake_run("kism\n"))
    assert dashboard._gh("api", "/user") == "kism\n"

    monkeypatch.setattr(subprocess, "run", fake_run("kism\n", returncode=1))
    assert not dashboard._gh("api", "/user"), "A failed call just means the repo gets skipped"


def test_gh_without_the_cli_installed(monkeypatch) -> None:
    def no_gh(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", no_gh)

    with pytest.raises(SystemExit):
        dashboard._gh("api", "/user")


def test_gh_json_parses_a_line_per_object(monkeypatch) -> None:
    monkeypatch.setattr(subprocess, "run", fake_run('{"a": 1}\n\n{"a": 2}\n'))

    assert dashboard._gh_json("api", "/x") == [{"a": 1}, {"a": 2}], "Blank lines are skipped"


def test_the_api_endpoints(monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(dashboard, "_gh", lambda *args: (calls.append(args), "{}")[1])

    dashboard.current_user()
    dashboard.list_repos("a user")
    dashboard.fetch_readme("kism/my-repo")

    assert "/user" in calls[0]
    assert "/users/a%20user/repos?per_page=100&type=owner&sort=pushed" in calls[1], "The user is url quoted"
    assert "/repos/kism/my-repo/readme" in calls[2]


def test_ci_workflows_only_keeps_real_active_ones(monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "_gh_json", lambda *args: WORKFLOWS)

    assert [w["name"] for w in dashboard.ci_workflows("kism/my-repo")] == ["Test"]


def test_extract_badges_keeps_only_badges() -> None:
    badges = dashboard.extract_badges(README)

    assert [badge.alt for badge in badges] == ["Test", "codecov"]
    assert badges[0].link == "https://github.com/kism/my-repo/actions/workflows/test.yml"
    assert not badges[1].link, "A badge that isn't wrapped in a link has no link"


def test_extract_badges_no_readme() -> None:
    assert dashboard.extract_badges("") == []


def test_first_paragraph_skips_markup() -> None:
    assert dashboard.first_paragraph(README) == "A cool thing that does cool stuff."
    assert not dashboard.first_paragraph("# Only a heading\n")
    assert not dashboard.first_paragraph("# Title\n\n## Install\n\nRun the installer.\n"), "Intro prose only"


def test_workflow_badges_point_at_the_default_branch() -> None:
    badges = dashboard.workflow_badges("kism/my-repo", "trunk", WORKFLOWS[:1])

    assert len(badges) == 1
    expected = "https://github.com/kism/my-repo/actions/workflows/test.yml/badge.svg?branch=trunk"
    assert badges[0].image == expected
    assert "branch%3Atrunk" in badges[0].link


def test_last_push_badge_colour(monkeypatch) -> None:
    def at(days_ago: int) -> dashboard.Badge:
        pushed = datetime.now(tz=UTC) - timedelta(days=days_ago)
        monkeypatch.setattr(dashboard, "_gh", lambda *args: pushed.isoformat())
        badge = dashboard.last_push_badge("kism/my-repo", "main")
        assert badge is not None
        return badge

    assert at(1).image.endswith("brightgreen")
    assert at(200).image.endswith("orange")
    assert at(365 * 3).image.endswith("red")
    assert "last%20push-" in at(1).image
    assert at(1).link == "https://github.com/kism/my-repo/commits/main"

    monkeypatch.setattr(dashboard, "_gh", lambda *args: "")
    assert dashboard.last_push_badge("kism/my-repo", "main") is None, "A failed call just drops the badge"


def test_build_repo_uses_readme_badges(monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "ci_workflows", lambda _: WORKFLOWS[:1])
    monkeypatch.setattr(dashboard, "fetch_readme", lambda _: README)
    monkeypatch.setattr(dashboard, "last_push_badge", lambda *args: dashboard.Badge("last push 2026-01-01", "i", "l"))

    repo = dashboard.build_repo(
        {"name": "my-repo", "full_name": "kism/my-repo", "html_url": "u", "description": None, "default_branch": "main"}
    )

    assert repo is not None
    assert repo.description == "A cool thing that does cool stuff.", "Falls back to the README"
    assert [badge.alt for badge in repo.badges] == ["last push 2026-01-01", "Test", "codecov"], "Push badge first"


def test_build_repo_without_ci_is_skipped(monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "ci_workflows", lambda _: [])

    assert dashboard.build_repo({"full_name": "kism/no-ci"}) is None


def test_build_writes_the_page(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        dashboard,
        "list_repos",
        lambda _: [
            {"full_name": "kism/my-repo", "fork": False, "archived": False},
            {"full_name": "kism/a-fork", "fork": True, "archived": False},
            {"full_name": "kism/old", "fork": False, "archived": True},
        ],
    )
    monkeypatch.setattr(dashboard, "build_repo", lambda repo: dashboard.Repo(repo["full_name"], "https://example.com"))

    output = tmp_path / "site" / "index.html"
    assert dashboard.build("kism", output) == 1, "Forks and archived repos don't make the page"

    page = output.read_text()
    assert "kism/my-repo" in page
    assert "a-fork" not in page


def test_render_escapes_html() -> None:
    page = dashboard.render([dashboard.Repo("<script>", "https://example.com", "a & b")], "kism")

    assert "<script>" not in page
    assert "a &amp; b" in page


def test_render_badge_only_links_when_there_is_a_link() -> None:
    badges = [
        dashboard.Badge("Linked", "https://example.com/a.svg", "https://example.com"),
        dashboard.Badge("Bare", "https://example.com/b.svg"),
    ]
    page = dashboard.render([dashboard.Repo("my-repo", "https://example.com", badges=badges)], "kism")

    assert re.search(r'<a href="https://example.com">\s*<img src="https://example.com/a.svg"[^>]*>\s*</a>', page)
    assert re.search(r'</a>\s*<img src="https://example.com/b.svg"[^>]*>\s*</div>', page), "Bare badge isn't wrapped"


def test_render_description_handles_inline_markdown() -> None:
    rendered = dashboard._render_description("Run `uv sync`, see the [docs](https://example.com/d) & go")

    assert rendered == 'Run <code>uv sync</code>, see the <a href="https://example.com/d">docs</a> &amp; go'


def test_render_description_ignores_dodgy_markdown() -> None:
    assert dashboard._render_description("![badge](https://img.example/b.svg) A thing") == "A thing"
    assert dashboard._render_description("[click](javascript:alert(1))") == "[click](javascript:alert(1))"
