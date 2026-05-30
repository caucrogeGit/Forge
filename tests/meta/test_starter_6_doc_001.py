"""Garde-fou STARTER-6-DOC-001.

Vérifie que le starter 6 (auth-mfa) a sa documentation utilisateur
sur le modèle des 5 autres starters.

Origine : audit F11 — code starter 6 livré en G7 mais documentation
utilisateur manquante (pas de docs/starters/auth-mfa/).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
STARTERS_DOC_DIR = PROJECT_ROOT / "docs" / "starters"
STARTER_6_DIR = STARTERS_DOC_DIR / "auth-mfa"
STARTERS_INDEX = STARTERS_DOC_DIR / "index.md"


class TestStarter6DocExists:
    """Les fichiers de doc starter 6 existent."""

    def test_starter_6_dir_exists(self):
        assert STARTER_6_DIR.is_dir(), (
            "Le répertoire docs/starters/auth-mfa/ doit exister "
            "(modèle des autres starters : un dossier par starter)."
        )

    def test_index_md_exists(self):
        index_md = STARTER_6_DIR / "index.md"
        assert index_md.exists(), (
            "docs/starters/auth-mfa/index.md doit exister (présentation)."
        )

    def test_rebuild_md_exists(self):
        rebuild_md = STARTER_6_DIR / "rebuild.md"
        assert rebuild_md.exists(), (
            "docs/starters/auth-mfa/rebuild.md doit exister (reconstruction)."
        )


class TestStarter6IndexContent:
    """Le index.md du starter 6 a le contenu minimal attendu."""

    def test_has_title(self):
        text = (STARTER_6_DIR / "index.md").read_text(encoding="utf-8")
        assert "# Starter 6" in text or "# Auth MFA" in text, (
            "Le titre doit identifier clairement le starter 6."
        )

    def test_mentions_alpha_status_and_pypi_publication(self):
        """Le statut Alpha et la publication PyPI depuis `1.0.0-beta.9` sont visibles.

        `forge-mvc-mfa` a été requalifié Pre-Alpha → Alpha par
        `MFA-PYPI-READY-001`, puis publié sur PyPI en `1.0.0-beta.9`
        (DOCS-OPTINS-PYPI-BETA9-SWEEP-001). Le starter 6 doit refléter cet état.
        """
        text = (STARTER_6_DIR / "index.md").read_text(encoding="utf-8")
        assert "Alpha" in text, (
            "Le starter 6 doit mentionner le statut Alpha de `forge-mvc-mfa` "
            "(MFA-PYPI-READY-001)."
        )
        assert "publié sur PyPI" in text or "Publié sur PyPI" in text, (
            "Le starter 6 doit indiquer que `forge-mvc-mfa` est publié sur PyPI "
            "depuis `1.0.0-beta.9` (DOCS-OPTINS-PYPI-BETA9-SWEEP-001)."
        )

    def test_mentions_profil_auth_mfa(self):
        text = (STARTER_6_DIR / "index.md").read_text(encoding="utf-8")
        assert "auth-mfa" in text, (
            "Le starter 6 doit mentionner le profil 'auth-mfa' associé."
        )

    def test_mentions_forge_starter_build_6(self):
        text = (STARTER_6_DIR / "index.md").read_text(encoding="utf-8")
        assert "starter:build 6" in text, (
            "Le starter 6 doit documenter la commande forge starter:build 6."
        )

    def test_mentions_forge_mvc_mfa(self):
        text = (STARTER_6_DIR / "index.md").read_text(encoding="utf-8")
        assert "forge-mvc-mfa" in text, (
            "Le starter 6 doit mentionner la dépendance forge-mvc-mfa."
        )


class TestStartersIndexUpdated:
    """docs/starters/index.md mentionne le starter 6."""

    def test_starter_6_in_synthesis_table(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        assert "3 — Auth MFA" in text or "[3 —" in text, (
            "docs/starters/index.md tableau de synthèse doit lister Auth MFA."
        )

    def test_starter_6_in_generation_block(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        assert "starter:build 3" in text, (
            "docs/starters/index.md doit documenter "
            "'forge starter:build 3' (Auth MFA) dans la section génération."
        )

    def test_starter_6_link_to_index(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        assert "auth-mfa/index.md" in text, (
            "docs/starters/index.md doit linker vers auth-mfa/index.md."
        )

    def test_starter_6_link_to_rebuild(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        assert "auth-mfa/rebuild.md" in text, (
            "docs/starters/index.md doit linker vers auth-mfa/rebuild.md."
        )

    def test_starter_6_status_documented(self):
        """Tableau de statut officiel mentionne le starter 6."""
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        if "## Statut officiel des starters" in text:
            after_status = text.split("## Statut officiel des starters", 1)[1]
            assert "Auth MFA" in after_status or "6 —" in after_status, (
                "Tableau de statut officiel doit inclure le starter 6."
            )


class TestNoBrokenStarter6References:
    """Les références au starter 6 ne sont pas cassées."""

    def test_index_links_to_existing_files(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        if "auth-mfa/index.md" in text:
            assert (STARTER_6_DIR / "index.md").exists()
        if "auth-mfa/rebuild.md" in text:
            assert (STARTER_6_DIR / "rebuild.md").exists()
