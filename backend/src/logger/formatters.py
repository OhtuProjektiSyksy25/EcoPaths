# pylint: disable=no-member
"""
Custom JSON formatter for logging.
Returns:
    log records in JSON format.
"""
import json
import logging
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for logging.

    Args:
        logging (_type_): _logging_ module
    """

    def format(self, record):
        """
        Format the log record as JSON.
        Args:
            record (_type_): _log record_

        Returns:
            _type_: _json string_
        """
        log = {
            "level": record.levelname,
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "logger": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data") and record.extra_data:
            log.update(record.extra_data)

        return json.dumps(log)
