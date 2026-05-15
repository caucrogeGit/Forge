"""Garde-fou SECURITY-MD-REFRESH-3.0-001.

Vérifie que SECURITY.md reflète l'état Forge 3.0 :
- table de support à jour (3.0.x supportée)
- périmètre mentionne les modules opt-in
- OIDC en posture 'non fourni' (cohérence avec docs/auth.md L.715)
- email de contact valide

Historiquement SECURITY.md listait 2.0.x comme branche active
(constat audit doc, mai 2026).
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SECURITY_MD = PROJECT_ROOT / "SECURITY.md"


def _current_major() -> str:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"].split(".")[0]


class TestSecurityMdVersionsUpToDate:
    """La table 'Versions supportées' correspond à la majeure courante."""

    def test_file_exists(self):
        assert SECURITY_MD.exists()

    def test_current_major_listed_as_supported(self):
        """La majeure courante (3.x) est listée comme supportée."""
        text = SECURITY_MD.read_text(encoding="utf-8")
        major = _current_major()
        patterns = [
            rf"\|\s*{major}\.0\.x\s*\|.*[✅✓]",
            rf"\|\s*{major}\.x\s*\|.*[✅✓]",
            rf"{major}\.0\.x.*support",
            rf"{major}\.x.*support",
        ]
        found = any(re.search(p, text, re.IGNORECASE) for p in patterns)
        assert found, (
            f"SECURITY.md ne mentionne pas la majeure {major}.x comme supportée. "
            f"Mettre à jour la table 'Supported Versions'."
        )

    def test_no_stale_v2_as_active(self):
        """La branche 2.x n'est plus présentée comme la branche active."""
        text = SECURITY_MD.read_text(encoding="utf-8")
        stale = [
            r"Seule la branche\s+`2\.",
            r"branche\s+`2\.0\.x`\s+reçoit",
            r"maintenu sur.*\b2\.0\.x\b",
        ]
        for p in stale:
            assert not re.search(p, text, re.IGNORECASE), (
                f"SECURITY.md contient une affirmation obsolète sur 2.0.x comme "
                f"branche active : pattern {p!r}."
            )

    def test_divulgation_references_current_branch(self):
        """La section divulgation référence la branche courante (X.0.x)."""
        major = _current_major()
        text = SECURITY_MD.read_text(encoding="utf-8")
        assert f"{major}.0.x" in text or f"{major}.x" in text, (
            f"La section 'Divulgation responsable' doit référencer {major}.0.x."
        )
        stale_divulgation = re.compile(
            r"version corrective.*`2\.0\.x`", re.IGNORECASE
        )
        assert not stale_divulgation.search(text), (
            "La section 'Divulgation responsable' référence encore `2.0.x` "
            "comme branche de correction."
        )


class TestSecurityMdPerimeterOptInModules:
    """Le périmètre mentionne les modules opt-in Forge."""

    def test_at_least_one_opt_in_module_in_perimeter(self):
        """Au moins un module opt-in est listé dans la section Périmètre."""
        text = SECURITY_MD.read_text(encoding="utf-8")
        opt_in = [
            "forge_mvc_mfa", "forge-mvc-mfa",
            "forge_mvc_rbac", "forge-mvc-rbac",
            "forge_mvc_workflow", "forge-mvc-workflow",
            "forge_mvc_stats", "forge-mvc-stats",
        ]
        found = any(m in text for m in opt_in)
        assert found, (
            "SECURITY.md doit mentionner au moins un module opt-in Forge "
            "(forge_mvc_mfa, forge_mvc_rbac, forge_mvc_workflow, forge_mvc_stats)."
        )


class TestSecurityMdOidcConsistent:
    """OIDC est cohérent avec docs/auth.md — non fourni nativement."""

    def test_oidc_not_presented_as_future_feature(self):
        """Si OIDC est mentionné, ce n'est pas comme feature prévue."""
        text = SECURITY_MD.read_text(encoding="utf-8")
        misleading = [
            r"OIDC.*prévu pour Forge 3",
            r"OIDC.*sera disponible",
            r"Forge.*fournit OIDC",
        ]
        for p in misleading:
            assert not re.search(p, text, re.IGNORECASE), (
                f"SECURITY.md présente OIDC comme feature prévue : {p!r}. "
                f"Cohérence avec docs/auth.md requise (OIDC non fourni nativement)."
            )


class TestSecurityMdContactPresent:
    """SECURITY.md fournit un moyen de contact valide."""

    def test_contact_present(self):
        text = SECURITY_MD.read_text(encoding="utf-8")
        has_contact = (
            re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
            or "security advisor" in text.lower()
            or "security@" in text.lower()
        )
        assert has_contact, (
            "SECURITY.md doit fournir un moyen de contact pour les rapports "
            "de vulnérabilité (email ou GitHub Security Advisories)."
        )
