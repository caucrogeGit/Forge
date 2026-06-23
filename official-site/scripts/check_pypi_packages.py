#!/usr/bin/env python3
"""Vérification réseau du statut PyPI des paquets Forge.

Interroge l'API JSON publique ``https://pypi.org/pypi/<package>/json`` pour
chaque paquet listé et affiche un tableau récapitulatif. Aucune dépendance
externe ; seulement la stdlib.

Tolère l'absence de réseau (affiche « non vérifié réseau » sans planter).

Le script est un outil de vérification, jamais une dépendance du build.
"""

from __future__ import annotations

import argparse
import json
import socket
from urllib import error, request

DEFAULT_PACKAGES: tuple[str, ...] = (
    "forge-mvc",
    "forge-mvc-stats",
    "forge-mvc-rbac",
    "forge-mvc-workflow",
    "forge-mvc-media",
    "forge-mvc-mfa",
)

EXPECTED_VERSION = "1.0.0b9"
PYPI_JSON = "https://pypi.org/pypi/{name}/json"


def fetch_pypi(name: str, timeout: float) -> dict:
    """Retourne un dict synthétique pour un paquet PyPI."""
    url = PYPI_JSON.format(name=name)
    try:
        with request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        if exc.code == 404:
            return {"status": "absent", "version": None, "note": "404"}
        return {"status": "error", "version": None, "note": f"HTTP {exc.code}"}
    except (error.URLError, socket.timeout, TimeoutError) as exc:
        return {"status": "network", "version": None, "note": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "version": None, "note": repr(exc)}

    info = data.get("info", {}) or {}
    return {
        "status": "ok",
        "version": info.get("version"),
        "summary": info.get("summary", "")[:80],
        "note": "",
    }


def coherence(version: str | None) -> str:
    if version is None:
        return "—"
    if version == EXPECTED_VERSION:
        return "ok"
    return f"divergent (≠ {EXPECTED_VERSION})"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Vérifie le statut PyPI des paquets Forge."
    )
    parser.add_argument(
        "packages",
        nargs="*",
        default=list(DEFAULT_PACKAGES),
        help=f"Paquets à interroger (défaut : {len(DEFAULT_PACKAGES)} paquets).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout par requête, secondes (défaut: 5).",
    )
    args = parser.parse_args()

    print(f"Version Forge attendue (référence)  : {EXPECTED_VERSION}")
    print(f"Endpoint                            : {PYPI_JSON.format(name='<package>')}")
    print(f"Timeout                             : {args.timeout}s")
    print()
    print(f"{'Paquet':22} {'Statut':10} {'Version':14} {'Cohérence':22} Note")
    print("-" * 100)

    network_error_seen = False
    for name in args.packages:
        result = fetch_pypi(name, args.timeout)
        status = result["status"]
        version = result.get("version") or "—"
        coh = coherence(result.get("version"))
        note = result.get("note") or result.get("summary") or ""
        if status == "network":
            note = "non vérifié réseau"
            network_error_seen = True
        print(f"{name:22} {status:10} {str(version):14} {coh:22} {note}")

    print()
    if network_error_seen:
        print("Attention : au moins une requête a échoué sans réseau.")
        print("Relancer plus tard, ou se référer à pypi.org manuellement.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
