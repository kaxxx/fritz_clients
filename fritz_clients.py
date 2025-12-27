#!/usr/bin/env python3
import os
import sys
import argparse
import itertools
from typing import List, Dict, Optional, Tuple

try:
    from fritzconnection import FritzConnection
    from fritzconnection.core.exceptions import FritzServiceError
    from fritzconnection.lib.fritzhosts import FritzHosts
    from fritzconnection.lib.fritzwlan import FritzWLAN
except ImportError:
    print("Fehlt: fritzconnection. Installiere z.B. mit: pip install fritzconnection==1.15.0", file=sys.stderr)
    sys.exit(2)


def fmt(val: object, fallback: str = "-") -> str:
    if val is None:
        return fallback
    s = str(val).strip()
    return s if s else fallback


def _norm_key(s: str) -> str:
    return s.lower().replace("_", "").replace("-", "").replace(" ", "")


def _extract_frequency_band(info: Dict) -> Optional[str]:
    """
    Sucht in einem GetInfo()-Dict nach X_AVM-DE_FrequencyBand (oder äquivalentem Key).
    TR-064 WLANConfiguration: NewX_AVM-DE_FrequencyBand liefert z.B. 2400/5000/6000/unknown. :contentReference[oaicite:1]{index=1}
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
    if fb == "2400":
        return "2.4 GHz"
    if fb == "5000":
        return "5 GHz"
    if fb == "6000":
        return "6 GHz"
    if fb == "unknown":
        return "WLAN (?)"
    # fallback: irgendwas anzeigen, was die Box liefert
    return f"WLAN ({freq_band})"


def _band_order(label: str) -> int:
    # Sortierreihenfolge (anpassbar)
    base = label.split("+", 1)[0].strip()
    order = {
        "2.4 GHz": 0,
        "5 GHz": 1,
        "6 GHz": 2,
        "WLAN (?)": 3,
        "LAN": 4,
        "-": 9,
    }
    return order.get(base, 8)


def get_wlan_bands_by_mac(fw: FritzWLAN) -> Dict[str, str]:
    """
    Liefert Mapping mac(lowercase) -> Bandlabel (z.B. "2.4 GHz" oder "2.4 GHz+5 GHz" bei Multi-Link/Mehrfachzuordnung).
    Iteriert dazu über WLANConfiguration1..N, bis die Box keinen Service mehr anbietet. :contentReference[oaicite:2]{index=2}
    """
    bands_by_mac: Dict[str, set] = {}

    for n in itertools.count(1):
        fw.service = n
        try:
            info = fw.get_info()
            band = _band_label(_extract_frequency_band(info))
            wlan_hosts = fw.get_hosts_info()  # keys: service,index,status,mac,ip,signal,speed :contentReference[oaicite:3]{index=3}
        except FritzServiceError:
            break

        for entry in wlan_hosts:
            if not entry.get("status"):
                continue  # nur aktive WLAN-Clients
            mac = fmt(entry.get("mac")).lower()
            if mac == "-":
                continue
            bands_by_mac.setdefault(mac, set()).add(band)

    # sets -> string (stabil sortiert)
    def sort_key(lbl: str) -> Tuple[int, str]:
        return (_band_order(lbl), lbl)

    out: Dict[str, str] = {}
    for mac, bands in bands_by_mac.items():
        out[mac] = "+".join(sorted(bands, key=sort_key))
    return out


def print_hosts(hosts: List[Dict]) -> None:
    headers = ["#", "Band", "IP", "Name", "Status", "Interface", "MAC"]
    rows = []
    for i, h in enumerate(hosts, start=1):
        status = "active" if h.get("status") else "-"
        rows.append([
            str(i),
            fmt(h.get("band")),
            fmt(h.get("ip")),
            fmt(h.get("name")),
            status,
            fmt(h.get("interface_type")),
            fmt(h.get("mac")),
        ])

    widths = [len(h) for h in headers]
    for r in rows:
        for idx, cell in enumerate(r):
            widths[idx] = max(widths[idx], len(cell))

    def line(parts):
        return "  ".join(p.ljust(widths[i]) for i, p in enumerate(parts))

    print(line(headers))
    print(line(["-" * w for w in widths]))
    for r in rows:
        print(line(r))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Listet angemeldete/aktive FRITZ!Box Clients via fritzconnection (TR-064) und sortiert nach WLAN-Band."
    )
    ap.add_argument("-i", "--ip", default=os.getenv("FRITZ_ADDRESS", "192.168.2.1"),
                    help="FRITZ!Box IP/Hostname (default: env FRITZ_ADDRESS oder 192.168.2.1)")
    ap.add_argument("-u", "--user", default=os.getenv("FRITZ_USERNAME"),
                    help="FRITZ!Box Benutzer (default: env FRITZ_USERNAME)")
    ap.add_argument("-p", "--password", default=os.getenv("FRITZ_PASSWORD"),
                    help="FRITZ!Box Passwort (default: env FRITZ_PASSWORD)")
    ap.add_argument("--tls", action="store_true",
                    help="TLS verwenden (Port 49443 statt 49000, je nach Box/Config)")
    ap.add_argument("--all", action="store_true",
                    help="Nicht nur aktive Clients, sondern alle bekannten Hosts anzeigen")
    args = ap.parse_args()

    if not args.password:
        print("Kein Passwort gesetzt. Übergib -p/--password oder setze FRITZ_PASSWORD.", file=sys.stderr)
        return 2

    # Eine FritzConnection instanzieren und wiederverwenden (schneller & sauberer)
    fc = FritzConnection(address=args.ip, user=args.user, password=args.password, use_tls=args.tls)
    fh = FritzHosts(fc)
    fw = FritzWLAN(fc)

    # WLAN-Bänder je MAC einsammeln
    wlan_band_by_mac = get_wlan_bands_by_mac(fw)

    # Hosts holen (aktiv oder alle)
    hosts = fh.get_hosts_info() if args.all else fh.get_active_hosts()

    # Band je Host bestimmen
    for h in hosts:
        mac = fmt(h.get("mac")).lower()
        band = wlan_band_by_mac.get(mac)
        if not band:
            # simple Heuristik für kabelgebunden / unknown
            it = fmt(h.get("interface_type")).lower()
            if "ethernet" in it or it == "lan":
                band = "LAN"
            else:
                band = "-"
        h["band"] = band

    # Sortieren: erst Band, dann Name, dann IP
    hosts = sorted(
        hosts,
        key=lambda h: (
            _band_order(fmt(h.get("band"))),
            fmt(h.get("band")),
            fmt(h.get("name")).lower(),
            fmt(h.get("ip")),
        ),
    )

    print_hosts(hosts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
