"""Simple logging setup — prints to stderr with levels."""

import sys
from datetime import datetime


LEVELS = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}
_LEVEL = "INFO"


def set_level(level: str):
    global _LEVEL
    level = level.upper()
    if level in LEVELS:
        _LEVEL = level


def _fmt(level: str, msg: str, **extra):
    ts = datetime.now().strftime("%H:%M:%S")
    extra_str = f" | {extra}" if extra else ""
    return f"[{ts}] [{level}] {msg}{extra_str}"


def debug(msg: str, **extra):
    if LEVELS.get(_LEVEL, 0) <= LEVELS["DEBUG"]:
        print(_fmt("DEBUG", msg, **extra), file=sys.stderr)


def info(msg: str, **extra):
    if LEVELS.get(_LEVEL, 0) <= LEVELS["INFO"]:
        print(_fmt("INFO", msg, **extra), file=sys.stderr)


def warn(msg: str, **extra):
    if LEVELS.get(_LEVEL, 0) <= LEVELS["WARN"]:
        print(_fmt("WARN", msg, **extra), file=sys.stderr)


def error(msg: str, **extra):
    if LEVELS.get(_LEVEL, 0) <= LEVELS["ERROR"]:
        print(_fmt("ERROR", msg, **extra), file=sys.stderr)
