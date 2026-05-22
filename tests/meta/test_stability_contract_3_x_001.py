"""Garde-fou STABILITY-CONTRACT-3.0-REFRESH-001.

Vérifie que docs/stability-contract.md reflète la série 1.x (série publique actuelle) :
- Titre et sections principales mentionnent Forge 1.x (pas 3.x ni 2.x)
- Aucune mention active de "Forge 2.x" ou "Forge 3.x" ne reste dans le contenu courant
- Le doc mentionne les modules opt-in et le mécanisme plugin

Origine : audit F7 — le doc parlait entièrement de Forge 2.x.
Mis à jour (VERSION-COHERENCE-1.0-001) : 3.x → 1.x suite à la publication PyPI sous la série 1.x.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
STABILITY_DOC = PROJECT_ROOT / "docs" / "stability-contract.md"


class TestTitleAndIntro:

    def test_title_is_1_x(self):
        text = STABILITY_DOC.read_text(encoding="utf-8")
        first_line = text.splitlines()[0]
        assert "Forge 1.x" in first_line, (
            f"Le titre du doc doit mentionner 'Forge 1.x' (série publique courante), got : {first_line!r}"
        )

    def test_no_active_forge_2_x_or_3_x_mentions(self):
        text = STABILITY_DOC.read_text(encoding="utf-8")
        forbidden_patterns = [
            "Forge 2.x garantit",
            "construits sur Forge 2.x",
            "toute la série 2.x",
            "Compatibilité attendue sur Forge 2.x",
            "stabilité Forge 2.x",
            "Forge 3.x garantit",
            "construits sur Forge 3.x",
            "toute la série 3.x",
            "Compatibilité attendue sur Forge 3.x",
        ]
        violations = [p for p in forbidden_patterns if p in text]
        assert not violations, (
            f"Mentions obsolètes détectées dans le contrat de stabilité : {violations}\n"
            f"Le contrat doit décrire la série 1.x (série publique courante)."
        )


class TestSeriesGuarantees:

    def test_mentions_serie_1_x(self):
        text = STABILITY_DOC.read_text(encoding="utf-8")
        assert "série 1.0.x" in text or "série 1.x" in text, (
            "Le doc doit mentionner 'la série 1.x' dans les garanties de compatibilité."
        )


class TestNewSectionsFor3X:

    def test_mentions_plugin_mechanism(self):
        text = STABILITY_DOC.read_text(encoding="utf-8")
        assert "register_jinja_context_provider" in text, (
            "Le doc doit mentionner le mécanisme de plugins introduit en T14."
        )

    def test_mentions_opt_in_modules(self):
        text = STABILITY_DOC.read_text(encoding="utf-8")
        modules_mentioned = [
            mod for mod in [
                "forge-mvc-rbac", "forge-mvc-workflow",
                "forge-mvc-stats", "forge-mvc-mfa",
            ]
            if mod in text
        ]
        assert len(modules_mentioned) >= 3, (
            f"Le doc doit mentionner au moins 3 modules opt-in (vu : {modules_mentioned})."
        )

    def test_mfa_marked_alpha_or_experimental(self):
        text = STABILITY_DOC.read_text(encoding="utf-8")
        if "forge-mvc-mfa" in text:
            mfa_match = re.search(r"forge-mvc-mfa.{0,300}", text, re.DOTALL)
            assert mfa_match, "Section MFA introuvable"
            context = mfa_match.group(0)
            assert (
                "Pre-Alpha" in context
                or "Alpha" in context
                or "expérimental" in context
                or "experimentale" in context.lower()
            ), (
                f"forge-mvc-mfa doit être marqué Alpha ou expérimental. "
                f"Contexte : {context[:200]}"
            )


class TestStructurePreserved:

    @pytest.mark.parametrize("section", [
        "## Objectif du contrat",
        "## Ce que Forge considère comme stable",
        "## Ce qui est public",
        "## Ce qui est interne",
        "## Ce qui est expérimental",
        "## Fichiers générés",
        "## Commandes CLI stables",
    ])
    def test_main_section_present(self, section):
        text = STABILITY_DOC.read_text(encoding="utf-8")
        assert section in text, (
            f"Section '{section}' manquante. Refactor trop agressif ?"
        )
