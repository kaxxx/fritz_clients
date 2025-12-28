fritzconnect – Aktive FRITZ!Box-Clients nach WLAN‑Band anzeigen

Dieses kleine CLI-Tool listet verbundene/aktive Geräte (Hosts) einer FRITZ!Box über die TR‑064‑Schnittstelle auf und sortiert sie nach dem verwendeten WLAN‑Band (2.4/5/6 GHz). Zusätzlich wird eine einfache Heuristik genutzt, um LAN‑Clients als "LAN" zu kennzeichnen.

Funktionen
- Abfrage der FRITZ!Box via TR‑064 (fritzconnection)
- Ermittlung der WLAN‑Bänder pro Gerät (inkl. Multi‑Band/Mehrfachzuordnung, z. B. "2.4 GHz+5 GHz")
- Ausgabe als übersichtliche Tabelle, sortiert nach Band → Name → IP
- Optional Anzeige aller bekannten Hosts (nicht nur aktive)

Voraussetzungen
- Python 3.8+
- Paket fritzconnection (getestet mit 1.15.0)
- Aktivierte TR‑064‑Schnittstelle der FRITZ!Box (Heimnetz → Netzwerk → Netzwerkeinstellungen)

Installation
Empfohlen wird die Installation in einer virtuellen Umgebung.

```
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install fritzconnection==1.15.0
```

Klonen oder kopieren Sie dieses Repository lokal. Ein Build ist nicht erforderlich; das Skript kann direkt ausgeführt werden.

Verwendung
Das Hauptskript ist fritz_clients.py.

Beispiele:

```
# Nur aktive Clients anzeigen (Standard), Verbindung ohne TLS
python fritz_clients.py -i 192.168.178.1 -u meinuser -p meinpasswort

# Mit TLS (Port 49443), IP aus ENV, Benutzer aus ENV
export FRITZ_ADDRESS=192.168.178.1
export FRITZ_USERNAME=meinuser
export FRITZ_PASSWORD=meinpasswort
python fritz_clients.py --tls

# Alle bekannten Hosts (nicht nur aktive) anzeigen
python fritz_clients.py -p meinpasswort --all
```

Argumente
- -i, --ip: FRITZ!Box IP/Hostname (Default: ENV FRITZ_ADDRESS oder 192.168.2.1)
- -u, --user: FRITZ!Box Benutzer (Default: ENV FRITZ_USERNAME)
- -p, --password: FRITZ!Box Passwort (Default: ENV FRITZ_PASSWORD) – erforderlich
- --tls: TLS verwenden (Port 49443 statt 49000, abhängig von Box/Config)
- --all: Nicht nur aktive Clients, sondern alle bekannten Hosts anzeigen

Ausgabe
Eine Tabelle mit Spalten: Nummer, Band, IP, Name, Status, Interface, MAC. Das Band wird nach folgender Ordnung gruppiert und sortiert:
- 2.4 GHz → 5 GHz → 6 GHz → WLAN (?) → LAN → -

Mehrband-Verbindungen werden mit "+" verknüpft, z. B. "2.4 GHz+5 GHz".

Hinweise und Troubleshooting
- Falls die Bibliothek fehlt, installieren Sie sie wie oben beschrieben (z. B. `pip install fritzconnection==1.15.0`).
- Stellen Sie sicher, dass TR‑064 auf der FRITZ!Box aktiviert ist und der Benutzer ausreichende Rechte besitzt.
- Bei Zertifikats-/TLS‑Fehlern: Testweise ohne `--tls` starten oder Zertifikat korrekt einrichten.
- Unterschiedliche FRITZ!OS‑Versionen liefern teils abweichende Keys. Dieses Tool versucht die relevanten Felder robust zu erkennen; fehlende Band‑Informationen werden als "-" angezeigt.

Projektstruktur (Kurzüberblick)
- fritz_clients.py: CLI, Host‑Abfrage, Sortierung und Ausgabe
- wlan_helpers.py: Ermittlung der WLAN‑Bänder pro MAC über alle WLANConfiguration‑Services
- bands.py: Mapping und Sortierreihenfolge der Bänder
- utils.py: Kleine Hilfsfunktionen (z. B. format_value)

Lizenz
Dieses Projekt steht unter der MIT-Lizenz. Siehe die Datei LICENSE im Repository für den vollständigen Lizenztext.
