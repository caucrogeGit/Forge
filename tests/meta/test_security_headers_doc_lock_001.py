"""Garde-fou SECURITY-HEADERS-DOC-LOCK-001.

Verifie que :
- SECURITY-HEADERS-DOC-LOCK-001 est reference dans la roadmap ;
- docs/philosophy/security.md mentionne les en-tetes de securite ;
- la documentation mentionne CSP ;
- la documentation mentionne HSTS ;
- la documentation mentionne X-Frame-Options ;
- la documentation mentionne X-Content-Type-Options ;
- la documentation mentionne Referrer-Policy ;
- la documentation contient une section de limites ;
- la documentation ne promet pas une securite complete.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent

SECURITY_DOC = PROJECT_ROOT / "docs" / "philosophy" / "security.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


class TestRoadmapReference:
    def test_roadmap_mentions_ticket(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "SECURITY-HEADERS-DOC-LOCK-001" in text, (
            "La roadmap doit mentionner SECURITY-HEADERS-DOC-LOCK-001."
        )

    def test_roadmap_marks_ticket_as_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        idx = text.find("SECURITY-HEADERS-DOC-LOCK-001")
        assert idx != -1
        bloc = text[idx:idx + 120]
        assert "livré" in bloc, (
            "SECURITY-HEADERS-DOC-LOCK-001 doit etre marque 'livré' dans la roadmap."
        )


class TestSecurityDocMentionsHeaders:
    def _doc(self) -> str:
        return SECURITY_DOC.read_text(encoding="utf-8")

    def test_doc_mentionne_headers_securite(self):
        text = self._doc()
        assert "En-têtes de sécurité" in text or "headers de sécurité" in text.lower() or "security header" in text.lower(), (
            "docs/philosophy/security.md doit avoir une section sur les en-tetes de securite."
        )

    def test_doc_mentionne_csp(self):
        text = self._doc()
        assert "Content-Security-Policy" in text or "CSP" in text, (
            "docs/philosophy/security.md doit mentionner Content-Security-Policy (CSP)."
        )

    def test_doc_mentionne_hsts_ou_strict_transport(self):
        text = self._doc()
        assert "Strict-Transport-Security" in text or "HSTS" in text, (
            "docs/philosophy/security.md doit mentionner HSTS ou Strict-Transport-Security."
        )

    def test_doc_mentionne_x_frame_options(self):
        text = self._doc()
        assert "X-Frame-Options" in text, (
            "docs/philosophy/security.md doit mentionner X-Frame-Options."
        )

    def test_doc_mentionne_x_content_type_options(self):
        text = self._doc()
        assert "X-Content-Type-Options" in text or "nosniff" in text, (
            "docs/philosophy/security.md doit mentionner X-Content-Type-Options ou nosniff."
        )

    def test_doc_mentionne_referrer_policy(self):
        text = self._doc()
        assert "Referrer-Policy" in text, (
            "docs/philosophy/security.md doit mentionner Referrer-Policy."
        )

    def test_doc_mentionne_permissions_policy(self):
        text = self._doc()
        assert "Permissions-Policy" in text, (
            "docs/philosophy/security.md doit mentionner Permissions-Policy."
        )

    def test_doc_contient_section_limites(self):
        text = self._doc()
        assert "Limites" in text or "limite" in text.lower() or "ne remplace pas" in text, (
            "docs/philosophy/security.md doit mentionner les limites des en-tetes de securite."
        )

    def test_doc_ne_promet_pas_securite_complete(self):
        text = self._doc()
        forbidden = [
            "garantit une sécurité complète",
            "protège contre toutes les attaques XSS",
            "remplace la configuration HTTPS du reverse proxy",
            "rend inutile une politique CSP applicative",
        ]
        for phrase in forbidden:
            assert phrase not in text, (
                f"docs/philosophy/security.md ne doit pas promettre une securite complete : {phrase!r}."
            )
