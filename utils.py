from typing import Any


def fmt(val: Any, fallback: str = "-") -> str:
    if val is None:
        return fallback
    s = str(val).strip()
    return s if s else fallback
