import pytest

from gz_terrain_gen.log_config import LOG_FORMAT, configure_logging


def test_log_format_includes_module_name_and_line_number() -> None:
    assert "{name}" in LOG_FORMAT
    assert "{line}" in LOG_FORMAT


def test_configure_logging_accepts_valid_level() -> None:
    configure_logging("INFO")


def test_configure_logging_rejects_invalid_level() -> None:
    with pytest.raises(ValueError):
        configure_logging("LOUD")
