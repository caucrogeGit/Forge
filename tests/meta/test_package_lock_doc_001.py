"""Garde-fou PACKAGE-LOCK-DOC-001.

Vérifie que les règles de verrouillage packaging sont documentées et que
les artefacts de build ne risquent pas d'être commités accidentellement.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestGitignoreBuildArtifacts:
    """Les artefacts de build sont exclus de Git."""

    def test_dist_ignored(self):
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "dist/" in gitignore, (
            ".gitignore doit exclure dist/ (artefacts build — PACKAGE-LOCK-DOC-001)"
        )

    def test_build_ignored(self):
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "build/" in gitignore, (
            ".gitignore doit exclure build/ (artefacts build — PACKAGE-LOCK-DOC-001)"
        )

    def test_egg_info_ignored(self):
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "*.egg-info" in gitignore, (
            ".gitignore doit exclure *.egg-info/ (artefacts build — PACKAGE-LOCK-DOC-001)"
        )


class TestReleasePolicyPackagingLock:
    """docs/release/release-policy.md documente explicitement le verrouillage packaging."""

    def _policy(self) -> str:
        doc = PROJECT_ROOT / "docs" / "release" / "release-policy.md"
        if not doc.exists():
            pytest.skip("docs/release/release-policy.md n'existe pas")
        return doc.read_text(encoding="utf-8")

    def test_section_verrouillage_presente(self):
        assert "Verrouillage packaging" in self._policy(), (
            "docs/release/release-policy.md doit contenir une section 'Verrouillage packaging' "
            "(PACKAGE-LOCK-DOC-001)"
        )

    def test_twine_check_documente_comme_validation_locale(self):
        text = self._policy()
        assert "twine check" in text, (
            "docs/release/release-policy.md doit documenter 'twine check' "
            "comme validation locale (PACKAGE-LOCK-DOC-001)"
        )

    def test_publication_releve_dun_ticket_dedie(self):
        text = self._policy()
        assert "ticket" in text and "publication" in text.lower(), (
            "docs/release/release-policy.md doit indiquer que la publication PyPI "
            "relève d'un ticket dédié (PACKAGE-LOCK-DOC-001)"
        )

    def test_mfa_non_publie_documente(self):
        text = self._policy()
        assert "forge-mvc-mfa" in text, (
            "docs/release/release-policy.md doit mentionner forge-mvc-mfa "
            "et son statut de non-publication PyPI en 1.0"
        )
