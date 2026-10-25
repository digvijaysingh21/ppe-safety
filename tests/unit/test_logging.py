import json

import pytest

from ppe.core.logging import configure_logging, get_logger


def test_json_logs_contain_event_and_bound_fields(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="INFO", json_logs=True)
    get_logger("test").info("camera_connected", camera_id="cam-1")
    record = json.loads(capsys.readouterr().out.strip())
    assert record["event"] == "camera_connected"
    assert record["camera_id"] == "cam-1"
    assert record["level"] == "info"
    assert "timestamp" in record


def test_messages_below_the_level_are_dropped(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="WARNING", json_logs=True)
    get_logger("test").info("too_quiet")
    assert capsys.readouterr().out == ""
