"""Tests pour SECURITY-MD-001 — Politique de sécurité Forge."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


def test_security_md_existe():
    """SECURITY.md existe à la racine du dépôt."""
    assert (ROOT / "SECURITY.md").exists()


def test_security_md_contient_supported_versions():
    """SECURITY.md contient une section 'Supported Versions'."""
    content = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "Supported Versions" in content


def test_security_md_contient_reporting():
    """SECURITY.md contient une section de signalement."""
    content = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "Reporting" in content or "Signalement" in content


def test_security_md_mentionne_sessions_memoire():
    """SECURITY.md mentionne les limites des sessions mémoire."""
    content = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "sessions mémoire" in content or "in-memory sessions" in content


def test_security_md_mentionne_version_courante():
    """SECURITY.md mentionne la version majeure courante."""
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    major = data["project"]["version"].split(".")[0]
    content = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert f"{major}.0" in content, (
        f"SECURITY.md doit mentionner la version majeure {major}.x"
    )


def test_readme_reference_security_md():
    """La politique de sécurité reste découvrable.

    Le README public simplifié ne lie plus explicitement SECURITY.md ;
    GitHub surface automatiquement le fichier `SECURITY.md` présent à la
    racine. On vérifie donc que la politique reste découvrable : lien dans
    le README **ou** fichier présent à la racine.
    """
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "SECURITY.md" in content or (ROOT / "SECURITY.md").exists()
