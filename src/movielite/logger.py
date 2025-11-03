import logging
import sys

_logger = None

def get_logger():
    global _logger
    if _logger is None:
        _logger = logging.getLogger("movielite")
        _logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        _logger.addHandler(handler)

    return _logger

def set_log_level(level: int):
    """Set logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING)"""
    get_logger().setLevel(level)
