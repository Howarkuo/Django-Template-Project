import json
import logging


class JsonFormatter(logging.Formatter):
    """Json formatter for loggin system."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats a logging record into a JSON string.

        Args:
        record (logging.LogRecord): The log record to format.

        Returns:
        str: A JSON-formatted string representation of the log record.
        """
        log_record = {
            "asctime": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "ip": getattr(record, "ip", "Unknown"),
            "path": getattr(record, "path", ""),
            "response_time": getattr(record, "response_time", ""),
        }
        return json.dumps(log_record)
