"""Garde-fou PIP-AUDIT-OPTIN-COVERAGE-001 (audit packaging).

pip-audit en CI n'auditait que les 4 dépendances du cœur (`requirements.txt`),
laissant les dépendances tierces des opt-ins (Pillow, cryptography, mariadb, ...)
jamais scannées. On audite désormais `requirements-audit.txt` ; ce test vérifie
que TOUTE dépendance tierce déclarée par un paquet opt-in y figure (via le cœur
ou la liste opt-in), pour qu'un nouvel ajout ne puisse pas échapper à l'audit.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]

# Paquets dev-only (ADR-041) : leurs dépendances (pytest) ne sont pas expédiées
# en runtime et sont couvertes par l'outillage, pas par l'audit de surface.
_DEV_ONLY_PACKAGES = {"forge-mvc-testing"}


def _normalize(dep: str) -> str:
    """Nom de distribution normalisé (sans version, extras, casse)."""
    name = re.split(r"[<>=!~; \[]", dep.strip(), maxsplit=1)[0]
    return name.strip().lower().replace("_", "-")


def _deps_of(pyproject: Path) -> list[str]:
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r"dependencies\s*=\s*\[(.*?)\]", text, re.DOTALL)
    if not m:
        return []
    return re.findall(r'"([^"]+)"', m.group(1))


def _audited_names() -> set[str]:
    names: set[str] = set()
    for req in (ROOT / "requirements.txt", ROOT / "requirements-audit.txt"):
        for line in req.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            names.add(_normalize(line))
    return names


def test_requirements_audit_file_exists():
    assert (ROOT / "requirements-audit.txt").is_file()


def test_ci_audits_the_extended_list():
    wf = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "requirements-audit.txt" in wf, "pip-audit doit cibler requirements-audit.txt"


def test_every_optin_thirdparty_dep_is_audited():
    audited = _audited_names()
    missing: list[str] = []
    for pyproject in sorted((ROOT / "packages").glob("*/pyproject.toml")):
        pkg_dir = pyproject.parent.name
        if pkg_dir in _DEV_ONLY_PACKAGES:
            continue
        for dep in _deps_of(pyproject):
            name = _normalize(dep)
            if name.startswith("forge-mvc"):
                continue  # dépendance interne, pas une surface CVE tierce
            if name not in audited:
                missing.append(f"{pkg_dir}: {dep}")
    assert not missing, (
        "Dépendances tierces d'opt-ins absentes de requirements-audit.txt "
        "(donc non scannées par pip-audit) :\n  " + "\n  ".join(missing)
    )
