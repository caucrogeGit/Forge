#!/usr/bin/env python3
"""Signale qu'un avis de sécurité ignoré a désormais un correctif amont.

`pip-audit` est lancé avec `--ignore-vuln` sur des avis sans version corrective
(voir `SECURITY.md`). Un `--ignore-vuln` est une dette : sans surveillance, il
survit à la publication du correctif et masque une vulnérabilité **réparable**.

Ce script relit l'audit **sans** les exclusions et échoue dès qu'un avis ignoré
annonce une version corrective : c'est le signal qu'il faut relever la borne de
la dépendance et retirer l'exclusion.

Il ne remplace pas l'audit : il surveille les seules exclusions.

Usage :
    python tools/check_ignored_vulns.py [requirements.txt ...]

Code retour : 0 si aucun avis ignoré n'a de correctif, 1 sinon (ou si l'audit
n'a pas pu tourner).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

#: Avis ignorés par `--ignore-vuln` dans la CI et `tools/release-validate.sh`.
#: Garder cette liste alignée sur ces deux endroits, et sur `SECURITY.md`.
IGNORED_VULNERABILITIES = {
    "PYSEC-2026-217": "mariadb : avis sans correctif amont, chemin vulnérable non emprunté par Forge",
}

DEFAULT_REQUIREMENTS = ("requirements-audit.txt",)


def _audit(requirement_files: tuple[str, ...]) -> "list[dict[str, Any]]":
    """Lance pip-audit en JSON, sans aucune exclusion, et rend ses dépendances."""
    command = [sys.executable, "-m", "pip_audit", "--format", "json", "--progress-spinner", "off"]
    for path in requirement_files:
        command += ["-r", path]

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    payload = completed.stdout.strip()
    if not payload:
        raise RuntimeError(
            "pip-audit n'a produit aucune sortie JSON.\n" + completed.stderr.strip()
        )
    try:
        report = json.loads(payload)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Sortie pip-audit illisible : {error}") from error
    dependencies: list[dict[str, Any]] = report.get("dependencies") or []
    return dependencies


def find_fixed_ignored(
    dependencies: "list[dict[str, Any]]",
) -> list[tuple[str, str, str, list[str]]]:
    """Avis ignorés qui annoncent désormais une ou plusieurs versions correctives."""
    found: list[tuple[str, str, str, list[str]]] = []
    for dependency in dependencies:
        name = str(dependency.get("name", "?"))
        version = str(dependency.get("version", "?"))
        vulnerabilities: list[dict[str, Any]] = dependency.get("vulns") or []
        for vulnerability in vulnerabilities:
            identifier = str(vulnerability.get("id", ""))
            if identifier not in IGNORED_VULNERABILITIES:
                continue
            fixes = [str(item) for item in (vulnerability.get("fix_versions") or [])]
            if fixes:
                found.append((identifier, name, version, fixes))
    return found


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    requirement_files = tuple(arguments) or DEFAULT_REQUIREMENTS

    missing = [path for path in requirement_files if not Path(path).is_file()]
    if missing:
        print(f"Fichier introuvable : {', '.join(missing)}", file=sys.stderr)
        return 1

    print(f"Surveillance des avis ignorés ({', '.join(requirement_files)})")
    for identifier, reason in sorted(IGNORED_VULNERABILITIES.items()):
        print(f"  - {identifier} : {reason}")

    try:
        dependencies = _audit(requirement_files)
    except RuntimeError as error:
        print(f"\nÉchec de l'audit : {error}", file=sys.stderr)
        return 1

    fixed = find_fixed_ignored(dependencies)
    if not fixed:
        print("\nAucun avis ignoré n'a de correctif amont. Rien à faire.")
        return 0

    print("\nUn avis ignoré a désormais un correctif :", file=sys.stderr)
    for identifier, name, version, fixes in fixed:
        print(
            f"  {identifier} — {name} {version} corrigé en {', '.join(fixes)}",
            file=sys.stderr,
        )
    print(
        "\nRelevez la borne de la dépendance, puis retirez l'exclusion de :\n"
        "  - .github/workflows/tests.yml (--ignore-vuln)\n"
        "  - tools/release-validate.sh (--ignore-vuln)\n"
        "  - tools/check_ignored_vulns.py (IGNORED_VULNERABILITIES)\n"
        "  - SECURITY.md",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
