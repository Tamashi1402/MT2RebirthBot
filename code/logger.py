# ============================================================
# MT2 REBIRTH BOT - LOGGER
# Console: coloured INFO/WARN/ERROR
# File:    logs/logs-YYYY-MM-DD.txt (single daily full DEBUG log)
# ============================================================
import logging
import os
import re
import sys
from typing import Any
from config import LOGS_FILE, LOG_LEVEL_CONSOLE

# -- ANSI color codes ---------------------------------------------------------
_RESET = "\033[0m"
_WHITE = "\033[97m"
_ORANGE = "\033[38;5;208m"
_RED = "\033[91m"
_GREEN = "\033[92m"

# Enable ANSI on Windows 10+ console
try:
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
except Exception:
    pass


def _repair_mojibake(value: Any) -> str:
    text = str(value)
    if not text:
        return text
    # Fast path for normal strings.
    if not any(marker in text for marker in ("Ã", "Â", "â", "\ufffd")):
        return text
    # Typical UTF-8 bytes decoded as cp1252/latin-1.
    try:
        repaired = text.encode("latin-1", "strict").decode("utf-8", "strict")
        if repaired and repaired != text and "\ufffd" not in repaired:
            text = repaired
    except Exception:
        pass
    # Common leftovers that still appear in mixed strings.
    replacements = {
        "â€”": "-",
        "â€“": "-",
        "â€¦": "...",
        "â€˜": "'",
        "â€™": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "Â": "",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


class _ColourFormatter(logging.Formatter):
    _LEVEL_COLOUR = {
        logging.DEBUG: _WHITE,
        logging.INFO: _WHITE,
        logging.WARNING: _ORANGE,
        logging.ERROR: _RED,
        logging.CRITICAL: _RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        colour = self._LEVEL_COLOUR.get(record.levelno, _WHITE)
        msg = _repair_mojibake(record.getMessage())
        return f"{colour}{msg}{_RESET}"


class _DevFileFormatter(logging.Formatter):
    """Full debug formatter (former dev log style), ANSI-stripped."""

    _ANSI_RE = re.compile(r"\033\[[0-9;]*m")

    def format(self, record: logging.LogRecord) -> str:
        msg = self._ANSI_RE.sub("", _repair_mojibake(record.getMessage()))
        ts = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(7)
        return f"{ts}  {level}  {msg}"


_fmt_file = _DevFileFormatter()


def get_logger(name: str = "MT2Bot") -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log

    log.setLevel(logging.DEBUG)

    # Ensure /logs exists before opening the daily log file.
    try:
        os.makedirs(os.path.dirname(LOGS_FILE), exist_ok=True)
    except Exception:
        pass

    # Single daily file log. Default is INFO to avoid huge daily logs; switch
    # LOG_LEVEL_FILE to DEBUG in config.json when actively diagnosing.
    fh = logging.FileHandler(LOGS_FILE, encoding="utf-8")
    fh.setLevel(getattr(logging, str(getattr(sys.modules.get("config"), "LOG_LEVEL_FILE", "INFO")).upper(), logging.INFO))
    fh.setFormatter(_fmt_file)
    log.addHandler(fh)

    # Console output remains colorized and level-filtered.
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(getattr(logging, LOG_LEVEL_CONSOLE, logging.INFO))
    ch.setFormatter(_ColourFormatter())
    log.addHandler(ch)

    return log


_last_change: dict[str, str] = {}
_last_every: dict[str, float] = {}


def debug_on_change(key: str, msg: str) -> None:
    """DEBUG once when the message for `key` actually changes."""
    prev = _last_change.get(key)
    if prev == msg:
        return
    _last_change[key] = msg
    get_logger().debug(msg)


def debug_every(key: str, seconds: float, msg: str, *, also_on_change: bool = True) -> None:
    """DEBUG at most every `seconds`, and immediately if the text changed."""
    import time
    now = time.time()
    prev = _last_change.get(key)
    last = _last_every.get(key, 0.0)
    changed = also_on_change and prev != msg
    if not changed and (now - last) < max(0.05, float(seconds)):
        return
    _last_change[key] = msg
    _last_every[key] = now
    get_logger().debug(msg)


def cprint(msg: str, level: str = "info"):
    """Log a colored line to console and file without double-printing."""
    clean_msg = _repair_mojibake(msg)
    _log = logging.getLogger("MT2Bot")
    lvl_map = {"info": logging.INFO, "ok": logging.INFO, "warn": logging.WARNING, "error": logging.ERROR, "err": logging.ERROR, "green": logging.INFO}
    if not _log.handlers:
        print(clean_msg, flush=True)
        return
    _log.log(lvl_map.get(level, logging.INFO), clean_msg)
