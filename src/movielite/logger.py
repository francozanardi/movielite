import logging

_LOGGER_NAME = "pycaps"
_logger = None

class CustomFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(datefmt="%H:%M:%S")
        self.info_fmt = "[%(asctime)s] %(message)s"
        self.default_fmt = "[%(asctime)s] [%(levelname)s] %(message)s"

    def format(self, record):
        if record.levelno == logging.INFO:
            self._style._fmt = self.info_fmt
        else:
            self._style._fmt = self.default_fmt
        return super().format(record)

def setup_logger(level: int | str = logging.INFO) -> logging.Logger:
    global _logger

    if _logger is None:
        _logger = logging.getLogger(_LOGGER_NAME)
        handler = logging.StreamHandler()
        formatter = CustomFormatter()
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
        _logger.setLevel(level)
        _logger.propagate = False

    else:
        _logger.setLevel(level)

def logger() -> logging.Logger:
    global _logger
    if _logger is None:
        setup_logger(level=logging.INFO)
    return _logger

def set_logging_level(level: int | str) -> None:
    logger().setLevel(level)

class ProcessLogger:
    def __init__(self, total_steps):
        self._current_step = 1
        self._total_steps = total_steps

    def step(self, msg: str) -> None:
        logger().info(f"[{self._current_step}/{self._total_steps}] {msg}")
        self._current_step += 1
