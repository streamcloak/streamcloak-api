import logging
import sys

from app.core.config import get_settings

settings = get_settings()

LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []

    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO if settings.ENVIRONMENT == "prod" else logging.DEBUG)
    return logger


logger = logging.getLogger("app")
