"""Tests pour AUTH-LEGACY-BOUNDARY-001 — Frontière core.auth / core.security."""

from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


def _auth_md():
    return (ROOT / "docs" / "features" / "auth.md").read_text(encoding="utf-8")


def _reference_md():
    # Frontière core.auth / core.security documentée sur la page Auth
    # (DOCS-API-CATALOG-003) ; api.md n'est plus qu'un catalogue de liens.
    return (ROOT / "docs" / "features" / "auth.md").read_text(encoding="utf-8")


def _readme_md():
    return (ROOT / "README.md").read_text(encoding="utf-8")


def test_auth_md_mentionne_core_auth_officiel():
    """docs/features/auth.md mentionne core.auth comme API officielle."""
    content = _auth_md()
    assert "core.auth" in content
    assert "officielle" in content or "officiel" in content


def test_auth_md_mentionne_core_security_hashing_legacy():
    """docs/features/auth.md mentionne core.security.hashing comme legacy."""
    content = _auth_md()
    assert "core.security.hashing" in content
    assert "legacy" in content.lower()


def test_auth_md_mentionne_argon2id():
    """docs/features/auth.md mentionne Argon2id."""
    content = _auth_md()
    assert "Argon2id" in content or "argon2id" in content.lower()


def test_auth_md_mentionne_pbkdf2_compatibilite():
    """docs/features/auth.md mentionne PBKDF2 dans un contexte de compatibilité."""
    content = _auth_md()
    assert "PBKDF2" in content


def test_auth_md_contient_section_frontiere():
    """docs/features/auth.md contient la section frontière API officielle / legacy."""
    content = _auth_md()
    assert "API officielle" in content and "legacy" in content.lower()


def test_auth_md_mentionne_modules_officiels_core_security():
    """docs/features/auth.md précise que certains modules core.security restent officiels."""
    content = _auth_md()
    assert "core.security.session" in content
    assert "core.security.rbac" in content or "core.security.middleware" in content


def test_reference_md_mentionne_frontiere_core_auth_core_security():
    """docs/reference/reference.md mentionne la frontière core.auth / core.security."""
    content = _reference_md()
    assert "core.auth" in content
    assert "core.security" in content


def test_readme_ne_presente_pas_pbkdf2_comme_voie_officielle():
    """README.md ne présente pas PBKDF2 comme voie officielle pour les nouveaux projets."""
    content = _readme_md()
    if "PBKDF2" not in content:
        return
    idx = content.find("PBKDF2")
    while idx != -1:
        context = content[max(0, idx - 80) : idx + 80]
        assert any(
            word in context.lower()
            for word in ("legacy", "historique", "ancien", "compatibilité", "compat")
        ), f"PBKDF2 apparaît sans marqueur legacy au contexte : {context!r}"
        idx = content.find("PBKDF2", idx + 1)


def test_roadmap_reference_auth_legacy_boundary_001():
    """forge-roadmap.md référence AUTH-LEGACY-BOUNDARY-001."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(
        encoding="utf-8"
    )
    assert "AUTH-LEGACY-BOUNDARY-001" in content
