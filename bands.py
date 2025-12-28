from typing import Dict, Optional


BAND_LABEL_MAP: Dict[str, str] = {
    "2400": "2.4 GHz",
    "5000": "5 GHz",
    "6000": "6 GHz",
    "unknown": "WLAN (?)",
}

BAND_ORDER_MAP: Dict[str, int] = {
    "2.4 GHz": 0,
    "5 GHz": 1,
    "6 GHz": 2,
    "WLAN (?)": 3,
    "LAN": 4,
    "-": 9,
}


def _norm_key(s: str) -> str:
    return s.lower().replace("_", "").replace("-", "").replace(" ", "")


def _extract_frequency_band(info: Dict) -> Optional[str]:
    """
    Sucht in einem GetInfo()-Dict nach X_AVM-DE_FrequencyBand (oder äquivalentem Key).
    TR-064 WLANConfiguration: NewX_AVM-DE_FrequencyBand liefert z.B. 2400/5000/6000/unknown.
    """
    for k, v in info.items():
        nk = _norm_key(str(k))
        if "frequencyband" in nk:
            return None if v is None else str(v).strip()
    return None


def _band_label(freq_band: Optional[str]) -> str:
    if not freq_band:
        return "-"
    fb = freq_band.strip().lower()
    return BAND_LABEL_MAP.get(fb, f"WLAN ({freq_band})")


def _band_order(label: str) -> int:
    base = label.split("+", 1)[0].strip()
    return BAND_ORDER_MAP.get(base, 8)
