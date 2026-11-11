#!/usr/bin/env python3
"""Génère les listes IPv4/IPv6 des préfixes annoncés par les ASN de asns.txt.

Source : RIPEstat (announced-prefixes). Aucune dépendance hors stdlib.
Les préfixes sont agrégés (collapse) pour réduire le nombre d'entrées.

Garde-fou : si une liste est vide ou perd plus de MAX_DROP de ses entrées
par rapport à la version précédente, le script échoue et rien n'est publié
(une liste vide reviendrait à désactiver le blocage côté UniFi).
"""
from __future__ import annotations

import ipaddress
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASN_FILE = ROOT / "asns.txt"
OUT_DIR = ROOT / "output"
RIPESTAT = "https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{asn}&sourceapp=fr-hosting-blocklist"
MAX_DROP = 0.5
RETRIES = 3


def read_asns() -> list[int]:
    asns = []
    for line in ASN_FILE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            asns.append(int(line.upper().removeprefix("AS")))
    if not asns:
        sys.exit("asns.txt est vide")
    return asns


def fetch_prefixes(asn: int) -> list[str]:
    url = RIPESTAT.format(asn=asn)
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = json.load(resp)
            if data.get("status") != "ok":
                raise RuntimeError(f"statut RIPEstat : {data.get('status')}")
            return [p["prefix"] for p in data["data"]["prefixes"]]
        except Exception as exc:  # noqa: BLE001
            print(f"AS{asn} tentative {attempt}/{RETRIES} : {exc}", file=sys.stderr)
            time.sleep(5 * attempt)
    sys.exit(f"Échec de récupération pour AS{asn}")


def previous_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for l in path.read_text().splitlines() if l and not l.startswith("#"))


def write_list(path: Path, nets: list, asns: list[int]) -> None:
    old = previous_count(path)
    new = len(nets)
    if new == 0:
        sys.exit(f"{path.name} : 0 entrée, abandon")
    if old and new < old * (1 - MAX_DROP):
        sys.exit(f"{path.name} : {old} -> {new} entrées (baisse > {MAX_DROP:.0%}), abandon")
    path.write_text("\n".join(str(n) for n in nets) + "\n")
    print(f"{path.name} : {new} entrées (avant : {old})")


def main() -> None:
    asns = read_asns()
    v4, v6 = [], []
    for asn in asns:
        prefixes = fetch_prefixes(asn)
        print(f"AS{asn} : {len(prefixes)} préfixes")
        for p in prefixes:
            net = ipaddress.ip_network(p, strict=False)
            (v4 if net.version == 4 else v6).append(net)
        time.sleep(1)

    OUT_DIR.mkdir(exist_ok=True)
    write_list(OUT_DIR / "ipv4.txt", list(ipaddress.collapse_addresses(v4)), asns)
    write_list(OUT_DIR / "ipv6.txt", list(ipaddress.collapse_addresses(v6)), asns)


if __name__ == "__main__":
    main()
