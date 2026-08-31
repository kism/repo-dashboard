"""Tests for the page builder, all against the pure functions so nothing hits the network."""

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
]


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


def test_build_repo_uses_readme_badges(monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "ci_workflows", lambda _: WORKFLOWS[:1])
    monkeypatch.setattr(dashboard, "fetch_readme", lambda _: README)

    repo = dashboard.build_repo(
        {"name": "my-repo", "full_name": "kism/my-repo", "html_url": "u", "description": None, "default_branch": "main"}
    )

    assert repo is not None
    assert repo.description == "A cool thing that does cool stuff.", "Falls back to the README"
    assert [badge.alt for badge in repo.badges] == ["Test", "codecov"]


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
