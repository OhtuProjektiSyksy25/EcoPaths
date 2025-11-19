# pylint: disable=no-member
"""
Logger module.
Provides a structured logging interface for the application.
"""
import logging


class AppLogger:
    """
    Application Logger with structured logging capabilities.
    """

    def __init__(self):
        self._logger = logging.getLogger("app")

    def _log(self, level, event, **data):
        """
        Internal method to log events with extra data.
        Args:
            level (_type_): _logging level_
            event (_type_): _event name_
            data (_type_): _additional data_
        """
        self._logger.log(
            level,
            event,
            extra={"extra_data": data},
            stacklevel=3
        )

    def debug(self, event, **data):
        """
        Log a debug event.
        Args:
            event (_type_): _event name_
            data (_type_): _additional data_
        """
        self._log(logging.DEBUG, event, **data)

    def info(self, event, **data):
        """
        Log a info event.
        Args:
            event (_type_): _event name_
            data (_type_): _additional data_
        """
        self._log(logging.INFO, event, **data)

    def warning(self, event, **data):
        """
        Log a warning event.
        Args:
            event (_type_): _event name_
            data (_type_): _additional data_
        """
        self._log(logging.WARNING, event, **data)

    def error(self, event, **data):
        """
        Log a error event.
        Args:
            event (_type_): _event name_
            data (_type_): _additional data_
        """
        self._log(logging.ERROR, event, **data)

    def critical(self, event, **data):
        """
        Log a critical event.
        Args:
            event (_type_): _event name_
            data (_type_): _additional data_
        """
        self._log(logging.CRITICAL, event, **data)


class ExcludeHttpxFilter(logging.Filter):
    """
    Logging filter to exclude httpx and httpcore logs.
    """

    def filter(self, record):
        """
        Filter out httpx and httpcore log records.
        Args:
            record (_type_): _log record_
        Returns:
            bool: True if record should be logged, False otherwise.
        """
        return not (
            record.name.startswith("httpx")
            or record.name.startswith("httpcore")
        )


log = AppLogger()
