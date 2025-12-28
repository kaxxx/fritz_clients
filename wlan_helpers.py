import itertools
from typing import Dict, Tuple, Set, Any

from bands import _extract_frequency_band, _band_label, _band_order


def get_wlan_bands_by_mac(fw: Any) -> Dict[str, str]:
    """
    Liefert Mapping mac(lowercase) -> Bandlabel (z.B. "2.4 GHz" oder "2.4 GHz+5 GHz" bei Multi-Link/Mehrfachzuordnung).
    Iteriert dazu über WLANConfiguration1..N, bis die Box keinen Service mehr anbietet.

    Hinweis: Import der fritzconnection-Ausnahme erfolgt zur Laufzeit, um harte Modulabhängigkeit
    beim Import dieser Hilfsfunktion zu vermeiden.
    """
    # Lazy-Import, um ImportError außerhalb des CLI-Entry-Points zu vermeiden
    try:
        from fritzconnection.core.exceptions import FritzServiceError  # type: ignore
    except ImportError:  # pragma: no cover - im regulären CLI-Aufruf vorhanden
        # Schlanker Fallback-Typ, falls fritzconnection nicht installiert ist
        class FritzServiceError(Exception):
            pass

    bands_by_mac: Dict[str, Set[str]] = {}

    for n in itertools.count(1):
        fw.service = n
        try:
            info = fw.get_info()
            band = _band_label(_extract_frequency_band(info))
            wlan_hosts = fw.get_hosts_info()  # keys: service,index,status,mac,ip,signal,speed
        except FritzServiceError:
            break

        for entry in wlan_hosts:
            if not entry.get("status"):
                continue  # nur aktive WLAN-Clients
            # Logik-Normalisierung ohne Anzeige-Fallback
            mac_raw = entry.get("mac")
            mac = str(mac_raw).strip().lower() if mac_raw else ""
            if not mac:
                continue
            bands_by_mac.setdefault(mac, set()).add(band)

    # sets -> string (stabil sortiert)
    def sort_key(lbl: str) -> Tuple[int, str]:
        return (_band_order(lbl), lbl)

    out: Dict[str, str] = {}
    for mac, bands in bands_by_mac.items():
        out[mac] = "+".join(sorted(bands, key=sort_key))
    return out
