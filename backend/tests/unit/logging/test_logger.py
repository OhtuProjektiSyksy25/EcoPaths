
import json
import logging
from src.logging.logger import AppLogger, ExcludeHttpxFilter
from src.logging.formatters import JSONFormatter


def test_json_formatter_outputs_valid_json():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="app",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.extra_data = {"foo": "bar"}

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["message"] == "Test message"
    assert parsed["foo"] == "bar"
    assert parsed["level"] == "INFO"


def test_app_logger_injects_extra_data(caplog):
    log = AppLogger()

    with caplog.at_level("INFO"):
        log.info("Event occurred", user_id=123)

    record = caplog.records[0]
    assert hasattr(record, "extra_data")
    assert record.extra_data["user_id"] == 123


def test_httpx_filter_blocks_httpx_logs():
    f = ExcludeHttpxFilter()
    httpx_record = logging.LogRecord("httpx", 20, "", 0, "msg", None, None)
    normal_record = logging.LogRecord("other", 20, "", 0, "msg", None, None)

    assert f.filter(httpx_record) is False
    assert f.filter(normal_record) is True
