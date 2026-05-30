"""Garde-fou STARTER-WELCOME-OPTIN-MFA-DOC-001.

Vérifie que le starter `welcome-optin-mfa` (n°3, ex auth-mfa) a sa
documentation utilisateur sur le modèle des autres starters, regroupée
sous le dossier-sujet `docs/starters/optin-mfa/`.

Origine : audit F11 — code starter MFA livré en G7 mais documentation
utilisateur manquante. Renommé lors de STARTER-RENAME-WELCOME-OPTIN-MFA-001
(auth-mfa → welcome-optin-mfa, docs → starters/optin-mfa/).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
STARTERS_DOC_DIR = PROJECT_ROOT / "docs" / "starters"
OPTIN_MFA_DIR = STARTERS_DOC_DIR / "optin-mfa"
DOC_MD = OPTIN_MFA_DIR / "welcome-optin-mfa.md"
REBUILD_MD = OPTIN_MFA_DIR / "welcome-optin-mfa-rebuild.md"
OVERVIEW_MD = OPTIN_MFA_DIR / "index.md"
STARTERS_INDEX = STARTERS_DOC_DIR / "index.md"


class TestStarterMfaDocExists:
    """Les fichiers de doc du starter MFA existent."""

    def test_optin_mfa_dir_exists(self):
        assert OPTIN_MFA_DIR.is_dir(), (
            "Le répertoire docs/starters/optin-mfa/ doit exister "
            "(dossier-sujet opt-in MFA)."
        )

    def test_overview_md_exists(self):
        assert OVERVIEW_MD.exists(), (
            "docs/starters/optin-mfa/index.md doit exister (vue d'ensemble du sujet)."
        )

    def test_doc_md_exists(self):
        assert DOC_MD.exists(), (
            "docs/starters/optin-mfa/welcome-optin-mfa.md doit exister (présentation)."
        )

    def test_rebuild_md_exists(self):
        assert REBUILD_MD.exists(), (
            "docs/starters/optin-mfa/welcome-optin-mfa-rebuild.md doit exister "
            "(reconstruction)."
        )


class TestStarterMfaDocContent:
    """Le welcome-optin-mfa.md a le contenu minimal attendu."""

    def test_has_title(self):
        text = DOC_MD.read_text(encoding="utf-8")
        assert "# Auth MFA" in text, (
            "Le titre doit identifier clairement le starter Auth MFA."
        )

    def test_mentions_alpha_status_and_pypi_publication(self):
        """Le statut Alpha et la publication PyPI depuis `1.0.0-beta.9` sont visibles.

        `forge-mvc-mfa` a été requalifié Pre-Alpha → Alpha par
        `MFA-PYPI-READY-001`, puis publié sur PyPI en `1.0.0-beta.9`
        (DOCS-OPTINS-PYPI-BETA9-SWEEP-001). Le starter doit refléter cet état.
        """
        text = DOC_MD.read_text(encoding="utf-8")
        assert "Alpha" in text, (
            "Le starter doit mentionner le statut Alpha de `forge-mvc-mfa` "
            "(MFA-PYPI-READY-001)."
        )
        assert "publié sur PyPI" in text or "Publié sur PyPI" in text, (
            "Le starter doit indiquer que `forge-mvc-mfa` est publié sur PyPI "
            "depuis `1.0.0-beta.9` (DOCS-OPTINS-PYPI-BETA9-SWEEP-001)."
        )

    def test_mentions_profil_auth_mfa(self):
        text = DOC_MD.read_text(encoding="utf-8")
        assert "auth-mfa" in text, (
            "Le starter doit mentionner le profil 'auth-mfa' associé."
        )

    def test_mentions_forge_starter_build_3(self):
        text = DOC_MD.read_text(encoding="utf-8")
        assert "starter:build 3" in text, (
            "Le starter doit documenter la commande forge starter:build 3."
        )

    def test_mentions_forge_mvc_mfa(self):
        text = DOC_MD.read_text(encoding="utf-8")
        assert "forge-mvc-mfa" in text, (
            "Le starter doit mentionner la dépendance forge-mvc-mfa."
        )


class TestStartersIndexUpdated:
    """docs/starters/index.md mentionne le starter MFA."""

    def test_starter_in_synthesis_table(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        assert "3 — Auth MFA" in text or "[3 —" in text, (
            "docs/starters/index.md tableau de synthèse doit lister Auth MFA."
        )

    def test_starter_in_generation_block(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        assert "starter:build 3" in text, (
            "docs/starters/index.md doit documenter "
            "'forge starter:build 3' (Auth MFA) dans la section génération."
        )

    def test_starter_link_to_doc(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        assert "optin-mfa/welcome-optin-mfa.md" in text, (
            "docs/starters/index.md doit linker vers "
            "optin-mfa/welcome-optin-mfa.md."
        )

    def test_starter_link_to_rebuild(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        assert "optin-mfa/welcome-optin-mfa-rebuild.md" in text, (
            "docs/starters/index.md doit linker vers "
            "optin-mfa/welcome-optin-mfa-rebuild.md."
        )

    def test_starter_status_documented(self):
        """Tableau de statut officiel mentionne le starter MFA."""
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        if "## Statut officiel des starters" in text:
            after_status = text.split("## Statut officiel des starters", 1)[1]
            assert "Auth MFA" in after_status or "3 —" in after_status, (
                "Tableau de statut officiel doit inclure le starter Auth MFA."
            )


class TestNoBrokenStarterMfaReferences:
    """Les références au starter MFA ne sont pas cassées."""

    def test_index_links_to_existing_files(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        if "optin-mfa/welcome-optin-mfa.md" in text:
            assert DOC_MD.exists()
        if "optin-mfa/welcome-optin-mfa-rebuild.md" in text:
            assert REBUILD_MD.exists()
