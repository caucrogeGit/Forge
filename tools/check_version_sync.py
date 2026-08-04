#!/usr/bin/env python3
# pyright: strict
"""tools/check_version_sync.py — cohérence de version sur tout le dépôt.

Ticket PKG-VERSION-SYNC-CHECK-001.

Dérive la version canonique depuis le pyproject racine (`[project].version`, en
PEP 440, ex. `1.0.0rc1`) et vérifie que TOUS les emplacements la reprennent :

- `version =` des sous-paquets ;
- les pins `forge-mvc>=` (et `forge-mvc-files>=` pour images) des sous-paquets ;
- les pins des extras du pyproject racine (`rbac`, `workflow`, `stats`, `all`) ;
- `core/__init__.py` (`__version__`) et `forge.py` (`_FORGE_VERSION`) ;
- le `__version__` du module de chaque sous-paquet (`VERSION-SYNC-OPTIN-MODULE-001`) ;
- le pin `forge-mvc==` du squelette (`skeleton/data/requirements.txt`) ;
- `package.json`, en forme SemVer publique (ex. `1.0.0-beta.17`).

`VERSION-SYNC-OPTIN-MODULE-001` : les vingt-sept `__init__.py` d'opt-in portent
chacun un `__version__`, et rien ne le comparait au canonique. Seul le
`pyproject.toml` du paquet était vérifié. Un bump qui en oublie un publie donc
un paquet en rc4 dont `forge_mvc_x.__version__` répond encore `rc3`, sans qu'un
seul contrôle proteste. Mesuré à la veille de la rc4 : les vingt-sept étaient
alignés, mais par chance, aucune contrainte ne le garantissant. Un bump touche
soixante et un fichiers ; la moitié n'était pas couverte.

Sortie : 0 si tout est cohérent, 1 avec le détail des écarts sinon.
Autonome (aucun argument) : utilisable en test méta et dans les scripts release.
"""
from __future__ import annotations

from typing import Any

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pep440_to_semver(version: str) -> str:
    """`1.0.0rc1` -> `1.0.0-beta.17` (stable inchangé)."""
    version = re.sub(r"rc(\d+)$", r"-rc.\1", version)
    version = re.sub(r"a(\d+)$", r"-alpha.\1", version)
    version = re.sub(r"b(\d+)$", r"-beta.\1", version)
    return version


def _toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _first_match(path: Path, pattern: str) -> str | None:
    found = re.search(pattern, path.read_text(encoding="utf-8"))
    return found.group(1) if found else None


def collect_mismatches() -> tuple[str, list[str]]:
    mismatches: list[str] = []
    root = _toml(ROOT / "pyproject.toml")
    canonical = root["project"]["version"]
    semver = pep440_to_semver(canonical)

    def check(label: str, found: str | None, expected: str) -> None:
        if found != expected:
            mismatches.append(f"{label} : trouvé {found!r}, attendu {expected!r}")

    # Sous-paquets : version= et pins forge-mvc / forge-mvc-files.
    for pyproject in sorted((ROOT / "packages").glob("forge-mvc-*/pyproject.toml")):
        name = pyproject.parent.name
        project = _toml(pyproject).get("project", {})
        check(f"{name} version", project.get("version"), canonical)
        for dep in project.get("dependencies", []):
            pin = re.match(r"(forge-mvc(?:-[a-z0-9]+)?)\s*>=\s*([0-9][^,\s]*)", dep)
            if pin and pin.group(1) in ("forge-mvc", "forge-mvc-files"):
                check(f"{name} pin {pin.group(1)}", pin.group(2), canonical)

    # VERSION-SYNC-OPTIN-MODULE-001 : le `__version__` du module, distinct du
    # `version` de son pyproject. C'est celui qu'une application lit à
    # l'exécution, et il n'était comparé à rien.
    for init in sorted((ROOT / "packages").glob("forge-mvc-*/forge_mvc_*/__init__.py")):
        paquet = init.parent.parent.name
        declare = _first_match(init, r'__version__\s*=\s*"([^"]+)"')
        if declare is not None:
            check(f"{paquet} module __version__", declare, canonical)

    # Extras du pyproject racine (rbac / workflow / stats / all).
    for extra, deps in root["project"].get("optional-dependencies", {}).items():
        for dep in deps:
            pin = re.match(r"(forge-mvc-[a-z0-9]+)\s*>=\s*([0-9][^,\s]*)", dep)
            if pin:
                check(f"extra [{extra}] {pin.group(1)}", pin.group(2), canonical)

    # Fichiers Python (PEP 440).
    check("core/__init__.py __version__",
          _first_match(ROOT / "core/__init__.py", r'__version__\s*=\s*"([^"]+)"'), canonical)
    check("forge.py _FORGE_VERSION",
          _first_match(ROOT / "forge.py", r'_FORGE_VERSION\s*=\s*"([^"]+)"'), canonical)

    # Squelette (pin == reproductible du projet généré).
    check("skeleton/data/requirements.txt forge-mvc==",
          _first_match(ROOT / "skeleton/data/requirements.txt", r"forge-mvc==([0-9][^,\s]*)"),
          canonical)
    check("skeleton/data/requirements-dev.txt forge-mvc-testing==",
          _first_match(ROOT / "skeleton/data/requirements-dev.txt", r"forge-mvc-testing==([0-9][^,\s]*)"),
          canonical)

    # package.json (SemVer public).
    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    check("package.json version (SemVer)", package_json.get("version"), semver)

    # package-lock.json (SemVer public) : le verrou npm doit suivre package.json.
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    check("package-lock.json version (SemVer)", lock.get("version"), semver)
    root_pkg = lock.get("packages", {}).get("", {})
    check("package-lock.json packages[''].version (SemVer)", root_pkg.get("version"), semver)

    return canonical, mismatches


def main() -> int:
    canonical, mismatches = collect_mismatches()
    if mismatches:
        print(f"Désynchronisation de version (canonique = {canonical}) :")
        for line in mismatches:
            print(f"  - {line}")
        return 1
    print(f"Versions cohérentes sur tout le dépôt (canonique = {canonical}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
