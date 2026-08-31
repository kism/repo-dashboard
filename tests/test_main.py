import argparse
import logging
from pathlib import Path

import pytest

from repo_dashboard import __main__, dashboard


def test_main(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    caplog.set_level(logging.INFO)

    output = tmp_path / "index.html"
    mock_args = argparse.Namespace(v=0, user="kism", output=output)
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: mock_args)
    monkeypatch.setattr(dashboard, "build", lambda user, out: 3)

    __main__.main()

    assert "repo-dashboard v0.0.1" in caplog.text
    assert "Wrote 3 repos" in caplog.text


def test_main_without_a_user(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_args = argparse.Namespace(v=0, user="", output=Path("site/index.html"))
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: mock_args)
    monkeypatch.setattr(dashboard, "current_user", lambda: "")

    with pytest.raises(SystemExit):
        __main__.main()

    assert "Could not work out the GitHub user" in caplog.text
