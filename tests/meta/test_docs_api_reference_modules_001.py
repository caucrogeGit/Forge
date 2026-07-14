"""Garde-fou DOCS-API-REFERENCE-MODULES-001 — réécrit pour l'ADR-042.

Avant l'ADR-042, ce garde-fou EXIGEAIT que docs/reference/api.md liste et lie
les opt-ins officiels (principe 10, contrat de complétude vu depuis le cœur).

L'ADR-042 découple la doc du cœur de celle des opt-ins : la référence du cœur
ne doit plus cataloguer, mentionner ni lier les opt-ins. La complétude de
l'API opt-in vit désormais dans l'espace « Opt-ins officiels » (chaque paquet a
sa référence par-module).

Ce test vérifie donc l'ABSENCE de toute référence opt-in dans api.md.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
API_REF = PROJECT_ROOT / "docs" / "reference" / "api.md"

# Noms de paquets / namespaces des 12 opt-ins.
_OPTIN_TOKENS = re.compile(r"forge-mvc-(?!testing)[a-z0-9]+|forge_mvc_[a-z0-9]+")


def test_file_exists():
    assert API_REF.exists()


def test_no_optin_package_reference():
    """api.md (cœur) ne référence aucun paquet/namespace opt-in (ADR-042)."""
    text = API_REF.read_text(encoding="utf-8")
    hits = sorted(set(_OPTIN_TOKENS.findall(text)))
    assert not hits, (
        "docs/reference/api.md ne doit plus référencer d'opt-in (ADR-042, "
        f"découplage cœur/opt-ins). Trouvé : {hits}"
    )


def test_no_optin_catalog_section():
    """Aucune section catalogue d'opt-ins dans api.md."""
    text = API_REF.read_text(encoding="utf-8")
    assert "## Opt-ins officiels" not in text, (
        "docs/reference/api.md ne doit plus contenir de section catalogue "
        "« Opt-ins officiels » (ADR-042)."
    )


def test_no_active_pip_install_extra():
    """Aucune commande copiable `pip install forge-mvc[X]` ne subsiste."""
    text = API_REF.read_text(encoding="utf-8")
    matches = re.findall(r"pip\s+install\s+forge-mvc\[\w+\]", text)
    assert not matches, (
        f"docs/reference/api.md ne doit contenir aucune commande copiable "
        f"`pip install forge-mvc[X]`. Trouvé : {matches}"
    )
