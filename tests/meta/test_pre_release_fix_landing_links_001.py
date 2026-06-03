"""Tests PRE-RELEASE-FIX-LANDING-LINKS-001 : 5 URLs cassées corrigées dans la landing."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
LANDING_SOURCE = PROJECT_ROOT / "mvc" / "views" / "landing" / "index.html"
LANDING_GENERATED = PROJECT_ROOT / "docs" / "index.html"

# URLs cassées identifiées par l'audit pré-release-3.0-audit-001
BROKEN_URLS = [
    "starter-app-01-contacts",
    "starter-app-utilisateurs-auth",
    "starter-app-carnet-contacts",
    "starter-app-suivi-comportement-eleves",
]

# URLs corrigées attendues (landing simplifiée : seule la carte `welcome`
# subsiste côté starters ; les autres sont accessibles via la documentation).
FIXED_URLS = [
    "starters/welcome-forge/",
    "roadmap/forge-roadmap/",
]


class TestBrokenURLsAbsent:
    """Les URLs cassées identifiées par l'audit ne sont plus présentes."""

    @pytest.mark.parametrize("broken", BROKEN_URLS)
    def test_broken_url_not_in_source(self, broken):
        content = LANDING_SOURCE.read_text(encoding="utf-8")
        assert broken not in content, (
            f"L'URL cassée '{broken}' devrait être supprimée de "
            f"mvc/views/landing/index.html (corrigée vers le nouveau slug)"
        )

    @pytest.mark.parametrize("broken", BROKEN_URLS)
    def test_broken_url_not_in_generated(self, broken):
        content = LANDING_GENERATED.read_text(encoding="utf-8")
        assert broken not in content, (
            f"L'URL cassée '{broken}' devrait être absente de "
            f"docs/index.html (régénération via forge sync:landing)"
        )

    def test_old_roadmap_pattern_corrected(self):
        """Le lien Forge/roadmap/ sans suffixe doit être corrigé."""
        content = LANDING_SOURCE.read_text(encoding="utf-8")
        assert 'Forge/roadmap/"' not in content, (
            "L'ancien pattern de lien 'Forge/roadmap/\"' devrait être "
            "corrigé en 'Forge/roadmap/forge-roadmap/\"'"
        )


class TestFixedURLsPresent:
    """Les URLs corrigées sont présentes dans la source et la version générée."""

    @pytest.mark.parametrize("fixed", FIXED_URLS)
    def test_fixed_url_in_source(self, fixed):
        content = LANDING_SOURCE.read_text(encoding="utf-8")
        assert fixed in content, (
            f"L'URL corrigée '{fixed}' devrait être présente dans "
            f"mvc/views/landing/index.html"
        )

    @pytest.mark.parametrize("fixed", FIXED_URLS)
    def test_fixed_url_in_generated(self, fixed):
        content = LANDING_GENERATED.read_text(encoding="utf-8")
        assert fixed in content, (
            f"L'URL corrigée '{fixed}' devrait être présente dans "
            f"docs/index.html (régénération via forge sync:landing)"
        )


class TestStarterLinksCount:
    """La section starters met en avant au moins le starter `welcome`.

    Refonte landing : les cartes Niveau 1/2/3 ont été retirées au profit
    d'une seule carte `welcome` + un renvoi à la documentation.
    """

    def test_at_least_one_starter_link(self):
        content = LANDING_SOURCE.read_text(encoding="utf-8")
        matches = re.findall(r"starters/[a-z][a-z0-9-]+/", content)
        unique_starters = set(matches)
        assert len(unique_starters) >= 1, (
            f"Au moins un lien starter devrait être présent, "
            f"trouvé {len(unique_starters)} : {unique_starters}"
        )


class TestRoadmapLinkUpdated:
    """Le lien roadmap pointe vers le slug correct."""

    def test_roadmap_points_to_forge_roadmap(self):
        content = LANDING_SOURCE.read_text(encoding="utf-8")
        assert "roadmap/forge-roadmap/" in content, (
            "Le lien roadmap devrait pointer vers 'roadmap/forge-roadmap/' "
            "(la section Roadmap n'a pas d'index.md)"
        )
