#!/usr/bin/env python3
import os
import sys
import argparse
from typing import List, Dict

try:
    from fritzconnection.lib.fritzhosts import FritzHosts
except ImportError:
    print("Fehlt: fritzconnection. Installiere z.B. mit: pip install fritzconnection==1.15.0", file=sys.stderr)
    sys.exit(2)


def fmt(val: object, fallback: str = "-") -> str:
    if val is None:
        return fallback
    s = str(val).strip()
    return s if s else fallback


def print_hosts(hosts: List[Dict]) -> None:
    # Spaltenbreiten dynamisch bestimmen
    headers = ["#", "IP", "Name", "Status", "Interface"]
    rows = []
    for i, h in enumerate(hosts, start=1):
        status = "active" if h.get("status") else "-"
        rows.append([
            str(i),
            fmt(h.get("ip")),
            fmt(h.get("name")),
            #fmt(h.get("mac")),
            status,
            fmt(h.get("interface_type")),
            #fmt(h.get("lease_time_remaining")),
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
        description="Listet angemeldete/aktive FRITZ!Box Clients via fritzconnection (TR-064)."
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

    fh = FritzHosts(address=args.ip, user=args.user, password=args.password, use_tls=args.tls)

    hosts = fh.get_hosts_info() if args.all else fh.get_active_hosts()
    # optional sortieren: erst nach Name, dann IP
    hosts = sorted(hosts, key=lambda h: (fmt(h.get("name")).lower(), fmt(h.get("ip"))))

    print_hosts(hosts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
