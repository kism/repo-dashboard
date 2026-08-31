"""Main Entrypoint."""

import argparse
from pathlib import Path

from rich import traceback

from . import dashboard
from .constants import PROGRAM_NAME, PROGRAM_NAME_WITH_VERSION
from .utils.logger import get_logger, setup_logger_cli

traceback.install(extra_lines=2)
logger = get_logger(__name__)

DEFAULT_OUTPUT = Path("site/index.html")


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description=PROGRAM_NAME_WITH_VERSION)
    parser.add_argument(
        "--user",
        action="store",
        type=str,
        default="",
        help="The GitHub user to list repos for, defaults to the authenticated `gh` user.",
    )
    parser.add_argument(
        "--output",
        action="store",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where to write the page, defaults to '{DEFAULT_OUTPUT}'.",
    )
    parser.add_argument(
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times).",
    )
    return parser.parse_args()


def main() -> None:
    """Main Entrypoint."""
    args = _get_args()
    setup_logger_cli(args.v)
    logger.info("%s", PROGRAM_NAME_WITH_VERSION)

    user = args.user or dashboard.current_user()
    if not user:
        logger.error("Could not work out the GitHub user, run `gh auth login` or pass --user")
        raise SystemExit(1)

    count = dashboard.build(user, args.output)
    logger.info("Wrote %d repos to %s", count, args.output)


if __name__ == "__main__":
    main()  # pragma: no cover
