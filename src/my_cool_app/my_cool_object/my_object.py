"""Demo object."""

from repo_dashboard.utils.logger import get_logger

logger = get_logger(__name__)


# KISM-BOILERPLATE: Demo object, doesn't do much
class MyCoolObject:
    """Demo object."""

    def __init__(self, message: str) -> None:
        """Init config for the NGINX Allowlist Writer."""
        # Monitor Writing
        logger.debug("Creating MyCoolObject")
        self._my_message = message

    def get_message(self) -> str:
        """Return the message."""
        logger.trace("Getting message")
        return self._my_message
