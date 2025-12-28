from typing import Any


def format_value(val: Any, fallback: str = "-") -> str:
    """
    Anzeige-/Output-Helfer:
    - Konvertiert val zu String und trimmt Whitespace.
    - None oder leerer String -> fallback (Standard: "-").

    Wichtig: Nur für Darstellung verwenden. Nicht in Geschäftslogik nutzen,
    damit Anzeige-Fallbacks (z.B. "-") keine Logikzweige beeinflussen.
    """
    if val is None:
        return fallback
    s = str(val).strip()
    return s if s else fallback
