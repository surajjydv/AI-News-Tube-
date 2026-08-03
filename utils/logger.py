import logging
from logging.handlers import RotatingFileHandler
import sys
import io
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "app.log"


def setup_logger(name: str = "AI-NewsTube", level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with both console and file handlers, ensuring UTF-8 encoding support on Windows.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if logger is called multiple times
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler with UTF-8 stream handling for Windows compatibility
    try:
        if sys.platform == "win32":
            utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            console_handler = logging.StreamHandler(utf8_stdout)
        else:
            console_handler = logging.StreamHandler(sys.stdout)
    except Exception:
        console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file handler at {LOG_FILE}: {e}")

    return logger


# Default application logger instance
logger = setup_logger()
