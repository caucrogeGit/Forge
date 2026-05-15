"""Garde-fou LANDING-POSITIONNEMENT-REMOVE-001.

Vérifie que la section 'Positionnement' (manifesto + compteur de tests)
a bien été retirée de la landing et n'est pas réintroduite par erreur.

Le contenu manifesto migre vers la charte (CHARTE_DOC.md) qui est la
source de vérité pour l'identité Forge. Le compteur de tests créait
un drift permanent à maintenir (sync à chaque ticket), pour un gain
marginal en lisibilité.

Origine : ticket T23 — cleanup post-3.0.2 décidé par le propriétaire
de Forge.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
LANDING_HTML = PROJECT_ROOT / "mvc" / "views" / "landing" / "index.html"
DOCS_INDEX_HTML = PROJECT_ROOT / "docs" / "index.html"


class TestLandingNoMorePositionnementSection:
    """La section 'Positionnement' n'existe plus dans la landing source."""

    def test_no_positionnement_html_comment(self):
        text = LANDING_HTML.read_text(encoding="utf-8")
        assert "<!-- Positionnement -->" not in text, (
            "Le commentaire HTML <!-- Positionnement --> a été réintroduit "
            "dans la landing. T23 l'avait retiré (décision : contenu "
            "manifesto vit dans CHARTE_DOC.md, compteur de tests retiré "
            "pour éviter le drift permanent)."
        )

    def test_no_landing_test_count_id(self):
        text = LANDING_HTML.read_text(encoding="utf-8")
        assert 'id="landing-test-count"' not in text, (
            "L'id 'landing-test-count' a été réintroduit. T23 l'avait "
            "retiré pour éliminer le drift permanent."
        )

    def test_no_landing_manifesto_list_class(self):
        text = LANDING_HTML.read_text(encoding="utf-8")
        assert "landing-manifesto-list" not in text, (
            "La classe 'landing-manifesto-list' a été réintroduite."
        )

    @pytest.mark.parametrize("manifesto_phrase", [
        "Petit dans son cœur",
        "Riche par ses briques",
        "Clair dans ses générateurs",
        "Fortement documenté",
    ])
    def test_manifesto_phrase_absent_from_landing(self, manifesto_phrase: str):
        """Les 4 phrases manifesto ne sont plus dans la landing."""
        text = LANDING_HTML.read_text(encoding="utf-8")
        assert manifesto_phrase not in text, (
            f"La phrase manifesto '{manifesto_phrase}' a été réintroduite "
            f"dans la landing. T23 a déplacé le manifesto vers CHARTE_DOC.md."
        )


class TestDocsIndexSynced:
    """docs/index.html est synchronisé (la section est aussi retirée)."""

    def test_docs_index_no_landing_test_count(self):
        if not DOCS_INDEX_HTML.exists():
            pytest.skip("docs/index.html absent")
        text = DOCS_INDEX_HTML.read_text(encoding="utf-8")
        assert 'id="landing-test-count"' not in text, (
            "docs/index.html contient encore 'landing-test-count'. "
            "Lancer `forge sync:landing` pour régénérer."
        )

    def test_docs_index_no_positionnement_comment(self):
        if not DOCS_INDEX_HTML.exists():
            pytest.skip("docs/index.html absent")
        text = DOCS_INDEX_HTML.read_text(encoding="utf-8")
        assert "<!-- Positionnement -->" not in text, (
            "docs/index.html contient encore la section Positionnement. "
            "Lancer `forge sync:landing`."
        )


class TestManifestoStillInCharter:
    """Le manifesto reste dans la charte (source de vérité)."""

    def test_charter_still_mentions_manifesto(self):
        """Le manifesto continue d'exister dans CHARTE_DOC.md."""
        charter = PROJECT_ROOT / "CHARTE_DOC.md"
        if not charter.exists():
            pytest.skip("CHARTE_DOC.md introuvable")
        text = charter.read_text(encoding="utf-8")
        manifest_phrases = [
            "petit dans son cœur",
            "riche par ses briques",
            "clair dans ses générateurs",
            "fortement documenté",
        ]
        found = [p for p in manifest_phrases if p.lower() in text.lower()]
        assert len(found) >= 3, (
            f"Le manifesto a été retiré de la landing mais doit rester dans "
            f"la charte. Phrases trouvées : {found}. Si la charte ne les "
            f"contient pas, T23 a perdu du contenu philosophique."
        )
