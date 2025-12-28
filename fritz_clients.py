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


from utils import fmt
from bands import _band_order
from wlan_helpers import get_wlan_bands_by_mac


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

    # Sortierschlüssel einmalig je Host berechnen (vermeidet wiederholte fmt()/lower()-Aufrufe)
    for h in hosts:
        _band = fmt(h.get("band"))
        h["_sbo"] = _band_order(_band)
        h["_sband"] = _band
        h["_sname"] = fmt(h.get("name")).lower()
        h["_sip"] = fmt(h.get("ip"))

    # Sortieren: erst Band, dann Name, dann IP
    hosts = sorted(
        hosts,
        key=lambda h: (
            h["_sbo"],
            h["_sband"],
            h["_sname"],
            h["_sip"],
        ),
    )

    print_hosts(hosts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
