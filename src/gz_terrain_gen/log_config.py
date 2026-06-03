import sys

from loguru import logger

LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level:<7} | {name}:{line} | {message}"
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


def configure_logging(level: str) -> None:
    normalized_level = level.upper()
    if normalized_level not in LOG_LEVELS:
        raise ValueError(f"log level must be one of: {', '.join(LOG_LEVELS)}")

    logger.remove()
    logger.add(sys.stderr, level=normalized_level, format=LOG_FORMAT)
