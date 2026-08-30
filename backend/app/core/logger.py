import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }
        
        # Capture extra fields if passed
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
            
        # Capture exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    """
    Configures the root logger.
    
    Args:
        level: The minimum logging level (e.g. INFO, DEBUG).
        json_format: If True, output logs in structured JSON format.
    """
    root_logger = logging.getLogger()
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Determine the log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Configure handler
    handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        formatter = JSONFormatter()
    else:
        # Standard clean human-readable log format for development
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Set levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

# Global helper for adding extra context to structured logs
class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def info(self, msg: str, extra: Dict[str, Any] = None) -> None:
        self.logger.info(msg, extra={"extra_fields": extra} if extra else None)
        
    def error(self, msg: str, extra: Dict[str, Any] = None, exc_info: Any = None) -> None:
        self.logger.error(msg, extra={"extra_fields": extra} if extra else None, exc_info=exc_info)
        
    def warning(self, msg: str, extra: Dict[str, Any] = None) -> None:
        self.logger.warning(msg, extra={"extra_fields": extra} if extra else None)
        
    def debug(self, msg: str, extra: Dict[str, Any] = None) -> None:
        self.logger.debug(msg, extra={"extra_fields": extra} if extra else None)

def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)
